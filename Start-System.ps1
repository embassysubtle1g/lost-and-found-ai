param([switch]$OpenBrowser)

# 啟動本機完整系統：資料庫、照片儲存、DINOv2、Ollama Qwen 與網頁。
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonExe = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$dockerExe = (Get-Command docker -ErrorAction SilentlyContinue).Source
if (-not $dockerExe) { $dockerExe = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" }
$ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$logsPath = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Force -Path $logsPath | Out-Null
function Get-Health($url) {
    try { Invoke-RestMethod $url -TimeoutSec 3 } catch { $null }
}
if (-not (Test-Path -LiteralPath $pythonExe)) { throw '請先依 README 建立 backend/.venv 並安裝依賴。' }
if (-not (Test-Path -LiteralPath $ollamaExe)) { throw '請先安裝 Ollama。' }
# 若 Docker 引擎尚未啟動，開啟已安裝的 Docker Desktop 並等待就緒。
function Test-DockerEngine {
    try {
        $null = & $dockerExe info --format '{{.ServerVersion}}' 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}
if (-not (Test-DockerEngine)) {
    $dockerDesktopExe = "$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe"
    if (-not (Test-Path -LiteralPath $dockerDesktopExe)) { $dockerDesktopExe = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" }
    if (-not (Test-Path -LiteralPath $dockerDesktopExe)) { throw '找不到 Docker Desktop，請手動開啟它。' }
    Start-Process -FilePath $dockerDesktopExe -WindowStyle Hidden
    Write-Host '正在等待 Docker Desktop 啟動…'
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        if (Test-DockerEngine) { break }
        Start-Sleep -Seconds 2
    }
    if (-not (Test-DockerEngine)) { throw 'Docker 引擎尚未就緒，請開啟 Docker Desktop 查看狀態後重試。' }
}
Set-Location -LiteralPath (Join-Path $projectRoot 'backend')
# 停止未量化的 CPU Qwen，避免同時載入兩份模型。
& $dockerExe compose stop language-ai
if ($LASTEXITCODE -ne 0) { throw '請確認 Docker Desktop 已啟動。' }
# 啟動 PostgreSQL 與 MinIO，保留原本資料卷。
& $dockerExe compose up -d --wait db storage
if ($LASTEXITCODE -ne 0) { throw '資料庫或照片儲存服務啟動失敗。' }
# 啟動已建置的穩定 CPU 映像，不進行建置或下載 CUDA。
& $dockerExe compose --profile ai up -d --no-build ai
if ($LASTEXITCODE -ne 0) { throw '既有 DINOv2 CPU 映像無法啟動，請查看 Docker 錯誤。腳本不會自動建置。' }
# 啟動既有 Ollama，再確認 Qwen 視覺模型已下載。
if (-not (Get-Health 'http://127.0.0.1:11434/api/version')) {
    Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if (Get-Health 'http://127.0.0.1:11434/api/version') { break }
        Start-Sleep -Seconds 1
    }
}
$models = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
if ('qwen2.5vl:3b' -notin $models.models.name) {
    & $ollamaExe pull qwen2.5vl:3b
    if ($LASTEXITCODE -ne 0) { throw 'Qwen 模型下載失敗。' }
}
# 用輕量 Python API 連接 Ollama，使用相同的 8081 埠。
if (-not (Get-Health 'http://127.0.0.1:8081/health')) {
    $env:MODEL_BACKEND = 'ollama'
    $env:OLLAMA_MODEL = 'qwen2.5vl:3b'
    $env:OLLAMA_URL = 'http://127.0.0.1:11434'
    $env:MAX_NEW_TOKENS = '512'
    Start-Process -FilePath $pythonExe -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8081' -WorkingDirectory (Join-Path $projectRoot 'services\lost-and-found-language-ai') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logsPath 'language.out.log') -RedirectStandardError (Join-Path $logsPath 'language.err.log')
}
# 校園地圖更新：遷移可重複執行，只在舊版後端尚未提供地點 API 時重新啟動它。
& $pythonExe -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw '校園地點資料庫更新失敗。' }
if (Get-Health 'http://127.0.0.1:8000/health') {
    $needsMapRestart = $false
    foreach ($requiredPath in @('/api/locations', '/api/reporting-units')) {
        try {
            $requiredData = Invoke-RestMethod ('http://127.0.0.1:8000' + $requiredPath) -TimeoutSec 5
            if ($requiredPath -eq '/api/locations') { $expectedCampusCount = @($requiredData).Count }
            if ($requiredPath -eq '/api/reporting-units') {
                if (@($requiredData).Count -ne $expectedCampusCount -or @($requiredData | Where-Object { -not $_.campus_location_id }).Count -gt 0) { $needsMapRestart = $true }
            }
        }
        catch {
            if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) { $needsMapRestart = $true }
            else { throw '地點或通報單位 API 目前無法使用，請查看後端記錄。' }
        }
    }
    # Restart this project's old backend when the downlisting API has not been loaded.
    $deleteSchemaClient = New-Object System.Net.WebClient
    try {
        $deleteSchemaClient.Encoding = [System.Text.Encoding]::UTF8
        $deleteSchema = $deleteSchemaClient.DownloadString('http://127.0.0.1:8000/openapi.json') | ConvertFrom-Json
    } finally { $deleteSchemaClient.Dispose() }
    if (-not $deleteSchema.paths.'/api/items/{reference}'.delete) { $needsMapRestart = $true }
    if ($needsMapRestart) {
        # Windows PowerShell 5.1 may decode JSON without a charset using the wrong encoding.
        $schemaClient = New-Object System.Net.WebClient
        try {
            $schemaClient.Encoding = [System.Text.Encoding]::UTF8
            $schema = $schemaClient.DownloadString('http://127.0.0.1:8000/openapi.json') | ConvertFrom-Json
        } finally { $schemaClient.Dispose() }
        if ($schema.info.title -ne '尋物雷達 API') { throw '8000 埠不是預期的主系統，未停止任何程序。' }
        $logPath = Join-Path $logsPath 'backend.err.log'
        if (-not (Test-Path -LiteralPath $logPath)) { throw '找不到後端啟動記錄，請關閉原本的後端視窗後再啟動。' }
        $pidMatches = [regex]::Matches((Get-Content -LiteralPath $logPath -Raw), 'Started server process \[(\d+)\]')
        if ($pidMatches.Count -eq 0) { throw '記錄內沒有後端程序編號，未停止任何程序。' }
        $loggedBackendPid = [int]$pidMatches[$pidMatches.Count - 1].Groups[1].Value
        $listeners = @(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop)
        if ($loggedBackendPid -notin $listeners.OwningProcess) { throw '後端程序與本專案記錄不符，未停止任何程序。' }
        Write-Host '正在重新啟動主後端以載入最新案件、地點與通報單位 API…'
        Stop-Process -Id $loggedBackendPid -ErrorAction Stop
        for ($attempt = 0; $attempt -lt 10; $attempt++) {
            if (-not (Get-Health 'http://127.0.0.1:8000/health')) { break }
            Start-Sleep -Milliseconds 500
        }
    }
}

# 檢查前端已建置，再啟動主後端。
if (-not (Test-Path (Join-Path $projectRoot 'frontend\dist\index.html'))) { throw '請先執行 npm.cmd --prefix frontend ci 與 npm.cmd --prefix frontend run build。' }
if (-not (Get-Health 'http://127.0.0.1:8000/health')) {
    & $pythonExe -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw '資料庫遷移失敗。' }
    Start-Process -FilePath $pythonExe -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logsPath 'backend.out.log') -RedirectStandardError (Join-Path $logsPath 'backend.err.log')
}
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    $backend = Get-Health 'http://127.0.0.1:8000/health'
    $language = Get-Health 'http://127.0.0.1:8081/health'
    $dino = Get-Health 'http://127.0.0.1:8080/health'
    if ($backend -and $language -and $dino) { break }
    Start-Sleep -Seconds 2
}
if (-not ($backend -and $language -and $dino)) { throw '部分服務尚未就緒，請查看 .runtime 記錄或 Docker 容器記錄。' }
if ($language.backend -and $language.backend -ne 'ollama') { throw '8081 仍是其他語言服務，請先停止舊服務。' }
if ($dino.model_info.device -and $dino.model_info.device -ne 'cpu') { throw 'DINOv2 裝置不是預期的 CPU，請檢查容器設定。' }
Write-Host '系統已就緒：http://127.0.0.1:8000；Qwen 使用 Ollama，DINOv2 使用穩定 CPU 版。'
if ($OpenBrowser) { Start-Process 'http://127.0.0.1:8000' }

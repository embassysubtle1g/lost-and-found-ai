# 使用既有的後端虛擬環境，啟動連接 Ollama 的 Qwen 描述 API。
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:MODEL_BACKEND = 'ollama'
$env:OLLAMA_URL = 'http://127.0.0.1:11434'
$env:OLLAMA_MODEL = 'qwen2.5vl:3b'
$env:MAX_NEW_TOKENS = '512'
& "$PSScriptRoot\..\..\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8081

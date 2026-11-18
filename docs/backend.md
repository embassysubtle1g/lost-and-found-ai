# 啟動免登入新版尋物雷達

需要 Python 3.10 以上、Node.js 22 LTS 與 Docker。Codespaces 在環境內執行 Docker，Windows 先開 Docker Desktop。

## 更新既有環境

先停止目前的 Backend（執行 uvicorn 的終端機按 Ctrl+C）。從儲存庫根目錄執行：

```bash
git pull --ff-only origin backend/first-edition
npm --prefix frontend ci
npm --prefix frontend run build
cd backend
docker compose up -d --wait
```

Linux / Codespaces：

```bash
source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

開啟 8000 首頁即為新版 React；管理頁點「拾獲物管理」，選擇機構即可操作。
若尚無機構，可在管理頁點「新增保管機構」，輸入名稱、地址與電話後直接建檔。
舊測試頁、登入頁及 Token API 已移除。0003 資料庫遷移必須先完成，才能使用免登入歸還功能。

## 首次安裝

第一次先建立設定和虛擬環境。請在 backend 目錄執行。
Codespaces / Linux：

```bash
test -f .env || cp .env.example .env
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

設定 .env 的資料庫、圖片儲存帳密，POSTGRES_PASSWORD 與 DATABASE_URL 內密碼須一致。
接著執行資料庫啟動、Alembic 遷移及前端建置指令。可執行 python -m app.core.seed_demo 建立兩個示範機構，無需設定帳號或密碼。
既有環境請沿用原本 .env 和 Docker volumes。若曾以其他 Compose 專案名稱啟動，請沿用同一 -p 名稱，保留既有資料卷。

## 開發與 DINOv2

前端開發可用 npm --prefix frontend run dev 啟動 5173，API 由 Vite 代理到 8000。一般展示只需建置 React 並開啟 Backend 的 8000。

Backend 的 DINOV2_URL 指向組員提供的服務，或在 backend 執行：

```bash
docker compose --profile ai up -d --build ai
docker compose logs -f ai
```

第一次需下載模型與依賴。等模型載入完成後，照片向量即可處理。DINOv2 API 文件位於 8080/docs。
Codespaces 的 localhost 代表雲端環境，與你的 Windows 本機分開。

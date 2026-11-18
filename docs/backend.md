# 本機與 Codespaces 啟動

專案根目錄可命名為 Lost-and-Found-System。以下指令從儲存庫根目錄開始執行。先開啟 Docker Desktop（Codespaces 使用環境內的 Docker），準備 Python 3.10 以上與 Node.js 22 LTS。

## 1. 資料庫及圖片儲存

```bash
cd backend
```

第一次執行時複製設定。Windows PowerShell 使用：

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Codespaces / Linux 使用：

```bash
test -f .env || cp .env.example .env
```

編輯 .env 中的帳密，POSTGRES_PASSWORD 與 DATABASE_URL 內密碼須一致。現有資料庫請沿用原本的 .env 和密碼。啟動服務：

```bash
docker compose up -d --wait
```

根目錄的 backend/compose.yaml 與既有 app/core/compose.yaml 使用同一個 backend 專案目錄時，可沿用原有資料。不要執行刪除 volumes 的指令。若過去用 app/core 做為 Compose 專案目錄，先用 docker compose ls 確認既有專案名稱，使用相同 -p 名稱啟動，以保留原本的資料卷。

## 2. Backend

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.core.seed_demo
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Codespaces / Linux：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.core.seed_demo
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

建立帳號時自訂 station_a、station_b 的密碼，至少 10 字元。既有帳號可以省略 seed_demo。0002 遷移新增拾獲區域，保留原有物品。既有紀錄區域為空時，查詢會使用原拾獲地點作為區域篩選的相容處理，承辦人可逐筆補齊區域。

API 文件 http://127.0.0.1:8000/docs 。Codespaces 在連接埠開啟 8000，再於網址後加 /docs。

## 3. React 前端

保留 Backend 執行中的終端機，開另一個終端機進入 frontend：

```bash
cd frontend
npm ci
npm run dev
```

瀏覽器開啟 http://127.0.0.1:5173 。Codespaces 在連接埠開啟 5173。
React 開發代理讓前端透過相同網址呼叫 /api/v1，Backend 與前端需在同一執行環境。

要由 Backend 同時提供前端，先在 frontend 執行 npm run build，再重啟 Backend。之後開啟 8000 即可。

## 4. DINOv2

使用組員的服務時，把 backend/.env 的 DINOV2_URL 設為 Backend 可連到的網址，並重新啟動 Backend。
若要使用本 repo 提供的 CPU 容器，在 backend 執行：

```bash
docker compose --profile ai up -d --build ai
docker compose logs -f ai
```

第一次需要下載 PyTorch、Transformers 和模型。等模型載入完成後使用，服務位址為 http://127.0.0.1:8080，API 文件為 /docs。
Backend 預設連此位址。主系統透過 multipart file 呼叫 /api/v1/images/embedding，採 dinov2_vitb14 的 768 維向量。
Codespaces 的 localhost 是遠端環境，無法直接連到你 Windows 電腦的 Ollama 或 DINOv2。

## 驗收

1. A 機構登入，新增拾獲錢包，填寫區域、詳細拾獲地點及日期，上傳正反面照片。
2. 公開失物大廳可依名稱、類別、可能遺失區域與大約遺失日期搜尋。
3. 照片狀態顯示「向量已就緒」後，用另一張錢包照片搜尋。每件物品出現一次。
4. 詳情顯示物品編號、實際拾獲地點與保管機構地址和電話。
5. B 機構無法管理 A 的紀錄。A 標記已歸還後，公開文字與圖片搜尋都排除此物品，A 後台仍保留歸還紀錄。

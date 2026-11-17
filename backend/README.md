# 拾獲物招領 Backend

此目錄提供 FastAPI 後端與第一版操作網頁。AI Service 啟動後，Backend 會依照組員的 HTTP API 擷取向量。

## Windows 本機啟動

需要 Python 3.10 以上、Docker Desktop 和瀏覽器。從 GitHub 下載此分支後，在 PowerShell 進入本目錄。

```powershell
cd backend
Copy-Item .env.example .env
```

在 `.env` 設定本機資料庫與物件儲存密碼。若修改 `POSTGRES_PASSWORD`，也請同步更新 `DATABASE_URL` 中的密碼（特殊字元需 URL 編碼）。將 `DINOV2_URL` 設為電腦可連到的 AI Service 基底網址。

```powershell
docker compose up -d --wait
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe seed_demo.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

- 民眾查詢 <http://127.0.0.1:8000/>
- 機構後台 <http://127.0.0.1:8000/staff>
- API 文件 <http://127.0.0.1:8000/docs>

建議使用不同的密碼建立 `station_a`、`station_b`。重跑建立帳號的指令會保留已存在的帳號和密碼。資料庫與圖片原檔會保存在 Docker volumes。專案設定供本機展示，部署到遠端時請另行配置 TLS、存取控制和登入／上傳限制。

## 展示流程

1. 以 `station_a` 登入，建立錢包並上傳正反面照片。民眾頁可立即用文字篩選待認領物品。
2. 後台確認向量已就緒，民眾頁上傳查詢照。候選應以物品呈現一次，詳情附上拾獲地點、保管地址及電話。
3. 驗證 `station_b` 的後台只有自己機構的物品。使用 A 帳號交還後按「標記為已歸還」。
4. 確認公開文字與照片搜尋移除這件物品，A 帳號仍能在後台查看歸還紀錄。

## DINOv2 串接

送出 `POST /api/v1/images/embedding`，表單欄位為 `file`。預設接受 `facebook/dinov2-base`、`dinov2_vitb14` 的 768 維向量。更改維度需要資料庫遷移並重新處理照片。模型與版本必須相符才可參與比對。

AI Service 尚未啟動時仍可建檔、上傳圖片、用文字搜尋和登記歸還。建檔照標記處理失敗後，可以在服務就緒時重試。查詢照僅用於當次搜尋。

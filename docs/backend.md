# 原稿版尋物雷達啟動

在 Codespaces 執行後端的終端機按 Ctrl+C 停止舊程序，從專案根目錄開始：

```bash
git pull --ff-only origin backend/first-edition
npm --prefix frontend ci
npm --prefix frontend run build
cd backend
docker compose up -d --wait
source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

開啟連接埠 8000。首頁為完整原稿介面，免登入，可登記遺失或拾獲資料、查詢、檢視配對與確認結案。
Windows 使用 .venv/Scripts/python.exe 執行上述 Python 指令。
首次安裝需先在 backend 複製 .env.example 為 .env、建立虛擬環境並安裝 requirements.txt。

本次需要 Alembic 0004 遷移，既有物品依 FOUND 呈現。照片及配對資料存入後端。
DINOv2 服務使用 backend/.env 的 DINOV2_URL，或從 backend 執行：

```bash
docker compose --profile ai up -d --build ai
```

照片向量需等待背景處理完成，再按媒合頁「重新比對」更新。尚無向量時，候選理由會標示依手動填寫資料比對。
物品名稱、分類、描述與顏色由新增的 Qwen 語言 AI 服務提供，自動填寫設定請見 [語言 AI 整合](language-ai.md)。

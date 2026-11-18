# 原稿介面與後端

frontend/public/radar.html 以提供的遺失物.txt 為畫面基準，保留導覽、大廳、遺失／拾獲登記、媒合中心、詳情和 API 設定視窗。React App 以完整頁面承載，避免改寫元件造成原稿版面差異。沒有登入功能。

API /api/items、/api/matches、/api/ai-recognize、/api/matches/confirm、/api/matches/dismiss、DELETE /api/matches/dismissed 支援原稿操作。
資料保存於 PostgreSQL，圖片存 Object Storage，照片背景向量由 DINOv2 擷取。0004 遷移在既有 items 新增 record_type 和 radar_data，原有拾獲物仍可顯示。
媒合有圖片向量時採 DINOv2 餘弦相似度，尚無向量時依原稿類別／顏色／地點／標籤規則計分，理由明確標示。確認媒合以交易鎖定兩筆紀錄後一起結案。排除配對持久保存，重新比對會清除排除紀錄。
原稿的示範圖可供展示；上傳照片請用 JPEG、PNG、WebP。真實登記不自動加入示範案件。

DINOv2 提供圖片特徵，無法回傳文字名稱／顏色／標籤。辨識按鈕先實際驗證 DINOv2，成功後顯示「圖片特徵已擷取」並提示手動填寫。取得 Qwen 視覺 API 規格後才能自動填入這些文字欄位。系統沒有通知服務，因此確認結案訊息只說明資料庫更新。

啟動：更新後執行 npm --prefix frontend ci、npm --prefix frontend run build，在 backend 執行 python -m alembic upgrade head，再重啟 FastAPI，開啟 8000。開發模式也可使用 5173。

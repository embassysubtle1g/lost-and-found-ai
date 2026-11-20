# 原稿介面與後端

frontend/public/radar.html 以提供的遺失物.txt 為畫面基準，保留導覽、大廳、遺失／拾獲登記、媒合中心、詳情和 API 設定視窗。React App 以完整頁面承載，避免改寫元件造成原稿版面差異。沒有登入功能。

API /api/items、/api/matches、/api/ai-recognize、/api/matches/confirm、/api/matches/dismiss、DELETE /api/matches/dismissed 支援原稿操作。
資料保存於 PostgreSQL，圖片存 Object Storage，照片背景向量由 DINOv2 擷取。0004 遷移在既有 items 新增 record_type 和 radar_data，原有拾獲物仍可顯示。
媒合有圖片向量時採 DINOv2 餘弦相似度，尚無向量時依原稿類別／顏色／地點／標籤規則計分，理由明確標示。確認媒合以交易鎖定兩筆紀錄後一起結案。排除配對持久保存，重新比對會清除排除紀錄。
原稿的示範圖可供展示；上傳照片請用 JPEG、PNG、WebP。真實登記不自動加入示範案件。

DINOv2 提供圖片向量；物品描述、名稱、分類、顏色和標籤由新增的 Qwen 服務自動填寫。模型自評信心與 needs_review 會顯示於表單，送出前可修改。啟動設定見 language-ai.md。

# Lost-and-Found-System

尋物雷達的前端完整依據提供的遺失物.txt 頁面呈現，包含失物大廳、登記通報、AI 媒合中心與詳情視窗。全系統免登入。

- frontend/ 放 React 入口與原稿完整頁面。
- backend/ 放 FastAPI、資料庫模型、API 與圖片／配對邏輯。
- services/lost-and-found-ai/ 放 DINOv2 獨立圖片特徵服務。
- docs/frontend-reference.md 說明原稿介面與 API 差異。

更新後先建置前端，再執行 Alembic 0004 遷移、重新啟動後端。詳見 [啟動方式](docs/backend.md)。

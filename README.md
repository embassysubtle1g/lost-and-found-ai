# 拾獲物招領系統

| 目錄 | 用途 |
| --- | --- |
| [backend/](docs/backend.md) | 主系統 FastAPI 後端，負責物品、權限、圖片儲存及搜尋 |
| [frontend/](frontend/README.md) | 團隊 React 前端的整合位置 |
| [services/lost-and-found-ai/](services/lost-and-found-ai/使用說明.md) | 獨立的 DINOv2 圖片特徵擷取服務 |
| [docs/](docs/integration.md) | 服務串接方式 |

主系統後端在 `backend/` 啟動，預設埠為 `8000`。AI 服務在 `services/lost-and-found-ai/` 啟動，預設埠為 `8080`。安裝與啟動指令請參考各自的使用說明。

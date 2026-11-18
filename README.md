# Lost-and-Found-System

機構保管拾獲物，民眾免登入查詢。前端依「尋物雷達」頁面改寫成 React／TypeScript，所有物品和照片搜尋都呼叫 Backend API。

| 目錄 | 用途 |
| --- | --- |
| backend/app/api | 路由與權限入口 |
| backend/app/core | 設定、資料庫、安全性與既有遷移 |
| backend/app/models | 資料存取 |
| backend/app/schemas | 請求格式 |
| backend/app/services | 圖片儲存、向量處理與業務流程 |
| backend/tests | API 與搜尋規則驗證 |
| frontend/src | React 頁面、元件、Hooks、型別和 API 用戶端 |
| services/lost-and-found-ai | 獨立 DINOv2 服務 |
| docs | 啟動、API 與整合說明 |

`Lost-and-Found-System/` 代表儲存庫根目錄的專案名稱。下載 ZIP 的資料夾名稱由 GitHub 依儲存庫與分支產生，可自行將解壓縮資料夾改名。

先看 [啟動說明](docs/backend.md)，API 對照表見 [整合說明](docs/integration.md)。

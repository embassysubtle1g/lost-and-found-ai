# 尋物雷達 React 前端

Node.js 22 LTS 或以上，在本目錄執行 `npm ci`、`npm run dev`。首次安裝尚無 lockfile 時執行 `npm install`。開啟終端機列出的 5173 網址。Codespaces 使用連接埠頁面開啟 5173。

Vite 會把 /api 請求轉送到同一台開發環境的 127.0.0.1:8000，Backend 必須先啟動。
可用環境變數 BACKEND_URL 改變 Vite 代理目的地。

- 失物大廳提供公開文字與條件查詢。
- 照片搜尋送出 multipart file 與選填條件，候選顯示物品及保管資訊。
- 機構後台提供登入、機構資訊與密碼更新、建檔、照片處理與歸還。
- 原始 HTML 的視覺參考保留品牌、藍白配色、卡片、上傳區塊與分頁導覽。第一版採機構建檔流程。
- 所有案件與相似度均由 Backend 回傳。DINOv2 提供圖片向量。

執行 `npm run build` 產生 dist，Backend 可直接提供這份建置後的頁面。

# 尋物雷達 React 前端

全系統免登入。失物大廳與照片搜尋提供公開查詢；拾獲物管理頁可選擇機構，直接建立、編輯、上傳照片、下架與登記歸還。首次使用可在管理頁新增機構，或由 backend 的 seed_demo 建立示範機構。

專案根目錄執行：

```bash
npm --prefix frontend ci
npm --prefix frontend run build
```

Backend 的 8000 首頁直接提供新版 React，舊測試頁已移除。
開發時也可在 frontend 執行 npm run dev，開啟 5173，Vite 代理 /api 到 8000。
前端透過 X-Organization-ID 選擇所管理的機構，此欄位是資料分組用途。所有使用者都能選擇與管理任一機構。

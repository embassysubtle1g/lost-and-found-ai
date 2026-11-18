# 前後端與 AI 串接

React 透過 /api/v1 呼叫 Backend。開發時由 Vite 代理到 8000，建置後可由 Backend 同網域提供。
完整請求格式以 Backend /docs 的 OpenAPI 為準。

| 方法與路徑 | 用途 |
| --- | --- |
| POST /api/v1/auth/login | JSON username、password，回傳 access_token |
| GET /api/v1/auth/me | 取得承辦帳號及所屬機構 |
| POST /api/v1/auth/logout | 撤銷本次憑證 |
| PUT /api/v1/auth/password | JSON current_password、new_password，撤銷既有登入 |
| PUT /api/v1/auth/organization | JSON name、address、phone |
| GET /api/v1/public/items | keyword、category、location、lost_date、page、limit |
| GET /api/v1/public/items/{id} | 公開詳情與保管資訊 |
| POST /api/v1/public/search | multipart file 必填，keyword、category、location、lost_date 選填 |
| GET /api/v1/public/images/{id} | 公開待認領物品照片 |
| GET /api/v1/staff/items | 本機構物品分頁 |
| POST /api/v1/staff/items | JSON name、category、found_date、found_region、found_location、private_note |
| GET /api/v1/staff/items/{id} | 本機構物品、照片狀態與內部備註 |
| PUT /api/v1/staff/items/{id} | 更新建檔資訊 |
| POST /api/v1/staff/items/{id}/return | 登記歸還 |
| POST /api/v1/staff/items/{id}/withdraw | 下架 |
| POST /api/v1/staff/items/{id}/images | multipart file |
| GET /api/v1/staff/images/{id} | 具權限的照片讀取 |
| PUT /api/v1/staff/items/{id}/images/{image}/cover | 更換封面 |
| DELETE /api/v1/staff/items/{id}/images/{image} | 移除照片與向量 |
| POST /api/v1/staff/items/{id}/images/{image}/retry | 重試失敗照片 |

承辦 API 使用 Authorization: Bearer <access_token>。公開 API 免登入。錯誤為 detail 字串或 FastAPI 驗證錯誤陣列。主要狀態為 401 未登入、404 查無資料或無權存取、409 狀態衝突、413 檔案過大、422 輸入錯誤、503 外部服務暫時不可用。

公開名稱與區域採文字包含搜尋，類別採相同值搜尋。lost_date 對應 found_date >= lost_date，避免將隔日拾獲排除。現有 since、until、organization 參數維持相容。每張照片最多 8 MB、每件最多八張。

照片搜尋回傳 {items: [...]}，每筆含 similarity，代表向量餘弦相似度。候選依相似度排序，同物品取最高分，並由機構確認物主。
列表回傳 {items: [...], page: 1, has_more: false}。公開格式排除 private_note、returned_by 和處理錯誤。

DINOv2 位於 services/lost-and-found-ai。Backend 把照片傳給 POST /api/v1/images/embedding，保存 model、model_version、embedding_dimension、embedding。只有設定一致的已完成向量參與比對。背景處理狀態為 PENDING、PROCESSING、COMPLETED、FAILED，失敗可重試。
民眾查詢照只用於當次搜尋。Qwen／自然語言 API 尚待組員提供規格。

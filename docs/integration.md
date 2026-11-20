# 免登入前後端與 AI 串接

React 透過 /api/v1 呼叫 Backend。系統已移除登入、Token、登出及修改密碼 API。
管理操作使用 X-Organization-ID 指定保管機構 ID，此欄位選擇資料分組，所有使用者都可切換。
未提供時使用第一個機構；若機構不存在，回傳 409 提示先建立或選擇機構。

| 方法與路徑 | 用途 |
| --- | --- |
| GET /api/v1/public/organizations | 取得可選機構 |
| POST /api/v1/staff/organizations | JSON name、address、phone，新增機構 |
| PUT /api/v1/staff/organization | 更新選定機構的 name、address、phone |
| GET /api/v1/public/items | keyword、category、location、lost_date、page、limit |
| GET /api/v1/public/items/{id} | 公開詳情與保管資訊 |
| POST /api/v1/public/search | multipart file 必填，其餘搜尋條件選填 |
| GET /api/v1/public/images/{id} | 待認領物品照片 |
| GET /api/v1/staff/items | 選定機構物品分頁 |
| POST /api/v1/staff/items | JSON name、category、found_date、found_region、found_location、private_note |
| GET /api/v1/staff/items/{id} | 選定機構物品、照片狀態與備註 |
| PUT /api/v1/staff/items/{id} | 更新建檔資訊 |
| POST /api/v1/staff/items/{id}/return | 歸還登記，保存歸還時間 |
| POST /api/v1/staff/items/{id}/withdraw | 下架 |
| POST /api/v1/staff/items/{id}/images | multipart file |
| GET /api/v1/staff/images/{id} | 選定機構的照片 |
| PUT /api/v1/staff/items/{id}/images/{image}/cover | 更換封面 |
| DELETE /api/v1/staff/items/{id}/images/{image} | 移除照片與向量 |
| POST /api/v1/staff/items/{id}/images/{image}/retry | 重試失敗照片 |

為保持既有 API 用戶端路徑相容，管理端路徑沿用 /staff。API 文件 /docs 可直接操作管理 API。
錯誤為 detail 字串或 FastAPI 驗證錯誤陣列，主要狀態為 404、409、413、422、503。

公開名稱與區域採文字包含搜尋，類別採相同值搜尋。lost_date 對應 found_date >= lost_date。
照片搜尋每件物品取最高向量相似度，只回傳待認領物品。每張照片最多 8 MB，每件最多八張。

DINOv2 仍以 multipart file 呼叫 /api/v1/images/embedding，使用一致模型版本的 768 維向量。
歸還後排除於公開查詢，管理頁保留紀錄。0003 遷移允許免登入的歸還紀錄，新的 returned_by 為 NULL，原有歸還紀錄維持原值。

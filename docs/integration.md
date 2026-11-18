# 服務串接

- React 前端呼叫主系統後端，介面文件位於 `http://127.0.0.1:8000/docs`。機構人員先呼叫 `POST /api/v1/auth/login`，再以回傳的 Bearer token 呼叫機構端 API。
- 主系統後端依 `backend/.env` 的 `DINOV2_URL` 呼叫 AI 服務。例如兩個服務都在本機時，設為 `http://127.0.0.1:8080`。
- 向量請求使用 `POST /api/v1/images/embedding`，上傳欄位是 `file`。目前兩端使用 `facebook/dinov2-base`（`dinov2_vitb14`），向量長度為 768。
- 主系統後端負責向量儲存與相似度搜尋。AI 服務的 API 文件位於 `http://127.0.0.1:8080/docs`。

啟動方式請見 [主系統後端](../backend/README.md) 與 [AI 服務](../services/lost-and-found-ai/使用說明.md)。

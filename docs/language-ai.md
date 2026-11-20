# 物品描述服務整合

來源為 embassysubtle1g/Lost-and-Found-System 的 services/lost-and-found-language-ai。
在本專案同一路徑保存該獨立服務，主系統只透過 HTTP 呼叫。

## 呼叫流程

前端「執行 AI 智慧辨識特徵」 → POST /api/ai-recognize（JSON image data URL）
→ Backend 驗證圖片 → POST LANGUAGE_AI_URL/api/v1/images/classify（multipart file）。
回傳 detected_item、suggested_category、description、attributes、confidence、needs_review。
Backend 轉成前端 title、category、description、color、tags 等欄位。
未知顏色留空，材質／品牌／可辨識特徵加入標籤，needs_review 顯示人工確認。
已手動輸入的內容保留，辨識期間換照片時捨棄舊回應。
確認送出後，表單資料與描述存入資料庫；DINOv2 仍於背景處理登記照片向量供媒合。

## 更新與設定

更新原測試分支後，建置 frontend，在 backend/.env 加入：

```dotenv
LANGUAGE_AI_URL=http://127.0.0.1:8081
LANGUAGE_AI_TIMEOUT=300
```

組員已有可連線服務時填其基底網址。Codespaces 的 localhost 代表遠端 Codespaces。
原語言 AI 預設使用 GPU 4-bit；本 Compose 的可選 CPU profile 設定 LOAD_IN_4BIT=false。
在 backend 執行：

```bash
docker compose --profile language up -d --build language-ai
docker compose logs --tail=60 language-ai
```

首次辨識會下載並載入 Qwen2.5-VL-3B。CPU 方式需要足夠記憶體與磁碟空間；
先前 Codespaces 已回報低磁碟空間，請先確認容量，或使用組員提供的服務網址。
health 成功只表示 API 有回應，第一次實際 classify 才會載入模型。

重新啟動 Backend，開啟 8000，選照片並辨識，確認表單自動填入後再送出。
主系統圖片上限沿用 8 MB。503 表示服務不可用，504 表示逾時，502 表示回應格式不符。
失敗可重試或手動填寫，前端會復原按鈕和處理狀態。

## 驗證範圍

API 契約測試以模擬服務驗證欄位轉換、null、人工確認、逾時、連線失敗與格式錯誤。
Qwen 真實推論需在有足夠資源的環境啟動後驗收。

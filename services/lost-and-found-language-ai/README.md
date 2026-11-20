# Lost and Found Language AI

遺失物管理系統使用的 AI Service，提供圖片理解與物品分類 API，讓主系統可以透過 HTTP 呼叫 AI 服務，取得結構化的遺失物辨識結果。

## 目前提供的功能

### 1. 服務健康檢查

確認 AI Service 是否正常啟動。

- **Method：** `GET`
- **Path：** `/health`
- **用途：** 回傳服務狀態、服務名稱與版本。

成功回應範例：

```json
{
  "status": "ok",
  "service": "Lost and Found Language AI Service",
  "version": "0.1.0"
}
```

### 2. 遺失物圖片辨識與分類

使用多模態視覺語言模型分析使用者上傳的圖片，辨識主要物品，並產生適合遺失物資料庫使用的通用分類及外觀描述。

- **Method：** `POST`
- **Path：** `/api/v1/images/classify`
- **Content-Type：** `multipart/form-data`
- **欄位名稱：** `file`
- **支援格式：** JPEG、PNG、WebP
- **圖片大小限制：** 10 MB

#### 辨識結果

API 回傳以下欄位：

| 欄位 | 型別 | 說明 |
|---|---|---|
| `detected_item` | string | 辨識出的具體物品名稱，例如「黑色短夾」 |
| `suggested_category` | string | 建議使用的通用分類，例如「皮夾」 |
| `description` | string | 物品外觀的簡潔描述 |
| `attributes.color` | string / null | 主要顏色 |
| `attributes.material` | string / null | 材質；無法判斷時為 null |
| `attributes.brand` | string / null | 品牌；無法辨識時為 null |
| `attributes.distinctive_features` | string[] | 可辨識的外觀特徵 |
| `confidence` | number | 模型自評信心程度，介於 0 至 1，僅供參考 |
| `needs_review` | boolean | 是否建議交由人工確認 |

成功回應範例：

```json
{
  "detected_item": "黑色拉鍊式錢包",
  "suggested_category": "皮夾",
  "description": "一個黑色的拉鍊式錢包，外觀可見卡片與紙幣。",
  "attributes": {
    "color": "黑色",
    "material": null,
    "brand": null,
    "distinctive_features": [
      "拉鍊式開口",
      "內部可見卡片與紙幣"
    ]
  },
  "confidence": 0.92,
  "needs_review": false
}
```

> 上述回應僅為格式示例，實際辨識結果會依上傳圖片而不同。信心程度是模型自評值，並非經過校準的統計機率。

#### 圖片辨識規則

- 優先辨識圖片中的主要物品，先提供具體物品名稱，再提出通用分類。
- 只描述圖片中可觀察到的內容，不臆測無法確認的品牌、材質或物品內部資訊。
- 圖片模糊、物品不明確、主要物品難以區分或無法判斷時，應將 `needs_review` 設為 `true`。
- 模型輸出會整理成固定 JSON 結構，供主系統直接接收及使用。

#### 常見錯誤回應

| HTTP 狀態碼 | 情況 |
|---|---|
| `400` | 圖片格式不支援、檔案為空、超過 10 MB 或圖片無法讀取 |
| `503` | 模型載入或執行發生錯誤，例如啟用 4-bit 量化但環境沒有可用 CUDA GPU |
| `500` | 其他未預期的圖片分類錯誤 |

## 使用的技術

| 項目 | 技術 |
|---|---|
| API 框架 | FastAPI |
| 視覺語言模型 | Qwen2.5-VL-3B-Instruct |
| 模型載入與推論 | Hugging Face Transformers |
| 圖片處理 | Pillow |
| 多模態圖片處理 | qwen-vl-utils |
| GPU 記憶體最佳化 | BitsAndBytes 4-bit 量化（可透過設定調整） |
| API 資料驗證 | Pydantic |

## 模型設定

可透過環境變數調整模型行為：

| 環境變數 | 預設值 | 說明 |
|---|---|---|
| `MODEL_NAME` | `Qwen/Qwen2.5-VL-3B-Instruct` | 使用的視覺語言模型 |
| `DEVICE` | `auto` | 模型執行裝置 |
| `LOAD_IN_4BIT` | `true` | 是否使用 4-bit 量化 |
| `MAX_NEW_TOKENS` | `512` | 模型生成文字的最大 token 數 |

模型採延遲載入方式：服務啟動時不立即下載及載入模型，而是在第一次執行圖片辨識時載入；同一個服務程序會重用已載入的模型。

## API 路由總覽

| Method | Endpoint | 功能 |
|---|---|---|
| GET | `/health` | 服務健康檢查 |
| POST | `/api/v1/images/classify` | 遺失物圖片辨識與分類 |

## 目前功能範圍與尚未提供的功能

目前程式已實作服務健康檢查及圖片辨識分類 API。

以下功能**尚未列入目前已實作的 API**，不應視為現階段已提供的服務：

- 以自然語言描述搜尋遺失物。
- 文字與圖片向量化（Embedding）。
- 向量資料庫或相似圖片搜尋。
- 將辨識結果寫入主系統資料庫。
- 遺失物案件新增、修改、刪除及管理。

這些功能可由後續版本擴充；目前主系統可先呼叫圖片分類 API，取得物品名稱、建議分類、描述及屬性資料，再自行決定如何儲存與使用。

## 專案定位

本專案是遺失物管理系統的獨立 AI Service，負責模型推論與 AI 結果整理；帳號、遺失物案件、資料庫儲存及一般業務流程由主系統負責。

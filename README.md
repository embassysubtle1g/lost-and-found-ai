> **Windows 雙擊啟動：** 在專案資料夾雙擊 `啟動尋物雷達.cmd`，會啟動服務並在就緒後自動開啟系統網頁。若啟動失敗，視窗會保留錯誤訊息。

> **本機 Windows（16GB RAM / RTX 4060）請先讀 [本機安裝、啟動與驗證](docs/local-windows.md)。** 此配置使用 Ollama 的量化 Qwen2.5-VL，保留 DINOv2 的原有向量流程，避免同時載入未量化 CPU Qwen。根目錄 `Start-System.ps1` 提供整套啟動；以下原 Docker 語言模型流程保留作其他環境參考。

# 尋物雷達｜Lost-and-Found-System

尋物雷達是一套以校園情境為核心的智慧失物招領系統，整合遺失協尋、拾獲登記、AI 圖片描述、圖片特徵向量比對與校園地圖，協助使用者登記物品、查找線索及確認媒合結果。

## 問題背景與專題目標

校園失物資訊經常分散於社群貼文、通訊群組及不同保管單位，使用者需要逐一查找。物品名稱與描述也可能因人而異，單靠文字搜尋，容易錯過外觀相似的物品。

本專題建立統一的失物登記與查詢介面，結合圖片描述、視覺特徵比對及地點資訊，提供可能的遺失與拾獲配對，減少人工查找與比對的負擔。

系統產生的描述與媒合建議供使用者參考，最終仍須人工確認物品特徵、所有權及歸還情況。

## 組員與分工

| GitHub 帳號 | 主要貢獻 |
| --- | --- |
| `normal3956-dot` | 負責後端系統與資料庫建置，設計資料存取及業務流程，完成前端、AI 模型與後端之間的 API 串接，並整合系統執行環境、測試與啟動流程。 |
| `embassysubtle1g` | 負責提供 DINOv2 視覺特徵模型與物品描述相關模型服務，協助規劃模型輸入、輸出與後端介接方式，支援 AI 功能整合。 |
| `una950927-del` | 負責完整前端介面的設計與實作，包含畫面配置、視覺樣式及操作互動，建立系統前端的主要基礎，並參與後續介面調整與功能更新。 |

### 前端開發與協作紀錄說明

本專案的前端介面由 `una950927-del` 完整製作。開發初期採用私下傳遞檔案的方式交付，再由後端整合至專案並統一提交，因此早期 GitHub 提交紀錄未完整反映其前端開發貢獻。

`una950927-del` 交付的前端成果是本系統完成整合的重要基礎；後續已開始使用個人 GitHub 帳號提交更新。組員分工以實際開發及交付內容為依據，提交次數僅作為協作紀錄參考。

## 系統方法摘要

系統將「物品描述」與「圖片比對」分為兩項互相配合的功能：

1. **物品描述：** 使用 Qwen 視覺語言模型分析照片，提供名稱、分類、顏色、標籤及描述建議，協助填寫通報資料。
2. **視覺特徵擷取：** 使用 DINOv2 將物品照片轉換為 768 維特徵向量，儲存於資料庫。
3. **案件媒合：** 比較遺失與拾獲案件的圖片向量相似度，產生候選配對。圖片向量尚未就緒時，另提供依填寫欄位產生的比對建議，並標示比對依據。
4. **地圖查詢：** 透過校園地圖、地點與時間篩選，協助使用者縮小查找範圍。
5. **人工確認：** 使用者核對物品資訊後，可排除不適合的配對，或確認媒合並結案。

### 操作流程

```text
上傳物品照片
    ↓
Qwen 提供物品描述與欄位建議
    ↓
使用者核對並完成遺失／拾獲登記
    ↓
照片存入 MinIO，案件資料存入 PostgreSQL
    ↓
DINOv2 在背景擷取圖片特徵向量
    ↓
系統比較遺失與拾獲案件，提供媒合建議
    ↓
人工核對，確認歸還並結案
```

## 案件刪除下架（2026-11-24）

開啟尚未結案的遺失或拾獲案件，在通報單位與電話旁點選「刪除案件」，確認後即可下架；原本的「複製聯絡方式」按鈕已移除，通報單位與電話仍保留顯示。

這項操作會透過 `DELETE /api/items/{reference}`，將資料庫中的案件狀態更新為 `WITHDRAWN`，並非僅在網頁暫時隱藏。沿用既有狀態，不必新增資料庫遷移。

- 下架案件不再出現在失物大廳、校園地圖、案件統計及媒合建議，公開照片端點也停止提供該照片。
- 重新整理或重新啟動系統後，仍維持下架狀態；重新掃描不會讓案件重新上架。
- 原始案件、照片及圖片向量保留，方便後續管理與必要時恢復。
- 已媒合歸還的案件保留結案紀錄，不提供刪除。
- 重複刪除已下架案件回傳成功；案件不存在回傳 HTTP 404。
- 目前沒有網頁復原或永久刪除按鈕。還原程式碼不會自動重新上架，恢復案件須另外處理資料庫狀態。

目前系統採免登入模式，任何能連入系統的使用者都可操作未結案案件的下架功能。

原始碼位於 `frontend/public/radar.html`、`backend/app/api/radar.py`，測試位於 `backend/tests/test_case_delete.py`。`Start-System.ps1` 會偵測並重新載入舊後端；更新前端後需重新建置。

## 校園地圖與單位整合（2026-11-21）

- 失物大廳加入最新版立體校園地圖，27 個可點選地點，支援時間熱點與案例篩選。
- 通報單位與遺失／拾獲地點共用相同 27 個名稱、順序及 5 個分組。選擇通報單位後自動帶入電話；沒有專屬分機的地點會標示校方總機。
- 地點與單位存在資料庫；通訊錄 138 筆歷史目錄保留，新選單只啟用與校園地點對應的 27 筆。電話來源版本與對應窗口保留於資料庫與文件。
- 本機穩定配置使用 DINOv2 CPU 容器與 Ollama 量化 Qwen 視覺模型；本機已確認 Qwen 使用 RTX 4060，無須建置 CUDA 版 DINOv2。
- 雙擊 `啟動尋物雷達.cmd` 可啟動服務，服務就緒後開啟網頁。首次下載仍須依下方步驟安裝依賴、建置前端與準備 CPU 映像及 Ollama 模型。
- 資料庫遷移目前到 `0007`；更新既有環境請執行 `alembic upgrade head`。使用本機啟動檔時會自動執行遷移，並在辨識到舊後端時載入新 API。

文件：[本機 Windows 啟動](docs/local-windows.md)、[校園地圖](docs/campus-map.md)、[通報單位與電話](docs/reporting-units.md)。

尋物雷達是一套整合遺失／拾獲登記、圖片描述、圖片向量比對和媒合結案的失物招領系統。

本分支整合前端、Backend、資料庫設定、DINOv2 與 Qwen 服務。系統目前採免登入操作。任何能連上系統的使用者，都可以登記資料、查看聯絡資訊、確認或排除配對，以及下架未結案案件。

## 目錄

- [問題背景與專題目標](#問題背景與專題目標)
- [組員與分工](#組員與分工)
- [系統方法摘要](#系統方法摘要)
- [案件刪除下架](#案件刪除下架2026-11-24)
- [系統功能](#系統功能)
- [資料夾結構](#資料夾結構)
- [資料流程與服務分工](#資料流程與服務分工)
- [資料庫與檔案儲存](#資料庫與檔案儲存)
- [開發環境與資源](#開發環境與資源)
- [第一次安裝](#第一次安裝)
- [資料取得與重現方式](#資料取得與重現方式)
- [已驗證結果與範例](#已驗證結果與範例)
- [AI 服務設定與啟動](#ai-服務設定與啟動)
- [使用方式](#使用方式)
- [更新既有環境](#更新既有環境)
- [API 總覽](#api-總覽)
- [常見問題](#常見問題)
- [驗證狀態與目前限制](#驗證狀態與目前限制)

## 系統功能

| 功能 | 操作內容 | 對應實作 |
| --- | --- | --- |
| 失物大廳 | 查看遺失與拾獲通報，依類型、名稱、顏色、標籤、分類和地點篩選 | 原稿頁面、GET /api/items |
| 遺失登記 | 填寫遺失物照片、名稱、分類、顏色、地點、時間、描述和聯絡方式 | POST /api/items，record_type=LOST |
| 拾獲登記 | 保存拾獲物的圖片、特徵、拾獲位置及保管／通報人聯絡方式 | POST /api/items，record_type=FOUND |
| 自動物品描述 | 上傳照片後自動填寫名稱、建議分類、外觀描述、顏色與特徵標籤 | Backend 呼叫 Qwen 圖片分類 API |
| 人工確認 | 辨識結果可修改，模型要求檢查時顯示提示，保留已手動編輯的欄位 | confidence、needs_review 與表單互動 |
| 圖片特徵擷取 | 登記照片後由背景工作呼叫 DINOv2，保存 768 維向量 | app/services/media.py |
| 相似物品媒合 | 比對尚未結案的遺失物與拾獲物，列出候選、相似度與比對理由 | GET /api/matches、pgvector |
| 排除與重新比對 | 排除結果存入資料庫；重新比對會清除排除紀錄並重新排程失敗照片 | 媒合 API |
| 確認結案 | 同一筆交易內將遺失及拾獲紀錄一起標記為已結案 | POST /api/matches/confirm |
| 物品詳情 | 查看照片、描述、地點、時間與通報單位及電話 | 前端詳細資料視窗 |
| 案件刪除下架 | 確認後將未結案案件標記為 WITHDRAWN，從列表、地圖與媒合退出 | DELETE /api/items/{reference} |
| 校園地圖 | 點選 27 個校園地點，依地點、時間及案件數量查找 | 前端 SVG 地圖、GET /api/locations |
| 通報單位與電話 | 共用 27 個校園地點清單，自動帶入聯絡電話 | GET /api/reporting-units |
| 管理 API | 保留機構分組、編輯、照片封面、刪除照片、下架及歸還等端點 | /api/v1/staff/*，免登入 |

目前首頁以提供的「遺失物.txt」畫面為基礎，另整合最新版校園地圖及共同地點／單位選單。登入流程與最早的綠色測試頁已移除。

## 資料夾結構

下列樹狀圖列出主要執行檔與資料夾，省略套件、模型快取與部分初始化檔。

```text
Lost-and-Found-System/                   # 專案根目錄，GitHub repo 名稱仍為 lost-and-found-ai
├── backend/                            # FastAPI 主系統
│   ├── app/
│   │   ├── api/
│   │   │   ├── radar.py                # 原稿介面的通報、描述、媒合、結案、案件下架和照片 API
│   │   │   ├── locations.py            # 校園地點目錄與舊地名對應
│   │   │   ├── reporting_units.py      # 共用 27 個通報單位、電話與地點關聯
│   │   │   └── items.py                # 公開查詢、機構分組、照片管理及歸還 API
│   │   ├── core/
│   │   │   ├── db.py                   # 載入 backend/.env，建立 PostgreSQL 連線
│   │   │   ├── organization.py         # 管理 API 的機構選擇與資料分組
│   │   │   ├── seed_demo.py            # 建立示範機構，無需建立登入帳號
│   │   │   ├── migrations/
│   │   │   │   ├── env.py              # Alembic 執行環境與離線 SQL 支援
│   │   │   │   └── versions/
│   │   │   │       ├── 0001_initial.py  # 初始資料表與 pgvector 擴充
│   │   │   │       ├── 0002_found_region.py
│   │   │   │       │                   # 新增拾獲區域，支援舊資料
│   │   │   │       ├── 0003_anonymous_management.py
│   │   │   │       │                   # 允許免登入歸還並保留既有歷史
│   │   │   │       ├── 0004_radar_interface.py  # LOST/FOUND、原稿欄位及排除配對表
│   │   │   │       ├── 0005_campus_locations.py  # 校園地點及案例關聯
│   │   │   │       ├── 0006_reporting_units.py   # 通訊錄歷史目錄
│   │   │   │       └── 0007_campus_reporting_units.py # 兩欄共用 27 個地點
│   │   │   └── …                       # 早期設定相容檔
│   │   ├── models/
│   │   │   └── items.py                # 拾獲物與照片資料查詢、機構歸屬查詢
│   │   ├── schemas/
│   │   │   ├── items.py                # 物品 API 輸入格式及欄位限制
│   │   │   └── organizations.py        # 機構名稱、地址與電話格式
│   │   ├── services/
│   │   │   ├── media.py                # 驗圖、Object Storage、DINOv2 呼叫與背景佇列
│   │   │   └── language_ai.py          # Qwen HTTP 用戶端、回應驗證與欄位轉換
│   │   └── main.py                     # API 入口、背景工作與建置後前端頁面
│   ├── tests/                          # API、搜尋契約、媒合與語言 AI 串接測試
│   │   └── test_case_delete.py          # 案件下架、結案保護及資料庫回滾驗證
│   ├── .env.example                    # 環境變數範本
│   ├── alembic.ini                     # 從 backend 目錄執行的遷移設定
│   ├── compose.yaml                    # PostgreSQL、MinIO 與兩種可選 AI 服務
│   └── requirements.txt                # 主系統 Python 依賴
├── frontend/                           # React／TypeScript 與原稿完整頁面
│   ├── public/
│   │   └── radar.html                  # 現行主要畫面、地圖、表單、詳情、下架與媒合互動
│   ├── src/
│   │   ├── assets/
│   │   │   └── style.css               # React 外層與完整頁面容器樣式
│   │   ├── components/                 # 先前 React 拆分元件
│   │   ├── pages/                      # 先前 React 拆分頁面
│   │   ├── services/                   # 先前 React API 用戶端
│   │   ├── hooks/                      # 先前機構選擇 Hook
│   │   ├── types/                      # 先前 TypeScript 型別
│   │   ├── App.tsx                    # 以 iframe 承載 radar.html，維持原稿版面
│   │   └── main.tsx                   # React 掛載入口
│   ├── index.html                     # Vite 入口
│   ├── package.json                   # 開發與正式建置指令
│   ├── package-lock.json              # 鎖定前端依賴
│   ├── tsconfig.json                  # TypeScript 設定
│   └── vite.config.ts                 # 開發伺服器與 Backend API 代理
├── services/                          # 與主系統分開安裝、執行的 AI 服務
│   ├── lost-and-found-ai/             # DINOv2 圖片向量服務
│   │   ├── app/
│   │   │   ├── api/v1/images.py        # inspect、embedding API
│   │   │   ├── models/                # DINOv2 模型載入與特徵擷取
│   │   │   ├── schemas/               # 向量回應格式
│   │   │   ├── services/              # 模型管理與擷取服務
│   │   │   └── main.py                # 獨立 FastAPI 入口
│   │   ├── Dockerfile                # CPU 版 PyTorch 容器
│   │   ├── requirements.txt           # DINOv2 依賴
│   │   └── 使用說明.md                # AI 服務原始說明
│   └── lost-and-found-language-ai/    # Qwen 圖片理解與物品描述服務
│       ├── app/
│       │   ├── api/v1/images.py        # POST /api/v1/images/classify
│       │   ├── core/config.py         # 模型名稱、裝置、量化和輸出長度
│       │   ├── models/vision_model.py # 選擇 Transformers 或本機 Ollama
│       │   ├── models/ollama_vision.py # 量化視覺模型 HTTP 介接、併發與輸出檢查
│       │   ├── schemas/image_classification.py
│       │   │                          # 名稱、分類、屬性與人工確認回應格式
│       │   ├── services/image_classification.py
│       │   │                          # 驗圖、提示詞、模型輸出解析
│       │   └── main.py                # 獨立 FastAPI 入口
│       ├── run-local.ps1             # 使用後端虛擬環境執行 Ollama 描述 API
│       ├── requirements-local.txt    # 輕量本機介接依賴
│       ├── Dockerfile                # 原始 Transformers CPU 容器與 8081 入口
│       ├── requirements.txt           # Qwen、PyTorch 和影像處理依賴
│       └── README.md                  # 語言 AI 原始 API 規格
├── docs/                              # 跨系統說明
│   ├── backend.md                    # 主系統啟動與更新
│   ├── integration.md                # 管理 API 與串接說明
│   ├── frontend-reference.md         # 原稿頁面與 Backend 對照
│   ├── language-ai.md                # 物品描述 API、環境變數與部署
│   ├── local-windows.md              # 本機安裝、啟動與驗證
│   ├── campus-map.md                 # 校園地圖與地點目錄
│   ├── reporting-units.md            # 通報單位電話來源與版本
│   └── validation.md                 # 測試與驗證限制
├── Start-System.ps1                  # 本機服務、遷移、舊後端更新與瀏覽器啟動
├── 啟動尋物雷達.cmd                  # Windows 雙擊入口
├── .gitignore                        # 忽略密碼設定、模型、套件和建置產物
└── README.md                         # 本文件
```

現行畫面與 API 呼叫邏輯集中在 frontend/public/radar.html。src/components、pages、services、hooks、types 保留先前拆分版本，現行 App.tsx 的入口使用原稿完整頁面。修改目前畫面時，請以 radar.html 為準。

backend/app/core/ 下保留的早期 Compose／Alembic 設定供舊版相容。新安裝使用 backend/compose.yaml 與 backend/alembic.ini。

## 資料流程與服務分工

### 登記與物品描述

1. 使用者上傳 JPEG、PNG 或 WebP 照片。
2. 前端呼叫主系統 POST /api/ai-recognize。
3. Backend 驗證照片，再以 multipart/form-data 的 file 欄位呼叫 Qwen 服務。
4. Qwen 回傳名稱、分類、外觀描述、顏色、材質、品牌、可辨識特徵、模型自評信心與人工確認提示。
5. Backend 將回應轉成前端表單欄位。使用者核對並修改後送出。
6. Backend 把通報資料寫入 PostgreSQL、照片寫入 MinIO，建立背景向量處理紀錄。

### 向量與媒合

1. 背景工作讀取待處理照片，呼叫 DINOv2 的 embedding API。
2. 驗證模型版本與向量維度，保存至 pgvector。
3. 媒合 API 比較仍開放的 LOST 與 FOUND 照片，模型版本相同時取每對物品中最高的圖片相似度。
4. 目前候選顯示門檻為 60%，畫面分數上限為 99%。原始向量相似度可能達 100%。
5. 圖片向量尚未就緒時，會依原稿的類別、顏色、地點和標籤規則計分，並在候選理由標示。
6. 使用者點重新比對，可取得最新候選、清除先前排除紀錄，並將失敗照片重新排程。
7. 確認媒合後，Backend 鎖定相關紀錄，在交易內一起結案。

同一張圖片可驗證向量串接；同一物品在不同角度、背景與光線下的檢索品質，仍需要測試圖片集驗收。

## 資料庫與檔案儲存

| 資料 | 儲存位置與用途 |
| --- | --- |
| campus_locations | 27 個校園地點、分區與 SVG 示意座標（非 GPS） |
| reporting_units | 單位電話來源、歷史目錄、啟用狀態與校園地點關聯 |
| items.campus_location_id、reporting_unit_id | 案例的地點及通報單位外鍵，既有文字資料保留 |
| organizations | 機構／通報資料分組，以及名稱、地址和電話 |
| items | 遺失與拾獲紀錄、狀態、時間、區域、描述等資料 |
| items.record_type | LOST 或 FOUND |
| items.radar_data | JSONB 保存原稿表單的顏色、標籤、描述和聯絡資料 |
| item_images | 圖片位置、封面、模型版本、向量及處理狀態 |
| dismissed_matches | 保存使用者排除的遺失／拾獲配對 |
| staff_accounts、sessions | 初始版本留下的歷史資料表，現行系統已移除登入功能 |
| MinIO Object Storage | 保存照片原檔 |
| PostgreSQL Docker volume | 保留資料庫內容 |
| model_cache、language_model_cache | 保存下載的模型檔案 |

照片處理狀態為 PENDING、PROCESSING、COMPLETED、FAILED。圖片顯示成功並不等於向量已完成，實際狀態與錯誤記錄在 item_images。

模型權重、上傳照片、資料庫內容及個人 .env 保存在執行環境，GitHub 保存程式與設定範本。下載程式到另一台電腦後，需要重新安裝環境並準備資料。

## 開發環境與資源

| 工具／服務 | 用途 |
| --- | --- |
| Git 或 GitHub ZIP | 取得程式版本 |
| Python 3.11 建議 | 執行主系統；現有 Backend 已在 Python 3.14 測試 |
| Node.js 22 LTS 或以上 | 安裝與建置 React 前端 |
| Docker Desktop（Windows） | 透過 Docker Compose 啟動資料庫、儲存和可選 AI 服務 |
| WSL 2（Windows） | Docker 的 Linux 容器執行環境 |
| 瀏覽器 | 操作系統和 /docs |
| 可連線 DINOv2 服務 | 圖片向量擷取 |
| 可連線 Qwen 圖片描述服務 | 自動填寫物品資訊 |

Codespaces 可執行前後端與 Docker，localhost 指向 Codespaces 自己。Windows 本機與 Codespaces 的資料、模型和網路位址各自獨立。

本專案提供的 AI 容器預設使用 CPU。Dockerfile 從 PyTorch CPU wheel 來源安裝，並檢查 PyTorch 的 CUDA build 欄位。Qwen 的 CPU Compose 設定使用 LOAD_IN_4BIT=false。

目前測試過的 Codespaces 為 32 GB 磁碟、約 8 GiB RAM，加入 Qwen 時遇到磁碟不足。Qwen2.5-VL-3B 的原始模型檔約 7.52 GB，還需要套件、容器、下載暫存及推論記憶體。CPU 改版容器與 Qwen 實際推論資源仍待量測。可透過 LANGUAGE_AI_URL 使用組員提供的服務。

### 套件與環境檔案

| 檔案 | 用途 |
| --- | --- |
| `backend/requirements.txt` | 主後端 Python 套件需求。 |
| `services/lost-and-found-ai/requirements.txt` | DINOv2 服務套件需求。 |
| `services/lost-and-found-language-ai/requirements.txt` | 原模型服務的套件需求。 |
| `services/lost-and-found-language-ai/requirements-local.txt` | 本機輕量模型介接環境的套件需求。 |
| `frontend/package.json`、`frontend/package-lock.json` | 前端套件、建置指令及鎖定版本。 |
| `backend/.env.example` | 後端環境變數範例，不包含個人實際設定。 |

首次安裝依序準備軟體、環境設定、Python 套件、前端建置、模型與容器，再啟動系統。模型權重、套件安裝目錄與使用者資料不包含在儲存庫內。本機 Windows 請優先依 [本機安裝、啟動與驗證](docs/local-windows.md) 準備 Ollama 與輕量介接服務，下方另保留主系統及其他部署方式的詳細指令。

## 資料取得與重現方式

### 測試照片

使用者可自行拍攝錢包、雨傘、鑰匙等日常物品，作為遺失及拾獲案件的測試照片。請使用自行拍攝或取得使用許可的圖片，避免包含個人證件、可辨識個資及敏感資訊。

本專案不依賴必須另外取得的私人失物資料集，使用者可透過自行建立案件重現主要流程。

1. **確認基本流程：** 使用同一張照片分別建立遺失與拾獲案件，檢查圖片上傳、向量產生及媒合流程。
2. **觀察不同拍攝條件：** 改用同一物品的不同角度照片，觀察比對結果。
3. **加入對照物品：** 使用外觀不同的物品作為對照，檢查候選配對是否合理。
4. **確認案件操作：** 完成人工核對後，測試確認結案或案件下架；取消刪除時案件應保留，確認下架後重新整理仍不顯示。

同一張照片的成功配對只能驗證流程，不能代表系統對不同照片的辨識準確率。

### 模型取得

DINOv2 與 Qwen 模型依安裝流程下載，不將模型權重直接放入儲存庫。

- DINOv2 使用設定的 `facebook/dinov2-base` 模型。
- 本機 Ollama 配置使用 `qwen2.5vl:3b`。
- 模型設定、下載方式與啟動步驟記錄於服務文件及 [本機安裝說明](docs/local-windows.md)。
- 首次執行須具備網路連線及足夠的磁碟空間，以完成模型下載。

### 校園地點與聯絡資料

校園地點清單由資料庫遷移建立；通報單位電話參考校方公開通訊資料，來源與版本說明記錄於 [通報單位與電話](docs/reporting-units.md)。

受使用限制的資料或素材不直接納入儲存庫，改提供來源及取得方式。後續使用者若新增其他圖片、資料集或素材，仍須確認其使用條件。

## 已驗證結果與範例

以下為本機開發環境中的功能驗證紀錄，並非大規模準確率評估，也不代表已完成其他電腦的乾淨環境安裝驗證。

| 驗證項目 | 觀察結果 |
| --- | --- |
| DINOv2 圖片特徵擷取 | 成功回傳 HTTP 200，特徵向量維度為 768。 |
| Qwen 圖片描述 | 紅色杯子測試圖片成功回傳名稱與描述；該次首次請求約 54.32 秒。 |
| 遺失／拾獲向量流程 | 測試案件的圖片處理狀態皆達到 COMPLETED，可取得媒合建議並完成結案。 |
| 案件下架 | 遺失與拾獲案件皆可下架；下架後停止出現在列表與媒合中，原始資料保留。 |
| 後端測試 | 2026-11-24 更新時，33 項測試通過，包含下架功能與本機資料庫回滾驗證。 |
| Ollama 介接測試 | 先前完成的 4 項介接測試通過。 |
| 前端建置 | 正式版建置通過。 |

### 圖片特徵擷取範例

以下為已驗證結果的摘要，並非 API 原始 JSON：

```text
圖片特徵擷取：成功
API 回應狀態：HTTP 200
特徵向量維度：768
圖片處理狀態：COMPLETED
```

### 案件下架範例

```text
操作：在未結案案件詳情中點選「刪除案件」並確認
API：DELETE /api/items/{reference}
成功回應：HTTP 204
資料庫狀態：WITHDRAWN

操作後：
案件退出大廳、地圖、統計與媒合建議。
重新整理後仍維持下架。
原始通報、照片與向量保留。
```

## 第一次安裝

### 1. 取得正式分支

```bash
git clone --branch Lost-and-Found-System https://github.com/embassysubtle1g/lost-and-found-ai.git
cd lost-and-found-ai
```

本儲存庫目前公開。使用 ZIP 時，在分支選單選 Lost-and-Found-System，再按 Code → Download ZIP 並解壓縮。

### 2. 準備 Backend 設定

進入 backend。Windows PowerShell 執行：

```powershell
cd backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Codespaces／Linux 執行：

```bash
cd backend
test -f .env || cp .env.example .env
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

編輯 backend/.env。資料庫密碼在 POSTGRES_PASSWORD 與 DATABASE_URL 內必須一致，URL 中的特殊字元需要編碼。既有環境沿用原本 .env。

| 變數 | 用途／預設 |
| --- | --- |
| POSTGRES_PASSWORD | PostgreSQL 啟動密碼 |
| DATABASE_URL | 主系統資料庫連線，預設連 127.0.0.1:5433 |
| OBJECT_ENDPOINT | MinIO，預設 http://127.0.0.1:9000 |
| OBJECT_ACCESS_KEY、OBJECT_SECRET_KEY | 圖片儲存帳密 |
| OBJECT_BUCKET | 圖片儲存 bucket 名稱 |
| DINOV2_URL | 向量服務，預設 http://127.0.0.1:8080 |
| DINOV2_MODEL | facebook/dinov2-base |
| DINOV2_VERSION | dinov2_vitb14 |
| LANGUAGE_AI_URL | 描述服務，預設 http://127.0.0.1:8081 |
| LANGUAGE_AI_TIMEOUT | 描述服務等待秒數，預設 300 |

### 3. 啟動資料庫與照片儲存

保持 Docker 執行中，在 backend 執行：

```bash
docker compose up -d --wait db storage
docker compose ps -a
```

### 4. 建立／升級資料表

Windows：

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Codespaces／Linux：

```bash
python -m alembic upgrade head
```

目前遷移依序為 0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0007。既有環境也必須執行升級，讓資料表與程式一致。

### 5. 建置前端

從 backend 返回儲存庫根目錄：

```bash
cd ..
npm --prefix frontend ci
npm --prefix frontend run build
```

建置產物位於 frontend/dist。Backend 的 8000 首頁直接提供該頁面。

### 6. 啟動主系統

Windows：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Codespaces／Linux：

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

保留此終端機執行。開啟 http://127.0.0.1:8000；Codespaces 從「連接埠」選擇 8000 並開啟瀏覽器。

## AI 服務設定與啟動

### 使用組員提供的服務

在 backend/.env 設定 Backend 能連上的基底網址，再重新啟動 Backend：

```dotenv
DINOV2_URL=http://你的向量服務主機:8080
LANGUAGE_AI_URL=http://你的描述服務主機:8081
```

主機需要具備從 Backend 執行環境連入的網路路徑。單純把對方電腦的 localhost 貼過來，會指向 Backend 所在的機器。

### 在同一個環境啟動 DINOv2

另開終端機，進入 backend：

```bash
docker compose --profile ai up -d --build ai
docker compose logs --tail=60 ai
```

第一次會下載套件與模型。API 文件位於 http://127.0.0.1:8080/docs。

### 在同一個環境啟動 Qwen

資源足夠時，在 backend 執行：

```bash
docker compose --profile language up -d --build language-ai
docker compose logs --tail=60 language-ai
```

服務使用 8081。模型延遲載入，第一次辨識才開始下載及載入。/health 回應成功代表 API 能回應，圖片分類成功才能確認模型可推論。

### 連接埠

| Port | 服務 |
| --- | --- |
| 8000 | 主系統網頁、/api 與 /api/v1、/docs |
| 5173 | 可選的 Vite 開發伺服器 |
| 8080 | DINOv2 |
| 8081 | Qwen 物品描述 |
| 5433 | 主機端 PostgreSQL；容器內為 5432 |
| 9000 | MinIO S3 API |

開發前端時可在另一個終端機執行 npm --prefix frontend run dev，使用 5173。Vite 將 /api 代理到同一環境的 8000。一般展示在建置後開啟 8000 即可。

## 使用方式

1. 開啟失物大廳，查看目前登記的遺失物與拾獲物。
2. 點「登記通報」，選擇遺失或拾獲。
3. 上傳照片，可點 AI 辨識自動填入名稱、分類、描述、顏色與標籤。
4. 依提示核對內容，選擇地點與通報單位，電話自動帶入，再填寫時間與其他資料。
5. 送出通報，Backend 保存資料與照片，背景處理圖片向量。
6. 進入 AI 智慧媒合中心，按重新比對取得背景處理完成後的候選。
7. 聯絡雙方確認物品，實際交還後再確認媒合結案。
8. 有誤的配對可以排除，重新比對會清除排除紀錄。
9. 若需下架未結案案件，開啟案件詳情，在通報單位與電話旁點「刪除案件」，核對確認視窗後送出。

Qwen 失敗時可以手動填寫後登記。DINOv2 未完成時，候選理由會顯示依填寫資料比對。
目前確認結案會更新資料庫狀態，尚未實作簡訊、Email 或其他通知發送。原稿部分按鈕文案仍有「通知失主」，請以實際聯絡流程完成通知。

### 日常啟動

完成首次安裝後，雙擊專案根目錄的 `啟動尋物雷達.cmd`，等待「系統已就緒」，再開啟 `http://127.0.0.1:8000`。啟動檔會確認 Docker 與必要服務；首次載入模型或模型重新載入時，辨識所需時間可能較長。

## 更新既有環境

先停止正在執行的 Backend。從 repo 根目錄執行：

```bash
git status
git fetch origin
```

若本機有尚未提交修改，先提交或備份後再切換。第一次取得正式分支時：

```bash
git switch --track origin/Lost-and-Found-System
```

若本機已有正式分支：

```bash
git switch Lost-and-Found-System
git pull --ff-only origin Lost-and-Found-System
```

接著重新建置前端，在 backend 更新依賴與遷移，再啟動：

```bash
npm --prefix frontend ci
npm --prefix frontend run build
cd backend
docker compose up -d --wait db storage
```

Linux／Codespaces：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Windows 使用 .venv\Scripts\python.exe 執行同樣的 pip、alembic 與 uvicorn 指令。
AI 容器程式更新時，對應服務需要重新 build。更新完成後，瀏覽器按 Ctrl+Shift+R。

既有測試分支與本機 language-test-* 分支可繼續保留作備份。正式更新來源使用 Lost-and-Found-System。

## API 總覽

| 方法／路徑 | 功能 |
| --- | --- |
| GET /health | Backend 健康回應 |
| GET /api/locations | 27 個校園地點、分組、地圖示意座標與舊地名別稱 |
| GET /api/reporting-units | 與校園地點一致的 27 個啟用通報單位及電話 |
| GET /api/items | 原稿大廳通報清單 |
| POST /api/items | 登記 LOST／FOUND，JSON 圖片為 data URL |
| DELETE /api/items/{reference} | 將未結案案件標記 WITHDRAWN；成功 204、不存在 404、已歸還 409 |
| GET /api/images/{id} | 讀取通報照片，結案後仍可查看；下架後停止公開提供 |
| POST /api/ai-recognize | JSON image，呼叫語言 AI 並轉換表單欄位 |
| GET /api/matches | 候選配對及比對理由 |
| POST /api/matches/confirm | 確認配對並一起結案 |
| POST /api/matches/dismiss | 排除一組配對 |
| DELETE /api/matches/dismissed | 清除排除紀錄並重新排程失敗照片 |
| GET /api/v1/public/items | 條件式公開拾獲物查詢與分頁 |
| GET /api/v1/public/items/{id} | 公開詳情 |
| POST /api/v1/public/search | multipart file，圖片向量搜尋 |
| GET /api/v1/public/organizations | 機構清單 |
| POST /api/v1/staff/organizations | 建立機構 |
| PUT /api/v1/staff/organization | 更新選定機構 |
| GET／POST /api/v1/staff/items | 機構分組的查詢／建檔 |
| GET／PUT /api/v1/staff/items/{id} | 詳情／修改 |
| POST /api/v1/staff/items/{id}/return | 登記已歸還 |
| POST /api/v1/staff/items/{id}/withdraw | 下架 |
| POST /api/v1/staff/items/{id}/images | 新增照片 |
| PUT /api/v1/staff/items/{id}/images/{image}/cover | 設定封面 |
| DELETE /api/v1/staff/items/{id}/images/{image} | 移除照片及比對向量 |
| POST /api/v1/staff/items/{id}/images/{image}/retry | 重試照片處理 |

管理 API 以 X-Organization-ID 選擇機構資料分組，未提供時使用第一個機構。現行系統免登入，可切換任一機構。完整輸入、輸出和錯誤格式請使用 Backend 的 /docs。

| 獨立 AI API | 功能 |
| --- | --- |
| DINOv2 GET /health | 服務健康檢查 |
| DINOv2 POST /api/v1/images/inspect | 圖片檢查 |
| DINOv2 POST /api/v1/images/embedding | 回傳模型資訊及 768 維向量 |
| Qwen GET /health | 服務健康檢查 |
| Qwen POST /api/v1/images/classify | 回傳名稱、分類、描述與屬性 |

主系統照片上限為 8 MB，支援 JPEG、PNG、WebP。語言 AI 原始服務上限 10 MB，經主系統操作時沿用 8 MB 限制。

## 常見問題

### 網頁顯示 500 或無法開啟

在 Backend 所在環境執行：

```bash
curl -i --max-time 5 http://127.0.0.1:8000/health
```

若連不上，檢查 uvicorn 終端機。若可回應，再看實際操作時的錯誤紀錄。8000 是主系統，8080 是獨立向量服務。

### 啟動時連不到 9000

在 backend 執行：

```bash
docker compose up -d --wait db storage
docker compose ps -a
docker compose logs --tail=40 storage
```

### 顯示「請先建置新版前端」

從 repo 根目錄執行 npm --prefix frontend ci、npm --prefix frontend run build，再重新開啟 8000。

### 物品已登記，圖片沒有配對

先到媒合中心重新比對，並確認至少各有一筆開放中的 LOST 和 FOUND。
向量未完成、已排除、已結案或相似度低於門檻，都會影響候選結果。

在 backend 查詢狀態：

```bash
docker compose exec -T db psql -U lost_found -d lost_found -c "SELECT i.name,i.record_type,p.state,p.embedding IS NOT NULL AS has_vector,p.error FROM items i LEFT JOIN item_images p ON p.item_id=i.id ORDER BY i.id DESC;"
```

### 物品描述服務失敗

檢查 LANGUAGE_AI_URL 與 language-ai 的紀錄。503 為服務不可用，504 為等待逾時，502 為回應格式不符。
第一次請求可能仍在下載及載入 Qwen。GPU 4-bit 模式需要可用 CUDA GPU，本 Compose CPU 模式已設為 false。

### Codespaces 空間不足

先停止正在下載／建置的工作，再查詢：

```bash
df -h /workspaces
docker system df
free -h
```

Docker 的 Build Cache SIZE 與可回收空間不同。資料庫、上傳照片及模型存在 volumes，清理前請辨認用途。
如果環境容量不足以放模型，可以使用組員已部署的 AI API。

### 停止與下次啟動

Backend 終端機按 Ctrl+C 停止主系統。Docker 服務可在 backend 執行 docker compose stop。
下次依需求啟動 db、storage 與 AI 服務，再啟動 Backend。模型快取與資料庫透過 volumes 保存。

## 驗證狀態與目前限制

- 2026-11-24 前端正式建置與 33 項主後端測試已通過；另有先前通過的 4 項 Ollama 介接測試。
- DINOv2 真實圖片已於 Codespaces 完成向量儲存與相同圖片媒合驗證。
- Qwen 已透過本機 Ollama 實際回傳圖片名稱與描述，並確認量化模型載入 RTX 4060；首次測試約 54 秒，後續依模型是否仍載入而異。
- DINOv2 CPU 容器已於本機完成建置、768 維向量、資料庫媒合與結案驗證。GPU 版建置已取消，目前沿用 CPU 配置。
- 多角度、不同背景、相似物品的辨識品質與 60% 門檻，需要以測試集評估。目前尚未完成大規模資料集評估，不宣稱整體辨識準確率。
- AI 產生的名稱、分類、顏色及描述可能有誤，須人工核對。圖片相似度是候選配對依據，不等於物品所有權或配對正確率。
- 執行速度受到硬體、模型載入狀態及其他程式資源使用量影響；拍攝角度、光線、背景與遮擋可能影響比對結果。
- 案件下架採保留資料的方式，網頁目前沒有永久刪除或復原功能。
- 候選圖片相似度與模型自評 confidence 各有不同用途，皆應搭配人工核對。
- 圖片媒合與文字欄位描述已實作，獨立的自然語言語意搜尋 API 尚未提供。
- 系統目前沒有登入與操作人身分驗證，確認結案後沒有自動通知。
- 模型版本／向量維度變更需要資料庫調整及舊照片重新擷取，現有向量欄位為 vector(768)。
- 前端建置依賴的既有 picomatch 安全通報已記錄於驗證文件，仍需追蹤修補版本。

## 其他文件

- [本機 Windows 啟動](docs/local-windows.md)
- [校園地圖](docs/campus-map.md)
- [通報單位與電話](docs/reporting-units.md)
- [Backend 安裝與更新](docs/backend.md)
- [API 整合說明](docs/integration.md)
- [原稿前端與資料流程](docs/frontend-reference.md)
- [Qwen 物品描述整合](docs/language-ai.md)
- [驗證記錄](docs/validation.md)
- [DINOv2 使用說明](services/lost-and-found-ai/使用說明.md)
- [語言 AI 原始 API 規格](services/lost-and-found-language-ai/README.md)

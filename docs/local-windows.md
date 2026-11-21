## 第一次從 GitHub 下載時

本文件後面的「已準備完成」描述是開發者本機驗證狀態。新電腦需先安裝 Python、Node.js、Docker Desktop／WSL2 與 Ollama，再依 README 建立 backend/.env、backend/.venv 並安裝主後端依賴。

在專案根目錄依序執行：

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
docker compose -f backend/compose.yaml --profile ai build ai
ollama pull qwen2.5vl:3b
```

第一行安裝鎖定版本的前端套件。第二行建置前端。第三行只建立 DINOv2 CPU 映像，首次需要下載套件。第四行準備 Ollama 量化 Qwen 視覺模型。完成後即可雙擊啟動檔；啟動檔沿用現有映像，不重新下載 CUDA。

## 雙擊開啟系統

在專案根資料夾雙擊 `啟動尋物雷達.cmd`。它會執行既有 `Start-System.ps1 -OpenBrowser`，必要時啟動 Docker Desktop 與 Ollama，再啟動資料庫、照片儲存、DINOv2 CPU 版、本機 Qwen 描述 API 和主後端。確認服務就緒後才開啟預設瀏覽器。

成功後啟動視窗可自動關閉，後端繼續在背景運作。失敗時視窗保留訊息，按任意鍵後關閉。關閉瀏覽器不會停止後端、Docker 或 Ollama。請保留啟動檔與專案資料夾的相對位置，亦可對啟動檔建立桌面捷徑。

> **目前使用穩定 CPU DINOv2 + Ollama GPU Qwen。** GPU DINOv2 建置已取消，設定已還原；Start-System.ps1 使用 `--no-build` 啟動既有 CPU 映像。下方 GPU 更新章節僅為先前嘗試的歷史紀錄，請勿依該章重跑建置。

# 本機 Windows 執行與驗證（2026-11-20）

此設定針對目前的 16GB RAM、RTX 4060 Laptop 8GB 電腦。網頁與後端仍使用原有 API。

## 服務分工

| 服務 | 位址 | 執行方式與功能 |
| --- | --- | --- |
| React 前端及 FastAPI 主後端 | http://127.0.0.1:8000 | backend/.venv；登記、查詢、配對與結案 |
| PostgreSQL + pgvector | 127.0.0.1:5433 | Docker db；儲存案例與 768 維向量 |
| MinIO | http://127.0.0.1:9000 | Docker storage；儲存照片 |
| DINOv2 | http://127.0.0.1:8080 | Docker ai；CPU 執行，登記後背景產生向量 |
| 物品描述 API | http://127.0.0.1:8081 | 本機 Python 輕量介接層；維持 multipart classify API |
| Ollama Qwen2.5-VL | http://127.0.0.1:11434 | qwen2.5vl:3b，Q4_K_M；自動選擇裝置，本機測試確認使用 GPU |

原本 Docker language-ai 是未量化 CPU 模型。此機請停止它，避免與本機描述 API 衝突並佔用過多記憶體。原有 Transformers 模式與 Dockerfile 仍保留給其他部署使用。

## 安裝與啟動

目前此電腦已有 Node.js、Python、Docker Desktop 與 Ollama；前端、backend/.venv 與模型都已準備完成。

先開啟 Docker Desktop，再於 PowerShell 執行：

```powershell
cd 'C:\Users\USER\Desktop\期末專案\lost-and-found-ai-Lost-and-Found-System'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-System.ps1
```

第一行進入專案根資料夾。第二行用獨立的 PowerShell 執行本專案啟動腳本；ExecutionPolicy 僅作用於該次程序，不修改系統永久設定。

腳本會停止舊 language-ai 容器、啟動 db/storage/ai、確認 Ollama 模型存在，再啟動本機描述 API 與主後端。資料庫與照片資料卷保留。背景 Python 記錄在 .runtime/，Docker 記錄仍透過 docker compose logs 查看。腳本只在服務未運行時啟動它，不會自動重新載入已運行的舊 Python 程式。

只啟動描述 API 時：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\services\lost-and-found-language-ai\run-local.ps1
```

這一行使用既有 backend/.venv 啟動 8081，並設定 MODEL_BACKEND=ollama；需先停止使用同一埠的舊服務。

模型權重存放於使用者的 Ollama 模型資料夾，不會放進 Git。原 Hugging Face 模型快取與舊 Docker 映像仍保留，未刪除。

## 操作

開啟 http://127.0.0.1:8000，重新整理後上傳照片，按辨識。名稱、分類、顏色、標籤與描述由 Qwen 提供，請人工核對。圖片最長邊縮至 896 像素、上下文限制 4096，最多產生 512 tokens，同時只接受一筆描述。模型閒置兩分鐘可被卸載；第一次或重新載入時較慢。

提交 LOST/FOUND 後，DINOv2 在背景產生向量。到媒合中心重新掃描，向量配對結果會標示 DINOv2；尚未有向量時，系統原有的欄位比對仍可能出現，請依理由區分。

前端辨識等待上限 270 秒，描述 API 至 Ollama 上限 240 秒，主後端語言 API 上限 300 秒。網路中斷或模型失敗會顯示錯誤，解除按鈕等待。請避免重複送出。

## 本機驗證結果

- 後端既有 20 項測試通過。
- Ollama 介接 4 項測試通過：圖片請求、忙碌拒絕、連線錯誤鎖定釋放、截斷輸出拒絕。
- TypeScript 與 Vite 建置通過。
- 透過主後端 /api/ai-recognize 實際辨識紅色杯子測試插畫，HTTP 200，首次約 54.32 秒；回傳紅色杯子及描述。
- Ollama /api/ps 顯示 Q4_K_M，size_vram=2760816721，確認 GPU 載入約 2.6GiB。
- 變更 GPU 前的 CPU 基準：DINOv2 實際回傳 HTTP 200、768 維向量，約 1.91 秒。
- 建立兩筆暫存 LOST/FOUND、讀取儲存照片、背景向量都 COMPLETED、資料庫向量配對顯示 99、確認結案 HTTP 204；已精確清除該次測試資料與照片。

以上證明服務串接與基本流程成功，不代表複雜照片辨識皆正確，也不代表同圖 99 分是經校準的尋回機率。前端原設計將 100 的顯示值上限設為 99。

啟動腳本已通過 PowerShell 語法檢查；由於此操作環境無法取得 Docker named pipe 權限，尚未直接執行整支腳本。各服務與實際 API 已分別驗證。需要你在一般 PowerShell 執行它時才有正常 Docker 使用權。

本機驗證詳細 JSON 位於 .runtime/。該資料夾被 Git 忽略。

## DINOv2 GPU 更新

2026-11-20 已把 ai 容器改為 NVIDIA GPU 配置：Compose `gpus: all`、`DEVICE=cuda`，Dockerfile 安裝 PyTorch 2.10.0 / torchvision 0.25.0 的 CUDA 12.8 版本。CUDA 執行階段由 Python wheels 提供；本機仍需 NVIDIA 驅動與 Docker Desktop GPU 支援。

Qwen 繼續由 Windows Ollama 執行，兩個模型共用同一張 RTX 4060。資料庫、向量 SQL 比對、照片儲存、主後端與圖片解碼仍使用 CPU/RAM。GPU 加速不會讓系統 RAM 用量歸零。

重新建置指令（在 backend 資料夾）：

```powershell
docker compose --profile ai up -d --build ai
```

這一行下載 CUDA 依賴、建置並啟動 DINOv2 GPU 容器，沿用同一個模型快取與 8080 埠。

檢查實際裝置：

```powershell
Invoke-RestMethod 'http://127.0.0.1:8080/health' | ConvertTo-Json -Depth 4
```

這一行讀取服務的健康狀態與模型裝置；`model_info.device` 必須顯示 `cuda:0` 或其他 CUDA 裝置，不能只依啟動成功判斷 GPU 有啟用。沒有 GPU 時服務會明確報錯，不會悄悄改回 CPU。

GPU 容器正在等待一般使用者 PowerShell 建置；目前尚未完成 GPU 推論驗證。後續測試結果記錄於 .runtime/gpu-validation.json。

設定依據：[PyTorch CUDA 版本安裝](https://pytorch.org/get-started/previous-versions/)、[Docker Compose GPU 設定](https://docs.docker.com/compose/how-tos/gpu-support/)。

# Python 台股分析機器人 (Stock Analysis Bot)

這是一個自動化的股票分析機器人，使用 Python 撰寫，部署於 Google Cloud Run。
核心功能包含：
1. 讀取 Google Sheets 上的股票觀察清單 (Watchlist)。
2. 使用 FinMind API 抓取台股日線資料。
3. 計算技術指標 (MA, KD)。
4. 使用 Google Gemini API 產生繁體中文分析短評。
5. 透過 LINE Messaging API 發送每日彙整報告。

## 專案結構

- `main.py`: Flask 應用程式入口，處理 `/run_analysis` 請求。
- `core/`: 核心邏輯模組
  - `sheets.py`: 處理 Google Sheets 讀取。
  - `data.py`: 處理 FinMind 資料抓取。
  - `analysis.py`: 處理技術指標計算與 AI 分析。
  - `notifier.py`: 處理 LINE 訊息發送。
- `config.py`: 設定檔管理。

## 本地開發與測試

### 1. 環境設定

請先建立 `.env` 檔案，並填入以下資訊：

```ini
# FinMind API Token (選填，建議申請以提高額度)
FINMIND_API_TOKEN=your_finmind_token

# Google Gemini API Key (必填)
GEMINI_API_KEY=your_gemini_api_key

# LINE Messaging API 設定 (必填)
LINE_CHANNEL_ACCESS_TOKEN=your_line_access_token
LINE_CHANNEL_SECRET=your_line_secret
LINE_USER_ID=your_user_id (或是 Group ID)

# Google Sheets 設定
# 您的 Service Account JSON 檔案路徑
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
# 您的觀察清單 Google Sheet 網址
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/xxxxxxx
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 準備 Google Sheets 憑證

請將您的 Google Cloud Service Account 金鑰下載並儲存為 `credentials.json` (或您的自訂檔名)，放在專案根目錄。
**注意：** 您必須在 Google Sheet 的共用設定中，將該 Service Account 的 email 加入編輯者或檢視者。

### 4. 執行應用程式

```bash
stock_id="2330" python main.py
```
(實際上 `main.py` 是 web server，可以執行後用瀏覽器或 curl 觸發)

```bash
python main.py
```
啟動後，訪問 `http://localhost:8080/run_analysis` 即可手動觸發分析並發送 LINE 通知。

## Google Cloud Run 部署

1. **建立 Docker 映像檔**
   (建議直接使用 Cloud Build 或本機 docker build)

2. **部署到 Cloud Run**
   設定環境變數 (Environment Variables) 對應 `.env` 的內容。
   *注意：`GOOGLE_SHEETS_CREDENTIALS_FILE` 在 Cloud Run 上處理比較麻煩，建議可以將 JSON 內容 base64 encode 後放在環境變數，再由程式代碼還原，或是使用 Google Secret Manager。本範例預設讀取檔案，您可能需要將 json 檔 COPY 進 Docker image (不建議提交到 git) 或使用 Secret Manager 掛載。*

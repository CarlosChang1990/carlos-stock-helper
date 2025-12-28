# Python 台股與財報分析機器人 (Stock Analysis Bot)

這是一個全自動化的台股分析機器人，部署於 **Google Cloud Run**。它結合了 **FinMind** (股價/財報)、**Mystery Pyramid** (籌碼)、**Google Gemini AI** (EPS 預估) 與 **LINE Messaging API**，每天自動為您推送最精準的市場分析。

## 核心功能 (Features)

### 1. 市場概況 (Market Overview)
- **大盤分析**：每日報告開頭自動分析 **加權指數 (TAIEX)** 與 **櫃買指數 (TPEx)**。
- **技術指標**：包含收盤價、日線慣性 (Inertia)、三日狀態 (3-Day Rules)。

### 2. 個股全方位分析 (Comprehensive Stock Analysis)
針對 Google Sheets 觀察清單中的每一檔股票，進行四大面向分析：

*   **[基本訊息]**：收盤價、漲跌幅。
*   **[技術面]**：
    *   **慣性分析**：日線 (Daily)、週線 (Weekly)、月線 (Monthly) 慣性判斷 (與多空轉折)。
    *   **三日狀態**：判斷 3 日高點/低點的突破與跌破，標示「多方攻擊」、「空方攻擊」或「盤整」。
    *   **支撐壓力**：自動計算近期的支撐區與壓力區。
*   **[籌碼面] (Chips)**：
    *   自動爬取「神秘金字塔」股權分散表。
    *   **大戶/散戶動向**：計算 400 張以上大戶與 50 張以下散戶的持股增減。
    *   **連續週數**：自動偵測大戶/散戶連續增減的週數。
*   **[基本面] (Fundamentals)**：
    *   **月營收**：最新月營收 (MoM, YoY)。
    *   **季財報**：毛利率 (GM)、營益率 (OM)、淨利率 (NM)、每股盈餘 (EPS)。

### 3. AI 智能擴充 (Powered by Gemini 2.5 Pro)
*   **法人 EPS 預估**：
    *   當偵測到新營收或財報時，自動觸發 AI 聯網搜尋。
    *   搜尋 **本年度** 與 **下年度** 的法人 EPS 預估值。
    *   **極簡輸出**：只顯示「年份 / 數值 / 趨勢 (調升/調降) / 來源連結」，拒絕廢話。
    *   使用 `google-genai` V1 SDK 與 Google Search Tool。

### 4. 自動化整合 (Automation)
*   **Google Sheets連動**：
    *   讀取 Watchlist (代號/名稱)。
    *   **自動補名**：若清單中缺少股票名稱，機器人會自動抓取並更新回 Google Sheet。
    *   **狀態追蹤**：更新「最後營收月份」與「最後財報季度」，避免重複觸發 AI 分析。
*   **LINE 推播**：
    *   分析結果自動推送到 LINE。
    *   支援長訊息自動分割。
    *   Webhook 回應：可透過簡單指令與機器人互動 (如 "id", "測試")。

---

## 專案結構 (Project Structure)

```text
.
├── main.py             # 程式入口 (Flask Web Server / Cloud Run Entrypoint)
├── deploy.sh           # 自動化部署腳本 (一鍵部署到 Cloud Run)
├── config.py           # 環境變數設定
├── requirements.txt    # Python 依賴套件
├── core/
│   ├── analysis.py     # 整合分析邏輯 (Market, Tech, Chip, Fundamental, Report)
│   ├── strategy.py     # 技術指標運算 (Inertia, 3-Day Rule, Support/Resistance)
│   ├── chips.py        # 籌碼面爬蟲 (Mystery Pyramid)
│   ├── ai.py           # Gemini AI 搜尋與生成 (EPS Forecast)
│   ├── data.py         # FinMind 資料獲取
│   ├── sheets.py       # Google Sheets 讀寫
│   └── notifier.py     # LINE 訊息發送
└── scripts/            # 測試與工具腳本
```

---

## 快速開始 (Quick Start)

### 1. 環境變數 (.env)
請複製 `.env.example` (若有) 或建立 `.env`，填入以下必要資訊：

```ini
# API Keys
FINMIND_API_TOKEN=your_finmind_token  (建議申請)
GEMINI_API_KEY=your_gemini_api_key    (必須支援 Gemini 2.5 Pro / Google Search)

# LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_CHANNEL_SECRET=...
LINE_USER_ID=...

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID
```


### 1.5 準備 Google Sheets 憑證 (credentials.json)
為了讓機器人讀寫您的試算表，請依照以下步驟設定 Google Service Account：

1.  前往 **[Google Cloud Console](https://console.cloud.google.com/)**。
2.  建立一個新專案 (或選擇現有專案)。
3.  搜尋並啟用 **Google Sheets API** 和 **Google Drive API**。
4.  前往 **IAM 與管理 > 服務帳戶**，建立一個服務帳戶。
5.  進入該服務帳戶，選擇 **金鑰 (Keys)** > **新增金鑰** > **建立新金鑰** > 選擇 **JSON** 格式。
6.  下載 JSON 檔案，將其重新命名為 `credentials.json` 並放入專案根目錄。
7.  **重要步驟**：打開您的 `credentials.json`，複製裡面的 `client_email` 地址 (例如 `stock-bot@project-id.iam.gserviceaccount.com`)。
8.  回到您的 Google Sheet 試算表，點擊右上角 **共用 (Share)**，將該 Email 加入並給予 **編輯者 (Editor)** 權限。

### 2. Google Sheets 格式
您的觀察清單 Sheet 應具備以下欄位 (Header 在第一行)：

| Stock ID (A) | Stock Name (B) | Last Rev (C) | Last Fin (D) |
| :--- | :--- | :--- | :--- |
| 2330 | 台積電 | 2024-11 | 2024-Q3 |
| 3037 | (若空缺會自動補) | | |

### 3. 部署到 Google Cloud Run
本專案提供一鍵部署腳本，會自動讀取 `.env` 並設定 Cloud Run 環境變數與 Cloud Scheduler 排程。

```bash
# 確保已安裝並登入 gcloud CLI
./deploy.sh
```

部署成功後：
*   **Webhook**: `https://<your-service-url>/callback` (請填入 LINE Developer Console)
*   **Scheduler**: 預設每週一至週五 早上 06:00 (Asia/Taipei) 自動執行分析。

### 4. 手動觸發
您也可以透過瀏覽器或 curl 手動觸發分析：
```bash
curl -X POST https://<your-service-url>/run_analysis
```

---

## 技術棧 (Tech Stack)
*   **Language**: Python 3.9+
*   **Web Framework**: Flask
*   **Server**: Gunicorn
*   **Cloud Platform**: Google Cloud Run + Cloud Scheduler
*   **Data API**: FinMind, Yahoo Finance (Backup), Mystery Pyramid (Scraping)
*   **AI Model**: Google Gemini 2.5 Pro (via `google-genai` SDK)

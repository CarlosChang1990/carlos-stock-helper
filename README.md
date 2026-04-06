# 📈 Python 台股智慧分析機器人 (Stock Analysis Bot)

[![Deployment](https://img.shields.io/badge/Deployment-Google%20Cloud%20Run-blue?logo=google-cloud)](https://cloud.google.com/run)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-red?logo=googlegemini)](https://deepmind.google/technologies/gemini/)
[![Messaging](https://img.shields.io/badge/Platform-LINE%20Messaging%20API-00C300?logo=line)](https://developers.line.biz/)

這是一個整合 **技術面、籌碼面、基本面** 與 **AI 智慧** 的全自動台股分析機器人。它不僅能每天自動推送精美的 **Flex Message** 分析報告，還能透過 **AI 圖片辨識** 直接分析您的對帳單或自選股截圖。

---

## 🌟 核心功能 (Featured Highlights)

### 1. 🎨 精美 Flex Message 報告
分析結果不再是冰冷的文字，而是以 LINE **Flex Message Carousel** 格式呈現。
- **色彩語義化**：漲跌紅綠標示、技術面趨勢顏色區分。
- **結構化排版**：清楚區分「基本訊息」、「技術面」、「籌碼面」與「基本面」。
- **自適應設計**：自動分割多個 Carousel，支援大量股票清單而不斷字。

### 2. 👁️ AI 截圖智慧辨識
直接將 **券商 App 的自選股截圖** 或 **對帳單** 傳入 LINE。
- **自動辨識**：利用 Gemini Vision Pro 提取圖片中的股票代碼與名稱。
- **自動更新清單**：將辨識結果自動同步至 Google Sheets 觀察清單。
- **即時分析**：完成更新後立即觸發全方位分析回報。

### 3. 🧠 雙重技術面引擎 (Twin-Engine TA)
- **慣性分析 (Inertia)**：判斷日/週線的多空背景慣性，掌握大趨勢。
- **三日狀態 (3-Day Rule)**：精準捕捉短線多空轉折與支撐壓力區間。
- **均線策略 (MA Cross)**：自動偵測月線 (MA20) 支撐與乖離狀態。

### 4. 📊 全方位數據整合
- **籌碼面**：自動爬取「神秘金字塔」股權分散表，追蹤大戶/散戶週動向。
- **基本面**：串接 **FinMind**，包含最新月營收 (YoY/MoM)、營收微縮趨勢圖 (Sparkline) 與近四季 EPS/營益率。
- **AI 擴充**：當有新營收或財報時，AI 自動檢索法人 EPS 預估值。

### 5. ☁️ 無縫雲端自動化
- **Google Sheets 同步**：觀察清單即資料庫，支援自動補名與進度追蹤。
- **Cloud Scheduler**：每週一至週五自動定時執行分析。
- **Cloud Run 部署**：高彈性、低成本的 Serverless 架構。

---

## 📂 專案結構 (Project Structure)

```text
.
├── main.py                 # Flask Web Server & LINE Webhook 進入點
├── config.py               # 環境變數與配置中心
├── deploy.sh               # Cloud Run 一鍵部署腳本
├── core/                   # 核心邏輯包
│   ├── analysis.py         # 整合分析協調器 (Aggregator)
│   ├── flex_message.py     # LINE Flex Message 佈局建構器
│   ├── strategy.py         # 技術指標運算核心 (Inertia, 3-Day, MA)
│   ├── ai.py               # Gemini AI 整合 (圖片辨識 & 檢索)
│   ├── data.py             # 數據獲取 (FinMind / Yahoo)
│   ├── sheets.py           # Google Sheets 讀寫服務
│   ├── chips.py            # 籌碼資料抓取 (Mystery Pyramid)
│   └── notifier.py         # LINE 推播/回覆服務
├── scripts/                # 維護與測試工具腳本
└── tests/                  # 單元測試與整合驗證
```

---

## 🚀 快速開始 (Quick Start)

### 1. 設置環境變數
建立 `.env` 檔案並填入以下資訊：
```ini
# API 授權
FINMIND_API_TOKEN=your_token
GEMINI_API_KEY=your_key

# LINE 頻道設定
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
LINE_USER_ID=your_id

# Google Sheets 連動
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_ID
```

### 2. 準備 Google Sheets
1. 建立一個 Google 試算表。
2. 標題列：`Stock ID`, `Stock Name`, `Last Rev`, `Last Fin`。
3. 將 Google 服務帳戶 Email 加入試算表的「編輯者」。
4. 將服務帳戶金鑰儲存為 `credentials.json` 置於根目錄。

### 3. 一鍵部署
確保已安裝 `gcloud` CLI 並登入：
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🛠️ 技術棧 (Tech Stack)

- **語言**: Python 3.9+
- **架構**: Flask + Gunicorn (Web)
- **雲端**: Google Cloud Run / Cloud Scheduler
- **AI**: Google Gemini (Powered by `google-genai` SDK)
- **數據**: FinMind API, BeautifulSoup4 (Scraping)

---

## 📝 授權 (License)
本專案僅供研究與學習使用，投資有風險，報告內容僅供參考。

# 澳門法院判決書爬蟲

🕸️ 自動爬取澳門法院判決書，支援日曆視圖、日期分類，並可同步到 Google Drive

🔗 **GitHub Actions 一鍵爬蟲**: [點擊運行](https://github.com/tc-gh-claw/court-crawler/actions/workflows/crawl.yml)

![Screenshot](https://via.placeholder.com/800x400/4f46e5/ffffff?text=Court+Crawler+Screenshot)

## ✨ 功能特色

- 🤖 **一鍵爬蟲** - GitHub Actions 自動化爬取
- 📅 **日曆視圖** - 直觀查看每日判決書數量
- 📊 **統計儀表板** - 年份/月份/法院分佈圖表
- 📈 **時間線模式** - 按日期排序瀏覽
- 🔍 **智能搜尋** - 支援關鍵字、法院、年份範圍
- ⬇️ **批量下載** - 選擇性下載，自動按日期分類
- ☁️ **Google Drive** - 自動備份到雲端硬碟

## 🚀 快速開始

### 方法一：一鍵爬蟲（推薦）

1. 進入 [Actions 頁面](https://github.com/tc-gh-claw/court-crawler/actions/workflows/crawl.yml)
2. 點擊 **「Run workflow」** 按鈕
3. 選擇參數：
   - **年份**: `2020-2025` 或 `2025` 或 `2023,2024,2025`
   - **法院**: `all` (全部) 或 `tui` (終審) 或 `tui,tsi` (終審+中級)
4. 點擊 **「Run workflow」** 開始爬蟲

**定時任務**: 每周一早上 9 點自動運行

### 方法二：本地運行

```bash
# 1. 克隆專案
git clone https://github.com/your-username/court-crawler.git
cd court-crawler

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 直接運行爬蟲
python -c "
from crawler_core import CourtCrawler
crawler = CourtCrawler()
results = crawler.crawl_all(years=[2025], courts=['tui', 'tsi'])
print(f'找到 {len(results)} 個判決書')
"

# 4. 或啟動 Web 服務
python app.py
# 開啟瀏覽器訪問 http://localhost:5000
```

### 方法三：線上部署

#### Render (推薦)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork 此專案到你的 GitHub
2. 點擊上方按鈕部署到 Render
3. 設定環境變數（見下方）

#### Heroku

```bash
# 1. 安裝 Heroku CLI 並登入
heroku login

# 2. 建立應用
heroku create your-court-crawler

# 3. 設定環境變數（Google Drive）
heroku config:set GOOGLE_CLIENT_ID=xxx
heroku config:set GOOGLE_CLIENT_SECRET=xxx
heroku config:set GOOGLE_REFRESH_TOKEN=xxx

# 4. 部署
git push heroku main
```

#### VPS / 雲伺服器

```bash
# 使用 Docker
docker build -t court-crawler .
docker run -p 5000:5000 \
  -e GOOGLE_CLIENT_ID=xxx \
  -e GOOGLE_CLIENT_SECRET=xxx \
  -e GOOGLE_REFRESH_TOKEN=xxx \
  court-crawler
```

## 🔑 Google Drive 設定

### 本地開發

1. 去 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立專案 → 啟用 Drive API → 建立 OAuth 憑證（桌面應用程式）
3. 下載 `credentials.json` 放到專案根目錄
4. 執行 `python setup_drive.py` 完成授權

### 線上部署（Render/Heroku/GitHub Actions）

雲端無法使用 OAuth 彈窗授權，需要手動取得 Refresh Token：

```bash
# 1. 安裝依賴
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# 2. 執行以下 Python 腳本取得 Token
python get_refresh_token.py
```

3. 將取得的值設定為環境變數：

```bash
# Render/Heroku
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret  
GOOGLE_REFRESH_TOKEN=your_refresh_token

# GitHub Actions (在 Settings -> Secrets and variables -> Actions 中設置)
Settings -> Secrets and variables -> New repository secret
```

## ⚙️ 環境變數

| 變數 | 說明 | 必需 |
|------|------|------|
| `PORT` | 服務埠號 | 否（預設 5000） |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | 用 Drive 時必需 |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | 用 Drive 時必需 |
| `GOOGLE_REFRESH_TOKEN` | Google OAuth Refresh Token | 用 Drive 時必需 |
| `BASE_FOLDER_NAME` | Google Drive 資料夾名稱 | 否（預設「澳門法院判決書」） |

## 📁 專案結構

```
court-crawler/
├── app.py                 # Flask 後端主程式
├── crawler_core.py        # 核心爬蟲模組（新增）
├── auto_download.py       # 自動下載腳本
├── setup_drive.py         # 本地 Drive 設定助手
├── get_refresh_token.py   # 取得 Refresh Token
├── requirements.txt       # Python 依賴
├── runtime.txt            # Python 版本
├── Procfile               # Heroku 配置
├── render.yaml            # Render 配置
├── Dockerfile             # Docker 配置
├── .github/
│   └── workflows/
│       └── crawl.yml      # GitHub Actions 一鍵爬蟲
├── templates/
│   └── index.html         # 前端頁面
├── static/                # 靜態檔案
└── README.md
```

## 🛠️ API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 主頁面 |
| `/api/crawl` | POST | 觸發爬蟲 |
| `/api/crawl-all` | POST | 觸發完整爬蟲 |
| `/api/search` | POST | 搜尋判決書 |
| `/api/calendar` | GET | 取得日曆數據 |
| `/api/stats` | GET | 取得統計數據 |
| `/api/start` | POST | 開始下載 |
| `/api/stop` | POST | 停止下載 |
| `/api/status` | GET | 取得下載狀態 |
| `/api/export` | GET | 匯出所有數據 |

## 🏛️ 支援的法院

| 代碼 | 法院名稱 | 說明 |
|------|----------|------|
| `tui` | 終審法院 | 最高審級 |
| `tsi` | 中級法院 | 上訴審級 |
| `tjb` | 初級法院 | 一審 |
| `ta` | 行政法院 | 行政訴訟 |

## 📝 技術棧

- **後端**: Python + Flask
- **爬蟲**: BeautifulSoup4 + Requests (核心: `crawler_core.py`)
- **自動化**: GitHub Actions
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **雲端**: Google Drive API
- **部署**: Docker + Render/Heroku

## ⚠️ 免責聲明

- 此工具僅供學術研究使用
- 請遵守澳門法院網站的使用條款
- 請勿過度頻繁爬取，建議設置適當延遲

## 📜 License

MIT License

---

Made with ❤️ for legal research

# 澳門法院判決書爬蟲

🕸️ 自動爬取澳門法院判決書，支援日曆視圖、日期分類，並可同步到 Google Drive

🔗 **Live Demo**: [https://your-username.github.io/court-crawler](https://your-username.github.io/court-crawler) (GitHub Pages)

![Screenshot](https://via.placeholder.com/800x400/4f46e5/ffffff?text=Court+Crawler+Screenshot)

## ✨ 功能特色

- 📅 **日曆視圖** - 直觀查看每日判決書數量
- 📊 **統計儀表板** - 年份/月份/法院分佈圖表
- 📈 **時間線模式** - 按日期排序瀏覽
- 🔍 **智能搜尋** - 支援關鍵字、法院、年份範圍
- ⬇️ **批量下載** - 選擇性下載，自動按日期分類
- ☁️ **Google Drive** - 自動備份到雲端硬碟

## 🚀 快速開始

### 本地運行

```bash
# 1. 克隆專案
git clone https://github.com/your-username/court-crawler.git
cd court-crawler

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定 Google Drive (可選)
# 參考下方「Google Drive 設定」

# 4. 啟動服務
python app.py

# 5. 開啟瀏覽器訪問 http://localhost:5000
```

### 線上部署

#### 方法一：Render (推薦)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork 此專案到你的 GitHub
2. 點擊上方按鈕部署到 Render
3. 設定環境變數（見下方）

#### 方法二：Heroku

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

#### 方法三：VPS / 雲伺服器

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

### 線上部署（Render/Heroku）

雲端無法使用 OAuth 彈窗授權，需要手動取得 Refresh Token：

```bash
# 1. 安裝依賴
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# 2. 執行以下 Python 腳本取得 Token
```

```python
# get_refresh_token.py
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

print("GOOGLE_CLIENT_ID:", creds.client_id)
print("GOOGLE_CLIENT_SECRET:", creds.client_secret)
print("GOOGLE_REFRESH_TOKEN:", creds.refresh_token)
```

3. 將取得的值設定為環境變數：

```bash
# Render/Heroku
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret  
GOOGLE_REFRESH_TOKEN=your_refresh_token
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
├── setup_drive.py         # 本地 Drive 設定助手
├── requirements.txt       # Python 依賴
├── runtime.txt            # Python 版本
├── Procfile               # Heroku 配置
├── render.yaml            # Render 配置
├── Dockerfile             # Docker 配置
├── .dockerignore          # Docker 忽略檔案
├── .gitignore             # Git 忽略檔案
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
| `/api/search` | POST | 搜尋判決書 |
| `/api/calendar` | GET | 取得日曆數據 |
| `/api/stats` | GET | 取得統計數據 |
| `/api/start` | POST | 開始下載 |
| `/api/stop` | POST | 停止下載 |
| `/api/status` | GET | 取得下載狀態 |
| `/api/export` | GET | 匯出所有數據 |

## 📝 技術棧

- **後端**: Python + Flask
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **爬蟲**: BeautifulSoup4 + Requests
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

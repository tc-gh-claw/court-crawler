# 自動下載設置指南

## 功能說明

系統已經實現以下功能：

1. ✅ **自動去重** - 已下載的判決書會記錄，不會重複下載
2. ✅ **批量下載** - 可以爬取所有年份的判決書
3. ✅ **自動上傳** - 自動上傳到 Google Drive 並按年月分類

## 已下載記錄

系統會將已下載的 URL 記錄在 `downloaded_records.json` 檔案中。

查看已下載記錄：
```
GET /api/downloaded
```

## 手動觸發全部下載

### 方法 1: 使用 API

```bash
# 爬取所有判決書（2020年至今）
curl -X POST https://court-crawler-am33.onrender.com/api/crawl-all

# 或者只爬取近期
curl -X POST https://court-crawler-am33.onrender.com/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"days_back": 30}'
```

### 方法 2: 使用網站界面

1. 開啟 https://court-crawler-am33.onrender.com
2. 撳「開始爬蟲」按鈕
3. 選擇「爬取所有年份」或「爬取近期」
4. 系統會自動下載並上傳到 Google Drive

## 自動每周下載（Render Cron Job）

### 設置步驟

1. 登入 Render Dashboard: https://dashboard.render.com
2. 找到你的服務 `court-crawler`
3. 撳「Settings」→「Cron Jobs」
4. 撳「Add Cron Job」
5. 填寫以下資訊：
   - **Name**: `weekly-download`
   - **Schedule**: `0 0 * * 0` (每周日午夜)
   - **Command**: `python auto_download.py`
6. 撳「Save」

### 或者使用 GitHub Actions

如果你使用 GitHub Actions，可以在 `.github/workflows/weekly-download.yml` 中添加：

```yaml
name: Weekly Download

on:
  schedule:
    - cron: '0 0 * * 0'  # 每周日午夜
  workflow_dispatch:  # 手動觸發

jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Crawl All
        run: |
          curl -X POST https://court-crawler-am33.onrender.com/api/crawl-all
```

## 檔案結構

下載的檔案會按以下結構儲存：

```
本地（Render 磁碟）:
downloads/
├── 2024-03/
│   └── 判決書1.pdf
├── 2024-11/
│   └── 判決書2.pdf
└── ...

Google Drive:
澳門法院判決書/
├── 2024-03月/
│   └── 判決書1.pdf
├── 2024-11月/
│   └── 判決書2.pdf
└── ...
```

## 注意事項

1. **Render Free Plan** 磁碟是暫存的，重啟後會清空，但 Google Drive 上的檔案會保留
2. 已下載記錄 `downloaded_records.json` 會持久化儲存
3. 建議使用較長的下載延遲（5-10 秒），避免被法院網站封鎖
4. 首次運行可能需要較長時間（下載所有歷史判決書）

## 檢查下載狀態

```bash
# 查看當前狀態
curl https://court-crawler-am33.onrender.com/api/status

# 查看日誌
curl https://court-crawler-am33.onrender.com/api/logs

# 查看已下載記錄
curl https://court-crawler-am33.onrender.com/api/downloaded
```
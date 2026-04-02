# Google Drive API 設定指南

## 🚀 本地開發設定

### 方法一：用自動腳本（最簡單）

1. **先喺 Google Cloud Console 下載 credentials.json**
   - 去 https://console.cloud.google.com/
   - 建立專案 → 啟用 Drive API → 建立 OAuth 憑證（桌面應用程式）
   - 下載 JSON，改名做 `credentials.json`
   - 放喺 `court-crawler/` 資料夾

2. **執行設定腳本**
   ```bash
   cd court-crawler
   python setup_drive.py
   ```

3. **跟住畫面指示做**
   - 會彈出瀏覽器要你登入 Google
   - 允許權限
   - 完成後會自動建立「澳門法院判決書」資料夾

---

## ☁️ 雲端部署設定（Render/Heroku）

雲端無法使用 OAuth 彈窗授權，需要用 **Refresh Token** 方式：

### Step 1: 準備 credentials.json

同本地開發一樣，先去 Google Cloud Console 下載 `credentials.json`

### Step 2: 取得 Refresh Token

```bash
# 執行這個腳本
python get_refresh_token.py
```

跟住會彈出瀏覽器叫你授權，完成後會顯示：

```
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REFRESH_TOKEN=xxx
```

### Step 3: 設定到 Render

1. 去 Render Dashboard → 你的 Service → Environment
2. 新增以下環境變數：
   - `GOOGLE_CLIENT_ID` = 上面取得的值
   - `GOOGLE_CLIENT_SECRET` = 上面取得的值
   - `GOOGLE_REFRESH_TOKEN` = 上面取得的值

### Step 4: 設定到 Heroku

```bash
heroku config:set GOOGLE_CLIENT_ID=xxx
heroku config:set GOOGLE_CLIENT_SECRET=xxx
heroku config:set GOOGLE_REFRESH_TOKEN=xxx
```

---

## 📸 詳細圖解步驟

### Step 1: 開啟 Google Cloud Console

開啟 https://console.cloud.google.com/

### Step 2: 建立專案

1. 頂部選單 → 「選取專案」
2. 按「新增專案」
3. 專案名稱：填 `court-crawler`
4. 按「建立」

### Step 3: 啟用 Google Drive API

1. 左邊漢堡選單 → 「API 和服務」→「程式庫」
2. 搜尋框打 `Google Drive API`
3. 按第一個結果
4. 按藍色「啟用」按鈕

### Step 4: 設定 OAuth 同意畫面

1. 左邊選單 → 「API 和服務」→「OAuth 同意畫面」
2. User Type 揀「外部」→「建立」
3. 填寫：
   - App 名稱：`Court Crawler`
   - 使用者支援電郵：（你嘅 Gmail）
   - 開發人員聯絡資訊：（你嘅 Gmail）
4. 按「儲存並繼續」
5. Scopes 頁面直接按「儲存並繼續」
6. Test users 頁面按「儲存並繼續」

### Step 5: 建立憑證

1. 左邊選單 → 「憑證」
2. 按「+ 建立憑證」→「OAuth 用戶端 ID」
3. 應用程式類型：揀「桌面應用程式」
4. 名稱：`Court Crawler Desktop`
5. 按「建立」
6. 彈出視窗會顯示：
   - 你的用戶端 ID
   - 你的用戶端密碼
7. **重要**：按「下載 JSON」
8. 將下載嘅檔案改名做 `credentials.json`

### Step 6: 放喺正確位置（本地）

```
court-crawler/
├── app.py
├── credentials.json    ← 放呢度
├── setup_drive.py
└── ...
```

---

## ✅ 驗證設定

### 本地開發：
```bash
python setup_drive.py
```

### 雲端部署：
```bash
python get_refresh_token.py
```

---

## 🔧 常見問題

### Q: 彈出「此應用程式未通過驗證」
A: 正常！因為係你個人開發嘅 App。按「進階」→「前往 Court Crawler（不安全）」→「繼續」

### Q: token.json 係咩？
A: 第一次認證後會自動生成，儲存你嘅登入狀態，下次唔使再登入。

### Q: 可以分享畀其他人用嗎？
A: 唔好分享 credentials.json！入面有你嘅私鑰。每人應該用佢自己嘅憑證。

### Q: 上傳去邊個 Google Drive？
A: 你用邊個 Google 帳號登入，就會上傳去邊個 Drive。

### Q: Refresh Token 會過期嗎？
A: 一般情況下 Refresh Token 唔會過期，除非：
- 你撤銷咗應用程式權限
- 超過 6 個月冇使用
- 帳號密碼改咗

---

## 🆘 仲係搞唔掂？

1. **我可以幫你遠端控制電腦**（如果部機係你嘅）
2. **或者你截圖俾我睇** 你卡喺邊步
3. **又或者我整個短片** 演示整個流程

你想點搞？

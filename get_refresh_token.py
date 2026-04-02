#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
取得 Google Drive Refresh Token
用於雲端部署（Render/Heroku）

使用方法:
1. 先準備好 credentials.json（OAuth 桌面應用程式憑證）
2. 執行: python get_refresh_token.py
3. 按指示完成 OAuth 授權
4. 將輸出的環境變數設定到 Render/Heroku
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    print("=" * 60)
    print("🔑 Google Drive Refresh Token 取得工具")
    print("=" * 60)
    print()
    print("這個工具會幫你取得 Refresh Token，用於雲端部署。")
    print()
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        
        print("即將開啟瀏覽器進行授權...")
        print("(如果沒有自動開啟，請手動複製連結到瀏覽器)")
        print()
        
        creds = flow.run_local_server(port=0)
        
        print()
        print("=" * 60)
        print("✅ 授權成功！")
        print("=" * 60)
        print()
        print("請將以下環境變數設定到 Render/Heroku：")
        print()
        print(f"GOOGLE_CLIENT_ID={creds.client_id}")
        print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
        print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
        print()
        print("=" * 60)
        print()
        print("設定方法：")
        print()
        print("【Render】")
        print("1. 去 Dashboard → 你的 Service → Environment")
        print("2. 點「Add Environment Variable」")
        print("3. 分別加入以上 3 個變數")
        print()
        print("【Heroku】")
        print("heroku config:set GOOGLE_CLIENT_ID=xxx")
        print("heroku config:set GOOGLE_CLIENT_SECRET=xxx")
        print("heroku config:set GOOGLE_REFRESH_TOKEN=xxx")
        print()
        
    except FileNotFoundError:
        print("❌ 找不到 credentials.json")
        print()
        print("請先：")
        print("1. 去 https://console.cloud.google.com/")
        print("2. 建立 OAuth 憑證（桌面應用程式）")
        print("3. 下載 credentials.json 放到這個資料夾")
        print()
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == '__main__':
    main()

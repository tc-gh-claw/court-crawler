#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Drive API 設定助手
自動引導你完成 OAuth 認證
"""

import os
import json
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

def check_credentials():
    """檢查 credentials.json 是否存在"""
    creds_path = Path("credentials.json")
    
    if creds_path.exists():
        print("✅ 找到 credentials.json")
        return True
    else:
        print("❌ 找不到 credentials.json")
        print("\n📋 請先完成以下步驟：")
        print("=" * 60)
        print("""
1. 去 https://console.cloud.google.com/
2. 建立新專案（或選擇現有專案）
3. 啟用 Google Drive API：
   - 左邊選單 → API 和服務 → 程式庫
   - 搜尋 "Google Drive API" → 啟用

4. 建立 OAuth 憑證：
   - 左邊選單 → API 和服務 → 憑證
   - 按「+ 建立憑證」→ OAuth 用戶端 ID
   - 應用程式類型：選「桌面應用程式」
   - 名稱：Court Crawler
   - 按「建立」→「下載 JSON」

5. 將下載的檔案改名為 credentials.json
   並放在呢個資料夾：{}
""".format(Path.cwd()))
        print("=" * 60)
        return False

def authenticate():
    """進行 OAuth 認證"""
    creds = None
    token_path = Path("token.json")
    
    # 檢查現有 token
    if token_path.exists():
        print("\n🔄 發現現有 token，嘗試刷新...")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # 如果冇效，重新認證
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 正在刷新 token...")
            creds.refresh(Request())
        else:
            print("\n🔐 需要授權，正在開啟瀏覽器...")
            print("（如果冇自動開啟，請手動複製連結到瀏覽器）\n")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 儲存 token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print("✅ Token 已儲存到 token.json")
    
    return creds

def test_drive_access(creds):
    """測試 Drive 存取權限"""
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # 測試：列出檔案
        results = service.files().list(
            pageSize=10, 
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        
        print("\n✅ Google Drive 連接成功！")
        print(f"\n📁 你的 Drive 中有 {len(files)} 個檔案（顯示前10個）：")
        print("-" * 60)
        
        if not files:
            print("（暫時冇檔案）")
        else:
            for file in files:
                print(f"  📄 {file['name']}")
        
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 連接失敗: {e}")
        return False

def create_crawler_folder(creds):
    """建立爬蟲專用資料夾"""
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # 檢查是否已有同名資料夾
        results = service.files().list(
            q="name='澳門法院判決書' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        existing = results.get('files', [])
        
        if existing:
            print(f"\n📁 已存在 '澳門法院判決書' 資料夾")
            return existing[0]['id']
        
        # 建立新資料夾
        folder_metadata = {
            'name': '澳門法院判決書',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder['id']
        print(f"\n✅ 已建立 '澳門法院判決書' 資料夾")
        
        # 設定權限（可選：分享給自己）
        print("\n設定資料夾權限...")
        
        return folder_id
        
    except Exception as e:
        print(f"\n❌ 建立資料夾失敗: {e}")
        return None

def main():
    print("=" * 60)
    print("🚀 Google Drive API 設定助手")
    print("=" * 60)
    
    # 檢查 credentials
    if not check_credentials():
        input("\n按 Enter 鍵結束...")
        return
    
    # 認證
    try:
        creds = authenticate()
    except Exception as e:
        print(f"\n❌ 認證失敗: {e}")
        input("\n按 Enter 鍵結束...")
        return
    
    # 測試連接
    if test_drive_access(creds):
        # 建立資料夾
        folder_id = create_crawler_folder(creds)
        
        if folder_id:
            print("\n" + "=" * 60)
            print("🎉 設定完成！")
            print("=" * 60)
            print(f"\n資料夾 ID: {folder_id}")
            print("\n你而家可以：")
            print("1. 執行 python app.py 啟動爬蟲網站")
            print("2. 喺網站入面啟用『上傳到 Google Drive』功能")
            print("\n下次使用時會自動用 token.json，唔使再認證！")
    else:
        print("\n⚠️ 請檢查 credentials.json 是否正確")
    
    input("\n按 Enter 鍵結束...")

if __name__ == '__main__':
    main()

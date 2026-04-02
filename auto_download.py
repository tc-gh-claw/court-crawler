#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動化每周下載腳本
可以在 Render Cron Job 中運行
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import crawl_all_judgments, process_downloads, save_cache, log

def auto_download():
    """自動下載所有新判決書"""
    print(f"[{datetime.now()}] 開始自動下載...")
    
    # 爬取所有判決書
    pdfs = crawl_all_judgments()
    
    if not pdfs:
        print("沒有新判決書需要下載")
        return
    
    print(f"找到 {len(pdfs)} 個新判決書")
    
    # 自動下載並上傳到 Google Drive
    process_downloads(pdfs, upload_to_gdrive=True)
    
    print(f"[{datetime.now()}] 自動下載完成")

if __name__ == '__main__':
    auto_download()

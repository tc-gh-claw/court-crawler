#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳門法院判決書爬蟲 - 進階網頁版
支援日曆視圖、日期分類、部署就緒
"""

import os
import re
import time
import json
import base64
import threading
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
from collections import defaultdict

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, jsonify, request, send_file
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dateutil import parser as date_parser

# ============ 設定 ============
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
SCOPES = ['https://www.googleapis.com/auth/drive']
BASE_URL = "https://www.court.gov.mo"
SENTENCE_URL = f"{BASE_URL}/sentence/"

# 快取設定
CACHE_FILE = Path("judgments_cache.json")
cache_data = {"pdfs": [], "last_update": None}

app = Flask(__name__)

# 儲存下載狀態
download_status = {
    "running": False,
    "total": 0,
    "current": 0,
    "message": "",
    "logs": []
}

# 已下載記錄（避免重複）
DOWNLOADED_RECORDS_FILE = Path("downloaded_records.json")
downloaded_records = set()

def load_downloaded_records():
    """載入已下載記錄"""
    global downloaded_records
    if DOWNLOADED_RECORDS_FILE.exists():
        try:
            with open(DOWNLOADED_RECORDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                downloaded_records = set(data.get('urls', []))
                log(f"已載入 {len(downloaded_records)} 個已下載記錄")
        except:
            downloaded_records = set()

def save_downloaded_records():
    """儲存已下載記錄"""
    with open(DOWNLOADED_RECORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'urls': list(downloaded_records)}, f, ensure_ascii=False, indent=2)

def is_downloaded(url):
    """檢查是否已下載"""
    return url in downloaded_records

def mark_downloaded(url):
    """標記為已下載"""
    downloaded_records.add(url)
    save_downloaded_records()

# 初始化
load_downloaded_records()

def log(message):
    """記錄日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    download_status["logs"].append(log_entry)
    print(log_entry)

def load_cache():
    """載入快取"""
    global cache_data
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except:
            pass

def save_cache():
    """儲存快取"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

def extract_date_from_text(text):
    """
    從文字中提取日期
    支援多種格式：2024/01/15, 2024年1月15日, 15/01/2024 等
    """
    if not text:
        return None
    
    # 常見日期格式
    patterns = [
        # 2024/01/15 或 2024-01-15
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        # 2024年1月15日
        r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日',
        # 15/01/2024 或 15-01-2024
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        # 案件編號中的日期，如 2024/001
        r'案件.*?[^\d](\d{4})[^\d]',
        # 案號中的年份
        r'案[件號].*?(\d{4})',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                # 判斷是 YMD 還是 DMY
                first = int(match[0])
                if first > 1900:  # YMD
                    year, month, day = first, int(match[1]), int(match[2])
                else:  # DMY
                    day, month, year = first, int(match[1]), int(match[2])
            else:
                year = int(match)
                month = day = 1
            
            # 驗證日期合理性
            if 1999 <= year <= datetime.now().year and 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    return datetime(year, month, day).strftime('%Y-%m-%d')
                except:
                    continue
    
    # 嘗試搵只有年份
    year_match = re.search(r'(19|20)\d{2}', text)
    if year_match:
        year = int(year_match.group(0))
        if 1999 <= year <= datetime.now().year:
            return f"{year}-01-01"
    
    return None

def get_drive_service():
    """取得 Google Drive API 服務
    支援本地開發（credentials.json + OAuth 流程）
    及雲端部署（環境變數 + Refresh Token）
    """
    creds = None
    
    # 方法 1: 雲端部署 - 使用環境變數
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN')
    
    if client_id and client_secret and refresh_token:
        try:
            creds = Credentials(
                None,  # token 會自動用 refresh_token 取得
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )
            creds.refresh(Request())
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            log(f"使用環境變數連接 Drive 失敗: {e}")
            return None
    
    # 方法 2: 本地開發 - 使用 credentials.json
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def create_drive_folder(service, name, parent_id=None):
    """喺 Google Drive 建立資料夾"""
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    try:
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder['id']
    except Exception as e:
        log(f"建立資料夾失敗: {e}")
        return None

def upload_to_drive(service, file_path, folder_id=None):
    """上傳檔案到 Google Drive"""
    file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    return file['id']

def crawl_all_judgments():
    """
    爬取所有判決書 - 使用改進的核心爬蟲
    支援多法院、多年份、多分頁
    """
    from crawler_core import CourtCrawler, COURT_MAP
    
    pdf_list = []
    
    try:
        log("開始爬取所有判決書 (改進版)...")
        
        # 使用新的核心爬蟲
        crawler = CourtCrawler()
        
        # 搜尋多個年份（2020-今年）
        current_year = datetime.now().year
        years = list(range(2020, current_year + 1))
        
        # 搜尋所有法院
        courts = ['tui', 'tsi', 'tjb', 'ta']  # 終審、中級、初級、行政
        
        for year in years:
            for court_code in courts:
                court_name = COURT_MAP.get(court_code, (court_code, court_code))[1]
                log(f"搜尋 {year} 年 {court_name}...")
                
                try:
                    # 爬取該年份和法院的所有判決書
                    pdfs = crawler.crawl_year_court(year, court_code, delay=1)
                    
                    # 過濾已下載的
                    new_pdfs = [p for p in pdfs if not is_downloaded(p['url'])]
                    
                    pdf_list.extend(new_pdfs)
                    log(f"  {year}年 {court_name}: 找到 {len(pdfs)} 個，新增 {len(new_pdfs)} 個")
                    
                except Exception as e:
                    log(f"  錯誤: {e}")
                    continue
        
        log(f"總共找到 {len(pdf_list)} 個新判決書")
        
    except Exception as e:
        log(f"爬取失敗: {e}")
        import traceback
        log(traceback.format_exc())
    
    return pdf_list

def search_judgments(court=None, year_from=None, year_to=None, keyword=None):
    """搜尋判決書（從快取）"""
    load_cache()
    results = cache_data.get('pdfs', [])
    
    # 過濾
    if court:
        results = [p for p in results if p.get('court') == court]
    if year_from:
        results = [p for p in results if p.get('year', '0000') >= year_from]
    if year_to:
        results = [p for p in results if p.get('year', '9999') <= year_to]
    if keyword:
        keyword = keyword.lower()
        results = [p for p in results if keyword in p.get('title', '').lower() 
                   or keyword in p.get('filename', '').lower()]
    
    return results

def get_calendar_data(year=None, month=None):
    """
    取得日曆格式的數據
    返回某年某月的判決書分佈
    """
    load_cache()
    pdfs = cache_data.get('pdfs', [])
    
    if not year:
        year = datetime.now().year
    
    # 按日期分組
    date_groups = defaultdict(list)
    
    for pdf in pdfs:
        date = pdf.get('date', '')
        if date and date.startswith(str(year)):
            date_groups[date].append(pdf)
    
    # 按月份分組
    if month:
        month_key = f"{year}-{month:02d}"
        date_groups = {k: v for k, v in date_groups.items() if k.startswith(month_key)}
    
    return dict(date_groups)

def get_stats():
    """取得統計數據"""
    load_cache()
    pdfs = cache_data.get('pdfs', [])
    
    stats = {
        'total': len(pdfs),
        'by_year': defaultdict(int),
        'by_month': defaultdict(int),
        'by_court': defaultdict(int),
        'recent_7_days': 0,
        'recent_30_days': 0
    }
    
    now = datetime.now()
    
    for pdf in pdfs:
        # 年份統計
        year = pdf.get('year', 'unknown')
        stats['by_year'][year] += 1
        
        # 月份統計
        date = pdf.get('date', '')
        if date and len(date) >= 7:
            stats['by_month'][date[:7]] += 1
        
        # 法院統計
        court = pdf.get('court', 'unknown')
        stats['by_court'][court] += 1
        
        # 最近日期統計
        if date:
            try:
                pdf_date = datetime.strptime(date, '%Y-%m-%d')
                days_diff = (now - pdf_date).days
                if days_diff <= 7:
                    stats['recent_7_days'] += 1
                if days_diff <= 30:
                    stats['recent_30_days'] += 1
            except:
                pass
    
    # 轉換為普通 dict
    stats['by_year'] = dict(stats['by_year'])
    stats['by_month'] = dict(stats['by_month'])
    stats['by_court'] = dict(stats['by_court'])
    
    return stats

def download_pdf(url, save_path, delay=3):
    """下載單個 PDF"""
    try:
        log(f"下載: {url}")
        resp = requests.get(url, timeout=60, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if resp.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            log(f"✓ 已儲存: {save_path}")
            
            if delay > 0:
                time.sleep(delay)
            return True
        else:
            log(f"✗ 下載失敗 (HTTP {resp.status_code}): {url}")
            return False
            
    except Exception as e:
        log(f"✗ 下載錯誤: {e}")
        return False

def process_downloads(pdf_list, upload_to_gdrive=True, base_folder_name="澳門法院判決書"):
    """處理下載同上傳"""
    global download_status
    
    download_status["running"] = True
    download_status["total"] = len(pdf_list)
    download_status["current"] = 0
    download_status["message"] = "開始處理..."
    
    # 初始化 Google Drive
    drive_service = None
    base_folder_id = None
    date_folders = {}
    
    if upload_to_gdrive:
        log("連接 Google Drive...")
        drive_service = get_drive_service()
        if drive_service:
            base_folder_id = create_drive_folder(drive_service, base_folder_name)
            log(f"Google Drive 資料夾已建立: {base_folder_id}")
        else:
            log("警告: 無法連接 Google Drive")
    
    # 按日期分組
    date_groups = defaultdict(list)
    for pdf in pdf_list:
        date = pdf.get('date', 'unknown')
        if date and date != 'unknown':
            # 使用年月作為資料夾名稱，例如 "2024-01"
            folder_key = date[:7] if len(date) >= 7 else date
        else:
            folder_key = 'unknown'
        date_groups[folder_key].append(pdf)
    
    log(f"按日期分組: {list(date_groups.keys())}")
    
    # 建立日期資料夾
    if drive_service and base_folder_id:
        for date_key in date_groups.keys():
            folder_name = f"{date_key}月" if date_key != 'unknown' else '未知日期'
            folder_id = create_drive_folder(drive_service, folder_name, base_folder_id)
            date_folders[date_key] = folder_id
            log(f"建立 {folder_name} 資料夾")
    
    # 下載同上傳
    success_count = 0
    skipped_count = 0
    for date_key, pdfs in date_groups.items():
        log(f"處理 {date_key} 的 {len(pdfs)} 個檔案...")
        
        # 建立日期本機資料夾
        date_dir = DOWNLOAD_DIR / date_key
        date_dir.mkdir(exist_ok=True)
        
        for pdf in pdfs:
            if not download_status["running"]:
                log("下載已停止")
                break
            
            download_status["current"] += 1
            
            # 檢查是否已下載
            if is_downloaded(pdf['url']):
                log(f"跳過（已下載）: {pdf['filename']}")
                skipped_count += 1
                continue
            
            download_status["message"] = f"下載 {pdf['filename']}..."
            
            # 下載
            save_path = date_dir / pdf['filename']
            if download_pdf(pdf['url'], save_path):
                success_count += 1
                mark_downloaded(pdf['url'])  # 標記為已下載
                
                # 上傳到 Google Drive
                if drive_service and date_key in date_folders:
                    try:
                        upload_to_drive(drive_service, str(save_path), date_folders[date_key])
                        log(f"✓ 已上傳: {pdf['filename']}")
                    except Exception as e:
                        log(f"✗ 上傳失敗: {e}")
            
            download_status["message"] = f"完成 {download_status['current']}/{download_status['total']}"
    
    download_status["running"] = False
    download_status["message"] = f"完成！成功 {success_count} 個，跳過 {skipped_count} 個"
    log(f"全部完成！成功下載 {success_count} 個，跳過 {skipped_count} 個已存在檔案")

# ============ Flask 路由 ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    """手動觸發爬蟲"""
    data = request.json or {}
    days_back = data.get('days_back', 30)
    crawl_all = data.get('crawl_all', False)  # 新增：是否爬取所有
    
    # 在背景執行爬蟲
    def do_crawl():
        if crawl_all:
            pdfs = crawl_all_judgments()  # 爬取所有
        else:
            pdfs = crawl_judgments(days_back)  # 爬取近期
        cache_data['pdfs'] = pdfs
        cache_data['last_update'] = datetime.now().isoformat()
        save_cache()
        log(f"爬蟲完成，找到 {len(pdfs)} 個判決書")
    
    thread = threading.Thread(target=do_crawl)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'crawling_started'})

@app.route('/api/crawl-all', methods=['POST'])
def api_crawl_all():
    """爬取所有判決書（多年份）"""
    
    def do_crawl_all():
        pdfs = crawl_all_judgments()
        cache_data['pdfs'] = pdfs
        cache_data['last_update'] = datetime.now().isoformat()
        save_cache()
        log(f"全部爬蟲完成，找到 {len(pdfs)} 個判決書")
        
        # 自動開始下載
        if pdfs:
            log("自動開始下載...")
            process_downloads(pdfs, upload_to_gdrive=True)
    
    thread = threading.Thread(target=do_crawl_all)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'crawl_all_started'})

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.json or {}
    court = data.get('court', '')
    year_from = data.get('year_from', '')
    year_to = data.get('year_to', '')
    keyword = data.get('keyword', '')
    
    results = search_judgments(court, year_from, year_to, keyword)
    return jsonify({
        'count': len(results),
        'pdfs': results
    })

@app.route('/api/calendar')
def api_calendar():
    """取得日曆數據"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    calendar_data = get_calendar_data(year, month)
    return jsonify(calendar_data)

@app.route('/api/stats')
def api_stats():
    """取得統計數據"""
    stats = get_stats()
    return jsonify(stats)

@app.route('/api/start', methods=['POST'])
def api_start():
    global download_status
    
    if download_status["running"]:
        return jsonify({'error': '下載進行中'}), 400
    
    data = request.json
    pdf_list = data.get('pdfs', [])
    upload_to_gdrive = data.get('upload_to_gdrive', True)
    delay = data.get('delay', 3)
    
    if not pdf_list:
        return jsonify({'error': '沒有 PDF 列表'}), 400
    
    download_status = {
        "running": True,
        "total": len(pdf_list),
        "current": 0,
        "message": "準備開始...",
        "logs": []
    }
    
    thread = threading.Thread(
        target=process_downloads,
        args=(pdf_list, upload_to_gdrive)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    download_status["running"] = False
    return jsonify({'status': 'stopped'})

@app.route('/api/status')
def api_status():
    return jsonify(download_status)

@app.route('/api/logs')
def api_logs():
    return jsonify({'logs': download_status['logs']})

@app.route('/api/downloaded')
def api_downloaded():
    """獲取已下載記錄"""
    return jsonify({
        'count': len(downloaded_records),
        'urls': list(downloaded_records)
    })

@app.route('/api/export')
def api_export():
    """匯出所有數據為 JSON"""
    load_cache()
    return jsonify(cache_data)

# 初始化
load_cache()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

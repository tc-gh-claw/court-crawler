#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳門法院判決書爬蟲 - 核心改進版
修復問題：
1. 每頁多個 case_list，每個是一個判決書
2. 支援多語言版本（優先中文）
3. 正確處理分頁
4. 完整的法院分類
"""

import os
import re
import time
import json
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.court.gov.mo"
COURT_MAP = {
    'tui': ('final', '終審法院'),
    'tsi': ('intermediate', '中級法院'),
    'tjb': ('primary', '初級法院'),
    'ta': ('admin', '行政法院'),
    'all': (None, '所有法院')
}

class CourtCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9',
        })
        self.csrf_token = None
    
    def get_csrf_token(self):
        """獲取 CSRF Token"""
        search_page = self.session.get(f"{BASE_URL}/zh/subpage/researchjudgments", timeout=30)
        soup = BeautifulSoup(search_page.text, 'html.parser')
        token_input = soup.find('input', {'name': 'wizcasesearch_sentence_filter_type[_token]'})
        self.csrf_token = token_input['value'] if token_input else ''
        return self.csrf_token
    
    def search_judgments(self, court='all', date_from=None, date_to=None, page=1):
        """
        搜尋判決書
        
        Args:
            court: 法院代碼 ('tui', 'tsi', 'tjb', 'ta', 'all')
            date_from: 開始日期 (YYYY-MM-DD)
            date_to: 結束日期 (YYYY-MM-DD)
            page: 頁碼
        """
        if not self.csrf_token:
            self.get_csrf_token()
        
        if not date_from:
            date_from = f"{datetime.now().year}-01-01"
        if not date_to:
            date_to = f"{datetime.now().year}-12-31"
        
        search_params = {
            'wizcasesearch_sentence_filter_type[court]': court,
            'wizcasesearch_sentence_filter_type[decisionDate][left_date]': date_from,
            'wizcasesearch_sentence_filter_type[decisionDate][right_date]': date_to,
            'wizcasesearch_sentence_filter_type[procNo]': '',
            'wizcasesearch_sentence_filter_type[subject]': '',
            'wizcasesearch_sentence_filter_type[sumary]': '',
            'wizcasesearch_sentence_filter_type[recContent][logic]': 'AND',
            'wizcasesearch_sentence_filter_type[recContent][key][]': '',
            'wizcasesearch_sentence_filter_type[_token]': self.csrf_token,
            'page': str(page)
        }
        
        resp = self.session.post(
            f"{BASE_URL}/zh/subpage/researchjudgments",
            data=search_params,
            timeout=30
        )
        
        return resp.text
    
    def parse_judgments(self, html, court_code='all'):
        """
        解析判決書列表
        
        網站結構：
        - 每個判決書在一個 <div class="case_list"> 中
        - 每個 case_list 包含多個 <li>，其中一個有 PDF 連結
        - 可能有中文(zh-)和葡萄牙文(pt-)兩個版本
        """
        soup = BeautifulSoup(html, 'html.parser')
        pdfs = []
        seen_urls = set()
        
        # 遍歷所有 case_list（每個是一個判決書）
        case_lists = soup.find_all('div', {'class': 'case_list'})
        
        for case_list in case_lists:
            items = case_list.find_all('li')
            
            # 找到第一個有 PDF 的項目（跳過表頭）
            for item in items:
                if 'seperate' in item.get('class', []):
                    continue
                
                # 提取日期
                date_span = item.find('span', {'class': 'date'})
                date_str = date_span.text.strip() if date_span else None
                
                # 解析日期 (DD/MM/YYYY -> YYYY-MM-DD)
                date = None
                if date_str:
                    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_str)
                    if match:
                        day, month, year = match.groups()
                        date = f"{year}-{month}-{day}"
                
                # 提取案件編號
                num_span = item.find('span', {'class': 'num'})
                case_num = num_span.text.strip() if num_span else ''
                
                # 提取類別
                type_span = item.find('span', {'class': 'type'})
                case_type = type_span.text.strip() if type_span else ''
                
                # 提取 PDF 連結
                pdf_links = item.find_all('a', href=re.compile(r'/sentence/.*\.pdf', re.I))
                
                zh_pdf = None
                pt_pdf = None
                
                for link in pdf_links:
                    href = link.get('href', '')
                    if '/sentence/zh-' in href:
                        zh_pdf = href
                    elif '/sentence/pt-' in href:
                        pt_pdf = href
                
                # 優先使用中文版本
                pdf_path = zh_pdf if zh_pdf else pt_pdf
                
                if pdf_path:
                    # 去重（基於案件編號和日期）
                    unique_key = f"{date}_{case_num}"
                    if unique_key in seen_urls:
                        continue
                    seen_urls.add(unique_key)
                    
                    # 判斷法院（從 URL 或搜尋參數）
                    court_id = 'unknown'
                    court_name = '未知法院'
                    
                    # 從 URL 判斷
                    if 'tui' in pdf_path.lower():
                        court_id, court_name = COURT_MAP['tui']
                    elif 'tsi' in pdf_path.lower():
                        court_id, court_name = COURT_MAP['tsi']
                    elif 'tjb' in pdf_path.lower():
                        court_id, court_name = COURT_MAP['tjb']
                    elif 'ta' in pdf_path.lower():
                        court_id, court_name = COURT_MAP['ta']
                    else:
                        # 從搜尋參數判斷
                        if court_code in COURT_MAP:
                            court_id, court_name = COURT_MAP[court_code]
                    
                    # 生成文件名
                    if date and case_num:
                        filename = f"{date}_{case_num.replace('/', '-')}.pdf"
                    else:
                        filename = pdf_path.split('/')[-1]
                    
                    pdf_info = {
                        'url': urljoin(BASE_URL, pdf_path),
                        'filename': filename,
                        'title': f"{case_num} {case_type}".strip(),
                        'date': date or 'unknown',
                        'year': date[:4] if date else 'unknown',
                        'month': date[5:7] if date and len(date) >= 7 else '01',
                        'case_number': case_num,
                        'case_type': case_type,
                        'court': court_id,
                        'court_name': court_name,
                        'has_zh': zh_pdf is not None,
                        'has_pt': pt_pdf is not None,
                    }
                    pdfs.append(pdf_info)
                    break  # 這個 case_list 處理完成
        
        return pdfs
    
    def get_total_pages(self, html):
        """獲取總頁數"""
        soup = BeautifulSoup(html, 'html.parser')
        pagination_links = soup.find_all('a', href=re.compile(r'page=(\d+)', re.I))
        
        page_numbers = set()
        for link in pagination_links:
            match = re.search(r'page=(\d+)', link.get('href', ''))
            if match:
                page_numbers.add(int(match.group(1)))
        
        return max(page_numbers) if page_numbers else 1
    
    def crawl_year_court(self, year, court, delay=1):
        """
        爬取特定年份和法院的所有判決書
        
        Args:
            year: 年份
            court: 法院代碼
            delay: 請求間隔（秒）
        
        Returns:
            list: 判決書列表
        """
        all_pdfs = []
        seen_keys = set()
        
        try:
            # 第一頁
            html = self.search_judgments(
                court=court,
                date_from=f"{year}-01-01",
                date_to=f"{year}-12-31",
                page=1
            )
            
            pdfs = self.parse_judgments(html, court)
            total_pages = self.get_total_pages(html)
            
            court_name = COURT_MAP.get(court, (court, court))[1]
            print(f"  {year}年 {court_name}: 第1頁/{total_pages}頁, 找到{len(pdfs)}個")
            
            for pdf in pdfs:
                key = f"{pdf['date']}_{pdf['case_number']}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_pdfs.append(pdf)
            
            # 其他頁
            for page in range(2, total_pages + 1):
                time.sleep(delay)
                
                html = self.search_judgments(
                    court=court,
                    date_from=f"{year}-01-01",
                    date_to=f"{year}-12-31",
                    page=page
                )
                
                pdfs = self.parse_judgments(html, court)
                print(f"  {year}年 {court_name}: 第{page}頁/{total_pages}頁, 找到{len(pdfs)}個")
                
                for pdf in pdfs:
                    key = f"{pdf['date']}_{pdf['case_number']}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_pdfs.append(pdf)
        
        except Exception as e:
            print(f"  錯誤: {e}")
        
        return all_pdfs
    
    def crawl_all(self, years=None, courts=None, delay=1):
        """
        爬取所有判決書
        
        Args:
            years: 年份列表（默認 2020-今年）
            courts: 法院代碼列表（默認全部）
            delay: 請求間隔（秒）
        
        Returns:
            list: 所有判決書列表
        """
        if not years:
            current_year = datetime.now().year
            years = list(range(2020, current_year + 1))
        
        if not courts:
            courts = ['tui', 'tsi', 'tjb', 'ta']
        
        all_pdfs = []
        seen_keys = set()
        
        for year in years:
            for court in courts:
                pdfs = self.crawl_year_court(year, court, delay)
                
                for pdf in pdfs:
                    key = f"{pdf['date']}_{pdf['case_number']}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_pdfs.append(pdf)
                
                time.sleep(delay)
        
        return all_pdfs


def test_crawler():
    """測試爬蟲"""
    print("=== 測試改進版法院爬蟲 ===\n")
    
    crawler = CourtCrawler()
    
    # 測試 1: 搜尋終審法院 2025 年
    print("--- 測試 1: 終審法院 2025 年 ---")
    html = crawler.search_judgments(court='tui', date_from='2025-01-01', date_to='2025-12-31', page=1)
    pdfs = crawler.parse_judgments(html, 'tui')
    total_pages = crawler.get_total_pages(html)
    
    print(f"第 1 頁找到 {len(pdfs)} 個判決書")
    print(f"總頁數: {total_pages}")
    
    for pdf in pdfs[:5]:
        print(f"  {pdf['date']} | {pdf['case_number']:12s} | {pdf['court_name']:8s} | {pdf['case_type'][:20]}")
    
    # 測試 2: 多頁爬取
    print("\n--- 測試 2: 多頁爬取 ---")
    all_pdfs = crawler.crawl_year_court(2025, 'tui', delay=0.5)
    print(f"總計: {len(all_pdfs)} 個判決書")
    
    # 測試 3: 多法院爬取
    print("\n--- 測試 3: 2025年 所有法院 ---")
    crawler2 = CourtCrawler()
    all_results = crawler2.crawl_all(years=[2025], courts=['tui', 'tsi'], delay=0.5)
    print(f"總計: {len(all_results)} 個判決書")
    
    # 按法院統計
    from collections import Counter
    court_counts = Counter(p['court_name'] for p in all_results)
    print("\n按法院分布:")
    for court, count in court_counts.items():
        print(f"  {court}: {count}")
    
    return all_results


if __name__ == '__main__':
    results = test_crawler()
    
    # 保存結果
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n結果已保存到 test_results.json")

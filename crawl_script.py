#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, '.')

from crawler_core import CourtCrawler
from datetime import datetime
import json
from collections import Counter

years_input = os.environ.get('INPUT_YEARS', '2020-2025')
courts_input = os.environ.get('INPUT_COURTS', 'all')

if '-' in years_input:
    start, end = map(int, years_input.split('-'))
    years = list(range(start, end + 1))
else:
    years = [int(y) for y in years_input.split(',')]

court_map = {
    'tui': '終審法院',
    'tsi': '中級法院', 
    'tjb': '初級法院',
    'ta': '行政法院',
    'all': None
}

if courts_input == 'all':
    courts = ['tui', 'tsi', 'tjb', 'ta']
else:
    courts = [c.strip() for c in courts_input.split(',')]

print(f'爬取年份: {years}')
print(f'爬取法院: {[court_map.get(c, c) for c in courts]}')

crawler = CourtCrawler()
results = crawler.crawl_all(years=years, courts=courts, delay=1)

print(f'\n爬蟲完成！共找到 {len(results)} 個判決書')

with open('crawl_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

court_counts = Counter(r['court_name'] for r in results)
print('\n按法院分布:')
for court, count in court_counts.items():
    print(f'  {court}: {count}')

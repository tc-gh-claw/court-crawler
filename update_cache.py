#!/usr/bin/env python3
import json
from datetime import datetime

try:
    with open('crawl_results.json', 'r', encoding='utf-8') as f:
        new_results = json.load(f)
except:
    new_results = []

try:
    with open('judgments_cache.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)
except:
    cache = {'pdfs': [], 'last_update': None}

existing_urls = {p['url'] for p in cache['pdfs']}
for pdf in new_results:
    if pdf['url'] not in existing_urls:
        cache['pdfs'].append(pdf)
        existing_urls.add(pdf['url'])

cache['last_update'] = datetime.now().isoformat()

with open('judgments_cache.json', 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print(f'快取已更新：共 {len(cache["pdfs"])} 個判決書')

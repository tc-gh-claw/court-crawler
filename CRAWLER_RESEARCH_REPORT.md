# 澳門法院判決書爬蟲核心研究報告

## 研究日期
2026-04-03

## 研究目標
重新研究並改進澳門法院判決書爬蟲的核心程式，確保能正確抓取所有判決書。

---

## 發現的問題

### 1. 網站結構誤解（嚴重問題）
**原程式問題：**
- 舊版爬蟲假設所有判決書連結在同一個容器中
- 實際上每個判決書在一個獨立的 `<div class="case_list">` 中
- 每頁有 10 個 `case_list`，每個包含一個判決書

**網站實際結構：**
```html
<div class="case_list" id="zh-language-case">
  <li class="seperate">  <!-- 表頭 -->
  <li>  <!-- 判決書 1 -->
    <span class="date">19/12/2025</span>
    <span class="num">17/2023</span>
    <span class="type">對行政司法裁判的上訴</span>
    <span class="download">
      <a href="/sentence/zh-xxxxx.pdf">中文</a>
      <a href="/sentence/pt-xxxxx.pdf">葡文</a>
    </span>
  </li>
</div>
<div class="case_list" id="zh-language-case">  <!-- 判決書 2 -->
  ...
</div>
<!-- 共 10 個 case_list -->
```

### 2. 多語言版本處理不完整
**問題：**
- 每個判決書可能有中文(`zh-`)和葡萄牙文(`pt-`)兩個版本
- 舊版沒有區分語言版本
- 部分判決書只有單一語言版本

### 3. 分頁處理缺失
**問題：**
- 舊版只抓取第一頁
- 終審法院 2025 年有 9 頁結果
- 中級法院 2025 年有 85+ 頁結果

### 4. 法院分類不完整
**舊版分類：**
- 只識別 終審/中級/初級 三種法院
- 缺少「行政法院(ta)」

**實際法院代碼：**
| 代碼 | 中文名稱 | 英文標識 |
|------|----------|----------|
| tui | 終審法院 | final |
| tsi | 中級法院 | intermediate |
| tjb | 初級法院 | primary |
| ta | 行政法院 | admin |

### 5. 數據解析錯誤
**問題：**
- 日期格式為 `DD/MM/YYYY`，舊版沒有正確解析
- 沒有提取案件編號和類別
- 缺少去重邏輯

---

## 改進內容

### 1. 新增 `crawler_core.py` - 核心爬蟲模組

**主要功能：**
- ✅ 正確解析每頁多個 `case_list`
- ✅ 支援中文/葡萄牙文版本選擇（優先中文）
- ✅ 完整的分頁處理
- ✅ 支援所有四種法院
- ✅ 正確解析日期、案件編號、類別
- ✅ 完善的去重機制

**核心類：** `CourtCrawler`

```python
class CourtCrawler:
    def search_judgments(court, date_from, date_to, page)
    def parse_judgments(html, court_code)
    def get_total_pages(html)
    def crawl_year_court(year, court, delay)
    def crawl_all(years, courts, delay)
```

### 2. 更新 `app.py`

**改進：**
- 導入新的核心爬蟲
- 替換 `crawl_all_judgments()` 函數
- 保持其他功能（Google Drive、Flask API）不變

---

## 測試結果

### 測試範圍
- 年份：2025
- 法院：終審法院、中級法院

### 抓取結果
```
總共: 34 個判決書

按法院分布:
  中級法院: 24
  終審法院: 10

語言版本:
  有中文: 26
  有葡文: 11
  雙語: 3
```

### 樣本數據
```json
{
  "url": "https://www.court.gov.mo/sentence/zh-31e601dc71ea3ccd.pdf",
  "filename": "2025-12-12_122-2025.pdf",
  "title": "122/2025 民事訴訟程序上訴",
  "date": "2025-12-12",
  "year": "2025",
  "month": "12",
  "case_number": "122/2025",
  "case_type": "民事訴訟程序上訴",
  "court": "final",
  "court_name": "終審法院",
  "has_zh": true,
  "has_pt": false
}
```

---

## 使用方式

### 1. 直接使用核心爬蟲
```python
from crawler_core import CourtCrawler

crawler = CourtCrawler()

# 爬取特定年份和法院
pdfs = crawler.crawl_year_court(2025, 'tui')

# 爬取所有年份和法院
all_pdfs = crawler.crawl_all(
    years=[2020, 2021, 2022, 2023, 2024, 2025],
    courts=['tui', 'tsi', 'tjb', 'ta'],
    delay=1  # 請求間隔（秒）
)
```

### 2. 使用 Flask API
```bash
# 啟動服務
python app.py

# API 端點
POST /api/crawl-all    # 觸發完整爬蟲
GET  /api/stats        # 獲取統計數據
GET  /api/status       # 獲取下載狀態
```

---

## 注意事項

1. **請求頻率**
   - 每次請求間隔 1 秒，避免對服務器造成壓力
   - 可調整 `delay` 參數

2. **完整爬取時間估算**
   - 假設每法院每年有 10 頁，每頁 10 個判決書
   - 6 年 × 4 法院 × 10 頁 = 240 頁
   - 240 頁 × 1 秒 = 約 4 分鐘

3. **數據去重**
   - 使用 `日期_案件編號` 作為唯一鍵
   - 避免同一判決書被重複抓取

---

## 文件結構

```
court-crawler/
├── app.py              # Flask 主應用（已更新）
├── crawler_core.py     # 核心爬蟲模組（新增）
├── auto_download.py    # 自動下載腳本
├── templates/
│   └── index.html      # 前端頁面
└── test_results.json   # 測試結果
```

---

## 後續建議

1. **增加錯誤重試機制**
2. **添加進度持久化**（避免中斷後重新開始）
3. **支持增量更新**（只抓取新判決書）
4. **添加數據驗證**（檢查 PDF 文件完整性）
5. **優化並發處理**（使用線程池加速）

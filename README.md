# Google Maps 資料爬蟲專案

這個專案是為【路遊憩】所開發的 Google Maps 資料爬蟲工具，用於自動化收集餐廳和景點的相關資訊，包括基本資料、評論等。

## 功能特點

- 支援多進程並行爬取，提高效率
- 智能處理反爬蟲機制
- 自動保存進度，支援斷點續爬
- 完整的錯誤處理和日誌記錄
- 支援餐廳和景點兩種資料類型
- 資料以結構化 JSON 格式保存

## 專案結構

```
Project-Web-Crawler/
├── comment_scraper.py        # 單進程評論爬蟲
├── multi_element_scraper.py  # 單進程詳細資訊爬蟲
├── parallel_detail_scraper.py # 多進程詳細資訊爬蟲
├── parallel_review_scraper.py # 多進程評論爬蟲
└── README.md
```

## 前置需求

- Python 3.6+
- Chrome 瀏覽器
- ChromeDriver
- 必要的 Python 套件：
  - selenium
  - pandas
  - psutil
  - openpyxl

## 安裝步驟

1. 克隆專案：
```bash
git clone https://github.com/your-username/Project-Web-Crawler.git
cd Project-Web-Crawler
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

## 使用說明

### 資料準備
1. 準備一個 Excel 檔案（完整_台北_新北_地點清單.xlsx），包含所有要爬取的地點的 Place ID
2. Place ID 欄位名稱必須為 "Place ID"

### 爬取詳細資訊
```python
python parallel_detail_scraper.py
```

### 爬取評論
```python
python parallel_review_scraper.py
```

## 參數設定

在各腳本中可以調整的主要參數：
- `num_processes`：並行處理的進程數（預設：6）
- `is_restaurant`：資料類型（True 為餐廳，False 為景點）
- 延遲時間：`random_delay()` 函數中的最小和最大延遲時間

## 輸出格式

### 詳細資訊 JSON 格式
```json
{
    "店名": "地點名稱",
    "Place ID": "Google Maps Place ID",
    "評分": "4.5",
    "種類": "餐廳類型",
    "地址": "完整地址",
    "開始營業時間": {
        "星期一": "11:00~21:00",
        // ... 其他營業時間
    },
    "平均每人消費": "300~600元",
    "電話": "電話號碼",
    "簡介": "店家簡介",
    "設施": ["無線網路", "提供素食"],
    // ... 其他屬性
}
```

### 評論 JSON 格式
```json
{
    "評論 1": {
        "內容": "評論內容",
        "日期": "一個月前"
    },
    // ... 更多評論
}
```

## 注意事項

1. 為避免被 Google Maps 封鎖：
   - 使用隨機延遲
   - 模擬真實使用者行為
   - 使用無痕模式
   
2. 錯誤處理：
   - 程式會自動保存進度
   - 支援斷點續爬
   - 臨時檔案自動清理

3. 資源使用：
   - 注意控制並行進程數
   - 定期清理瀏覽器進程
   - 監控記憶體使用

## 錯誤排除

1. ChromeDriver 版本不符：
   - 確保 ChromeDriver 版本與 Chrome 瀏覽器版本相符
   
2. 資料未正確保存：
   - 檢查輸出資料夾權限
   - 確認進度檔案可寫入

3. 爬取速度過慢：
   - 適當調整進程數
   - 檢查網路連線
   - 調整延遲時間

## 授權

MIT License

## 貢獻指南

歡迎提交 Issue 和 Pull Request 來改善專案。
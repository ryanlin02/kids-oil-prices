import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pytz

def fetch_oil_prices():
    """
    從經濟部能源署網站爬取最新油價資訊
    """
    # 目標網址
    url = "https://www2.moeaea.gov.tw/oil111/Gasoline/RetailPrice"
    
    try:
        # 發送請求
        response = requests.get(url)
        response.encoding = 'utf-8'  # 確保正確編碼
        
        # 檢查請求是否成功
        if response.status_code != 200:
            print(f"請求失敗，狀態碼：{response.status_code}")
            return None
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到數據資料表
        table = soup.find('table', {'class': 'table-format'})
        
        if not table:
            print("找不到油價資料表格")
            return None
        
        # 初始化資料結構
        oil_data = {
            'cpc': {'92': '', '95': '', '98': '', 'diesel': ''},
            'fpg': {'92': '', '95': '', '98': '', 'diesel': ''},
            'update_time': ''
        }
        
        # 獲取最新的油價資料（表格中的第一行）
        rows = table.find_all('tr')
        
        # 找出更新日期
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 8:  # 確保行有足夠的單元格
                # 檢查是否是中油的資料
                if "台灣中油" in cells[1].text:
                    oil_data['cpc']['92'] = cells[3].text.strip()
                    oil_data['cpc']['95'] = cells[4].text.strip()
                    oil_data['cpc']['98'] = cells[5].text.strip()
                    oil_data['cpc']['diesel'] = cells[6].text.strip()
                    
                    # 如果還沒有更新時間，則從這行取得
                    if not oil_data['update_time']:
                        update_date = cells[0].text.strip()
                        oil_data['update_time'] = update_date
                        
                # 檢查是否是台塑的資料
                elif "台塑石化" in cells[1].text:
                    oil_data['fpg']['92'] = cells[3].text.strip()
                    oil_data['fpg']['95'] = cells[4].text.strip()
                    oil_data['fpg']['98'] = cells[5].text.strip()
                    oil_data['fpg']['diesel'] = cells[6].text.strip()
        
        # 添加爬蟲執行時間
        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
        oil_data['crawl_time'] = current_time
        
        return oil_data
    
    except Exception as e:
        print(f"爬取失敗：{e}")
        return None

def save_to_json(data, file_path):
    """
    將爬取到的資料儲存為 JSON 檔案
    """
    # 確保目錄存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 寫入 JSON 檔案
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"資料已儲存至 {file_path}")

if __name__ == "__main__":
    # 爬取油價資料
    oil_prices = fetch_oil_prices()
    
    if oil_prices:
        # 儲存至 JSON 檔案
        save_to_json(oil_prices, "data/oil_prices.json")
        print("油價資料更新成功！")
    else:
        print("無法取得油價資料")

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pytz
import sys
import re

def fetch_oil_prices():
    """
    從經濟部能源署網站爬取最新油價資訊
    """
    # 初始化資料結構，即使失敗也能返回基本結構
    oil_data = {
        'cpc': {'92': '暫無資料', '95': '暫無資料', '98': '暫無資料', 'diesel': '暫無資料'},
        'fpg': {'92': '暫無資料', '95': '暫無資料', '98': '暫無資料', 'diesel': '暫無資料'},
        'update_time': '暫無資料'
    }
    
    # 目標網址 - 使用經濟部能源署的汽柴油參考零售價頁面
    url = "https://www2.moeaea.gov.tw/oil111/oil/oil04.asp"
    
    try:
        # 發送請求
        print(f"正在請求網址: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'  # 確保正確編碼
        
        # 檢查請求是否成功
        if response.status_code != 200:
            print(f"請求失敗，狀態碼：{response.status_code}")
            return oil_data
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找所有表格
        tables = soup.find_all('table')
        
        # 輸出找到多少表格以進行調試
        print(f"找到 {len(tables)} 個表格")
        
        # 尋找包含油價資料的表格（通常是包含「台灣中油」和「台塑石化」的表格）
        for table_idx, table in enumerate(tables):
            print(f"檢查表格 #{table_idx + 1}")
            
            # 檢查表格是否包含中油和台塑的資料
            table_text = table.get_text()
            if '台灣中油' in table_text and '台塑石化' in table_text:
                print(f"找到油價資料表格 #{table_idx + 1}")
                
                # 尋找表格中的所有行
                rows = table.find_all('tr')
                print(f"該表格包含 {len(rows)} 行")
                
                # 第一行通常包含最新的資料
                for row_idx, row in enumerate(rows):
                    # 跳過標題行
                    if row_idx == 0:
                        continue
                        
                    # 獲取該行中的所有單元格
                    cells = row.find_all(['td', 'th'])
                    
                    # 如果找到的單元格數量足夠
                    if len(cells) >= 8:
                        # 嘗試獲取日期資訊
                        date_text = cells[0].get_text().strip()
                        print(f"日期文字: {date_text}")
                        
                        # 如果這是中油的資料行
                        if '台灣中油' in cells[1].get_text():
                            # 獲取油價資料
                            oil_data['cpc']['92'] = cells[2].get_text().strip()
                            oil_data['cpc']['95'] = cells[3].get_text().strip()
                            oil_data['cpc']['98'] = cells[4].get_text().strip()
                            oil_data['cpc']['diesel'] = cells[5].get_text().strip()
                            
                            # 設置更新時間
                            oil_data['update_time'] = date_text
                        
                        # 如果這是台塑的資料行
                        elif '台塑石化' in cells[1].get_text():
                            # 獲取油價資料
                            oil_data['fpg']['92'] = cells[2].get_text().strip()
                            oil_data['fpg']['95'] = cells[3].get_text().strip()
                            oil_data['fpg']['98'] = cells[4].get_text().strip()
                            oil_data['fpg']['diesel'] = cells[5].get_text().strip()
                
                # 如果已經找到資料，跳出循環
                if oil_data['update_time'] != '暫無資料':
                    break
        
        # 如果沒有在表格中找到資料，嘗試直接從頁面中提取
        if oil_data['update_time'] == '暫無資料':
            print("在表格中沒有找到資料，嘗試使用備用方法")
            
            # 嘗試獲取最新日期
            date_pattern = r'\d{4}/\d{2}/\d{2}'
            date_matches = re.findall(date_pattern, soup.get_text())
            if date_matches:
                latest_date = date_matches[0]
                oil_data['update_time'] = latest_date
                print(f"找到日期: {latest_date}")
            
            # 嘗試獲取92無鉛汽油價格
            price_92_pattern = r'92無鉛汽油[^\d]*(\d+\.\d+)'
            price_92_matches = re.findall(price_92_pattern, soup.get_text())
            if price_92_matches:
                oil_data['cpc']['92'] = price_92_matches[0]
                if len(price_92_matches) > 1:
                    oil_data['fpg']['92'] = price_92_matches[1]
            
            # 嘗試獲取95無鉛汽油價格
            price_95_pattern = r'95無鉛汽油[^\d]*(\d+\.\d+)'
            price_95_matches = re.findall(price_95_pattern, soup.get_text())
            if price_95_matches:
                oil_data['cpc']['95'] = price_95_matches[0]
                if len(price_95_matches) > 1:
                    oil_data['fpg']['95'] = price_95_matches[1]
            
            # 嘗試獲取98無鉛汽油價格
            price_98_pattern = r'98無鉛汽油[^\d]*(\d+\.\d+)'
            price_98_matches = re.findall(price_98_pattern, soup.get_text())
            if price_98_matches:
                oil_data['cpc']['98'] = price_98_matches[0]
                if len(price_98_matches) > 1:
                    oil_data['fpg']['98'] = price_98_matches[1]
            
            # 嘗試獲取超級柴油價格
            diesel_pattern = r'超級柴油[^\d]*(\d+\.\d+)'
            diesel_matches = re.findall(diesel_pattern, soup.get_text())
            if diesel_matches:
                oil_data['cpc']['diesel'] = diesel_matches[0]
                if len(diesel_matches) > 1:
                    oil_data['fpg']['diesel'] = diesel_matches[1]
        
        # 如果依然沒有找到資料，嘗試訪問另一個頁面
        if oil_data['update_time'] == '暫無資料':
            print("嘗試訪問另一個頁面獲取資料")
            alt_url = "https://www2.moeaea.gov.tw/oil111/Gasoline/RetailPrice"
            alt_response = requests.get(alt_url, headers=headers, timeout=30)
            alt_response.encoding = 'utf-8'
            
            if alt_response.status_code == 200:
                alt_soup = BeautifulSoup(alt_response.text, 'html.parser')
                
                # 查找表格
                alt_table = alt_soup.find('table', {'class': 'table-format'})
                if alt_table:
                    rows = alt_table.find_all('tr')
                    for row in rows[1:3]:  # 假設前兩行包含中油和台塑的最新資料
                        cells = row.find_all('td')
                        if len(cells) >= 7:
                            date_text = cells[0].get_text().strip()
                            company = cells[1].get_text().strip()
                            
                            if '台灣中油' in company:
                                oil_data['cpc']['92'] = cells[3].get_text().strip()
                                oil_data['cpc']['95'] = cells[4].get_text().strip()
                                oil_data['cpc']['98'] = cells[5].get_text().strip()
                                oil_data['cpc']['diesel'] = cells[6].get_text().strip()
                                oil_data['update_time'] = date_text
                            
                            elif '台塑石化' in company:
                                oil_data['fpg']['92'] = cells[3].get_text().strip()
                                oil_data['fpg']['95'] = cells[4].get_text().strip()
                                oil_data['fpg']['98'] = cells[5].get_text().strip()
                                oil_data['fpg']['diesel'] = cells[6].get_text().strip()
        
        # 添加爬蟲執行時間
        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
        oil_data['crawl_time'] = current_time
        
        # 如果成功獲取資料，輸出結果
        if oil_data['update_time'] != '暫無資料':
            print("成功獲取油價資料:")
            print(f"更新時間: {oil_data['update_time']}")
            print(f"中油92: {oil_data['cpc']['92']}")
            print(f"中油95: {oil_data['cpc']['95']}")
            print(f"中油98: {oil_data['cpc']['98']}")
            print(f"中油柴油: {oil_data['cpc']['diesel']}")
            print(f"台塑92: {oil_data['fpg']['92']}")
            print(f"台塑95: {oil_data['fpg']['95']}")
            print(f"台塑98: {oil_data['fpg']['98']}")
            print(f"台塑柴油: {oil_data['fpg']['diesel']}")
            
        return oil_data
    
    except Exception as e:
        print(f"爬取失敗：{e}")
        # 添加爬蟲執行時間
        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
        oil_data['crawl_time'] = current_time
        oil_data['error'] = str(e)
        return oil_data

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
    try:
        print("開始執行爬蟲程式...")
        # 確保 data 資料夾存在
        os.makedirs("data", exist_ok=True)
        
        # 爬取油價資料
        oil_prices = fetch_oil_prices()
        
        # 儲存至 JSON 檔案
        save_to_json(oil_prices, "data/oil_prices.json")
        print("油價資料更新成功！")
    except Exception as e:
        print(f"程式執行失敗：{e}")
        sys.exit(1)

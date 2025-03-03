import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pytz
import re
import sys
import time

def fetch_oil_prices():
    """
    從經濟部能源署網站爬取最新油價資訊
    """
    # 初始化資料結構
    oil_data = {
        'cpc': {'92': '暫無資料', '95': '暫無資料', '98': '暫無資料', 'diesel': '暫無資料'},
        'fpg': {'92': '暫無資料', '95': '暫無資料', '98': '暫無資料', 'diesel': '暫無資料'},
        'update_time': '暫無資料'
    }
    
    # 設定請求標頭，模擬瀏覽器行為
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # 直接爬取汽柴油參考零售價頁面
        url = "https://www2.moeaea.gov.tw/oil111/Gasoline/RetailPrice"
        print(f"正在請求網址: {url}")
        
        # 發送請求
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'  # 確保正確編碼
        
        # 檢查請求是否成功
        if response.status_code != 200:
            print(f"請求失敗，狀態碼：{response.status_code}")
            return oil_data
        
        # 解析HTML內容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找數據資料表
        print("正在尋找數據資料表...")
        tables = soup.find_all('table')
        
        target_table = None
        for table in tables:
            if "台灣中油" in table.text and "台塑石化" in table.text:
                target_table = table
                break
        
        if target_table:
            print("找到目標表格，開始解析資料...")
            
            # 取得所有行
            rows = target_table.find_all('tr')
            
            # 跳過標題行，取第一筆資料（最新的油價資訊）
            if len(rows) > 2:  # 確保至少有標題行和一行資料
                # 中油數據（通常在第一行）
                cpc_row = None
                fpg_row = None
                
                # 尋找中油和台塑的行
                for i in range(1, min(4, len(rows))):  # 檢查前幾行
                    row_cells = rows[i].find_all('td')
                    if len(row_cells) >= 7:
                        if "台灣中油" in row_cells[1].text:
                            cpc_row = row_cells
                            # 取得更新日期
                            oil_data['update_time'] = row_cells[0].text.strip()
                        elif "台塑石化" in row_cells[1].text:
                            fpg_row = row_cells
                
                # 解析中油數據
                if cpc_row:
                    oil_data['cpc']['92'] = cpc_row[3].text.strip()
                    oil_data['cpc']['95'] = cpc_row[4].text.strip()
                    oil_data['cpc']['98'] = cpc_row[5].text.strip()
                    oil_data['cpc']['diesel'] = cpc_row[6].text.strip()
                    print(f"已獲取中油油價資料：92={oil_data['cpc']['92']}, 95={oil_data['cpc']['95']}, 98={oil_data['cpc']['98']}, 柴油={oil_data['cpc']['diesel']}")
                
                # 解析台塑數據
                if fpg_row:
                    oil_data['fpg']['92'] = fpg_row[3].text.strip()
                    oil_data['fpg']['95'] = fpg_row[4].text.strip()
                    oil_data['fpg']['98'] = fpg_row[5].text.strip()
                    oil_data['fpg']['diesel'] = fpg_row[6].text.strip()
                    print(f"已獲取台塑油價資料：92={oil_data['fpg']['92']}, 95={oil_data['fpg']['95']}, 98={oil_data['fpg']['98']}, 柴油={oil_data['fpg']['diesel']}")
        else:
            print("在頁面中未找到目標表格，嘗試使用備用方法...")
            
            # 使用正則表達式直接從頁面中提取日期和價格
            # 提取最新日期
            date_pattern = r'\d{4}/\d{2}/\d{2}'
            date_matches = re.findall(date_pattern, soup.text)
            if date_matches:
                oil_data['update_time'] = date_matches[0]
                print(f"找到更新日期: {oil_data['update_time']}")
            
            # 嘗試提取中油和台塑的92、95、98無鉛汽油以及超級柴油價格
            try:
                # 尋找表格內容
                table_content = soup.find('div', {'id': 'datatable'})
                if table_content:
                    # 尋找最新的一筆資料
                    first_row = table_content.find('tr', class_=lambda x: x and ('tr_odd' in x or 'tr_even' in x))
                    if first_row:
                        cells = first_row.find_all('td')
                        if len(cells) > 10:
                            # 更新日期
                            oil_data['update_time'] = cells[0].text.strip()
                            
                            # 中油價格
                            oil_data['cpc']['92'] = cells[3].text.strip()
                            oil_data['cpc']['95'] = cells[4].text.strip()
                            oil_data['cpc']['98'] = cells[5].text.strip()
                            oil_data['cpc']['diesel'] = cells[6].text.strip()
                            
                            # 台塑價格
                            oil_data['fpg']['92'] = cells[8].text.strip()
                            oil_data['fpg']['95'] = cells[9].text.strip()
                            oil_data['fpg']['98'] = cells[10].text.strip()
                            oil_data['fpg']['diesel'] = cells[11].text.strip()
                            
                            print(f"使用備用方法成功獲取油價資料")
            except Exception as e:
                print(f"備用方法提取失敗: {e}")
        
        # 添加爬蟲執行時間
        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
        oil_data['crawl_time'] = current_time
        
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

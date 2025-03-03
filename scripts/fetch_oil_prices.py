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
        'Referer': 'https://www2.moeaea.gov.tw/oil111/Home',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    
    try:
        # 直接爬取汽柴油參考零售價頁面
        url = "https://www2.moeaea.gov.tw/oil111/Gasoline/RetailPrice"
        print(f"正在請求網址: {url}")
        
        # 發送請求，設置超時時間為30秒
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
        print(f"找到 {len(tables)} 個表格")
        
        target_table = None
        for table in tables:
            if "台灣中油" in table.text and "台塑石化" in table.text:
                target_table = table
                break
        
        # 如果找不到表格，使用CSS選擇器直接選擇
        if not target_table:
            try:
                target_table = soup.select_one('.table_wrapper .report_table table.detail')
                print("使用CSS選擇器找到表格")
            except Exception as e:
                print(f"使用CSS選擇器查找表格失敗: {e}")
        
        if target_table:
            print("找到目標表格，開始解析資料...")
            
            # 取得所有行
            rows = target_table.find_all('tr')
            print(f"表格中有 {len(rows)} 行")
            
            # 跳過標題行，取第一筆資料（最新的油價資訊）
            if len(rows) > 2:  # 確保至少有標題行和一行資料
                try:
                    # 取第三行 (索引2)，這是最新的數據行
                    data_row = rows[2]
                    cells = data_row.find_all('td')
                    print(f"第一個數據行有 {len(cells)} 個單元格")
                    
                    # 解析日期
                    date_cell = cells[0].text.strip()
                    oil_data['update_time'] = date_cell
                    print(f"更新日期: {date_cell}")
                    
                    # 中油數據 - 第3,4,5,6欄
                    cpc_92 = cells[2].text.strip()
                    cpc_95 = cells[3].text.strip()
                    cpc_98 = cells[4].text.strip()
                    cpc_diesel = cells[5].text.strip()
                    
                    oil_data['cpc']['92'] = cpc_92
                    oil_data['cpc']['95'] = cpc_95
                    oil_data['cpc']['98'] = cpc_98
                    oil_data['cpc']['diesel'] = cpc_diesel
                    
                    print(f"中油數據: 92={cpc_92}, 95={cpc_95}, 98={cpc_98}, 柴油={cpc_diesel}")
                    
                    # 台塑數據 - 第8,9,10,11欄
                    fpg_92 = cells[7].text.strip()
                    fpg_95 = cells[8].text.strip()
                    fpg_98 = cells[9].text.strip()
                    fpg_diesel = cells[10].text.strip()
                    
                    oil_data['fpg']['92'] = fpg_92
                    oil_data['fpg']['95'] = fpg_95
                    oil_data['fpg']['98'] = fpg_98
                    oil_data['fpg']['diesel'] = fpg_diesel
                    
                    print(f"台塑數據: 92={fpg_92}, 95={fpg_95}, 98={fpg_98}, 柴油={fpg_diesel}")
                    
                except Exception as e:
                    print(f"解析數據時出錯: {e}")
                    print("嘗試其他解析方法...")
                    
                    # 備用解析方法：尋找特定日期的行
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) > 6:
                            try:
                                date_text = cells[0].text.strip()
                                if "2025/03/03" in date_text:  # 尋找最新日期的行
                                    oil_data['update_time'] = date_text
                                    
                                    # 中油數據
                                    oil_data['cpc']['92'] = cells[2].text.strip()
                                    oil_data['cpc']['95'] = cells[3].text.strip()
                                    oil_data['cpc']['98'] = cells[4].text.strip()
                                    oil_data['cpc']['diesel'] = cells[5].text.strip()
                                    
                                    # 台塑數據
                                    oil_data['fpg']['92'] = cells[7].text.strip()
                                    oil_data['fpg']['95'] = cells[8].text.strip()
                                    oil_data['fpg']['98'] = cells[9].text.strip()
                                    oil_data['fpg']['diesel'] = cells[10].text.strip()
                                    
                                    print("使用備用方法成功解析數據")
                                    break
                            except Exception as e:
                                print(f"處理行時出錯: {e}")
                                continue
        else:
            print("在頁面中未找到目標表格")
            
            # 使用正則表達式直接從頁面文本中提取數據
            print("嘗試使用正則表達式提取數據...")
            try:
                # 提取日期
                date_pattern = r'\d{4}/\d{2}/\d{2}'
                date_matches = re.findall(date_pattern, soup.text)
                if date_matches:
                    oil_data['update_time'] = date_matches[0]
                    print(f"找到日期: {oil_data['update_time']}")
                
                # 找到包含油價的表格文本
                table_content = soup.find('div', {'id': 'datatable'})
                if table_content:
                    print("找到數據表格內容")
                    table_text = table_content.text
                    
                    # 尋找中油和台塑的價格
                    # 這裡需要根據實際頁面結構調整正則表達式
                    patterns = {
                        'cpc_92': r'台灣中油.*?0時.*?(\d+\.\d+)',
                        'cpc_95': r'台灣中油.*?0時.*?\d+\.\d+\s+(\d+\.\d+)',
                        'cpc_98': r'台灣中油.*?0時.*?\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)',
                        'cpc_diesel': r'台灣中油.*?0時.*?\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)',
                        'fpg_92': r'台塑石化.*?1時.*?(\d+\.\d+)',
                        'fpg_95': r'台塑石化.*?1時.*?\d+\.\d+\s+(\d+\.\d+)',
                        'fpg_98': r'台塑石化.*?1時.*?\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)',
                        'fpg_diesel': r'台塑石化.*?1時.*?\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)'
                    }
                    
                    for key, pattern in patterns.items():
                        matches = re.findall(pattern, table_text)
                        if matches:
                            # 根據key設置相應的字典值
                            if key.startswith('cpc_'):
                                oil_type = key.split('_')[1]
                                oil_data['cpc'][oil_type] = matches[0]
                                print(f"中油 {oil_type} = {matches[0]}")
                            elif key.startswith('fpg_'):
                                oil_type = key.split('_')[1]
                                oil_data['fpg'][oil_type] = matches[0]
                                print(f"台塑 {oil_type} = {matches[0]}")
            except Exception as e:
                print(f"正則表達式提取失敗: {e}")
        
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

def get_latest_oil_prices_manual():
    """提供最新的手動更新油價作為備用方案"""
    # 從經濟部能源署網站上看到的最新數據
    oil_data = {
        'cpc': {'92': '29.7', '95': '31.2', '98': '33.2', 'diesel': '28.9'},
        'fpg': {'92': '29.7', '95': '31.2', '98': '33.2', 'diesel': '28.7'},
        'update_time': '2025/03/03'
    }
    
    # 添加爬蟲執行時間
    taipei_tz = pytz.timezone('Asia/Taipei')
    current_time = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
    oil_data['crawl_time'] = current_time
    oil_data['note'] = "備用數據（自動更新失敗後使用）"
    
    return oil_data

def save_to_json(data, file_path):
    """將爬取到的資料儲存為 JSON 檔案"""
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
        
        # 驗證爬蟲獲取的數據
        # 檢查是否所有值都是「暫無資料」
        all_empty = all(value == '暫無資料' for value in oil_prices['cpc'].values()) and \
                   all(value == '暫無資料' for value in oil_prices['fpg'].values())
        
        # 如果爬蟲失敗，使用備用數據
        if all_empty or oil_prices['update_time'] == '暫無資料':
            print("爬蟲未獲取到有效數據，使用備用數據...")
            oil_prices = get_latest_oil_prices_manual()
        
        # 儲存至 JSON 檔案
        save_to_json(oil_prices, "data/oil_prices.json")
        print("油價資料更新成功！")
    except Exception as e:
        print(f"程式執行失敗：{e}")
        # 即使出錯也嘗試保存備用數據
        try:
            print("嘗試使用備用數據...")
            oil_prices = get_latest_oil_prices_manual()
            save_to_json(oil_prices, "data/oil_prices.json")
            print("已保存備用數據")
        except Exception as backup_error:
            print(f"保存備用數據也失敗: {backup_error}")
        sys.exit(1)

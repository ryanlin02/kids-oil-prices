# scrape_oil_prices.py
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
import time

def scrape_cpc_prices():
    """爬取台灣中油的油價資訊"""
    try:
        # 中油油價網頁 - 使用專門的油價網頁而非首頁
        url = "https://www.cpc.com.tw/historyprice.aspx"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        print(f"中油網頁狀態碼: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到價格表格 - 使用更精確的選擇器
        price_table = soup.select_one('table.table_main')
        
        if not price_table:
            print("找不到中油油價表格，嘗試其他選擇器")
            # 備用選擇器
            price_table = soup.select_one('table')
            
            if not price_table:
                # 記錄HTML內容以便診斷
                print("無法找到任何表格，輸出部分HTML內容進行診斷:")
                print(response.text[:500])
                raise Exception("找不到中油油價表格")
                
        # 找到最新的一行數據
        rows = price_table.select('tr')
        
        if len(rows) < 2:
            raise Exception("中油表格結構異常")
            
        latest_row = rows[1]  # 假設第一行是標題，第二行是最新數據
        cells = latest_row.select('td')
        
        # 輸出診斷信息
        print(f"找到中油表格，共有 {len(rows)} 行")
        print(f"最新行有 {len(cells)} 個單元格")
        
        # 直接從網頁抓取後處理數據
        prices = {}
        
        # 使用備用方法 - 嘗試在頁面上查找所有顯示油價的元素
        price_elements = soup.select('.price')
        if price_elements:
            for element in price_elements:
                text = element.get_text().strip()
                print(f"找到價格元素: {text}")
                
                if '92' in text:
                    prices['gasoline_92'] = extract_price(text)
                elif '95' in text:
                    prices['gasoline_95'] = extract_price(text)
                elif '98' in text:
                    prices['gasoline_98'] = extract_price(text)
                elif '柴油' in text:
                    prices['diesel'] = extract_price(text)
        
        # 如果上面方法沒有找到，嘗試直接解析當前油價頁面
        if not prices:
            print("嘗試從中油油價網頁直接查找價格...")
            price_texts = re.findall(r'(9[258](?:無鉛汽油|汽油)|(?:超級)?柴油)[^\d]+([\d.]+)', response.text)
            
            for fuel_type, price in price_texts:
                print(f"匹配到: {fuel_type} - {price}")
                
                if '92' in fuel_type:
                    prices['gasoline_92'] = price
                elif '95' in fuel_type:
                    prices['gasoline_95'] = price
                elif '98' in fuel_type:
                    prices['gasoline_98'] = price
                elif '柴油' in fuel_type:
                    prices['diesel'] = price
                
        # 如果還是沒有找到，嘗試使用固定的爬蟲
        if not prices:
            print("使用備用方法獲取中油油價...")
            
            # 嘗試台灣中油官方首頁
            url = "https://www.cpc.com.tw/zh-tw/index.html"
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 在首頁尋找油價信息
            all_text = soup.get_text()
            price_matches = re.findall(r'(92|95|98)(?:無鉛汽油|汽油)[^\d]*([\d.]+)', all_text)
            diesel_match = re.search(r'(?:超級)?柴油[^\d]*([\d.]+)', all_text)
            
            for fuel_type, price in price_matches:
                if fuel_type == '92':
                    prices['gasoline_92'] = price
                elif fuel_type == '95':
                    prices['gasoline_95'] = price
                elif fuel_type == '98':
                    prices['gasoline_98'] = price
            
            if diesel_match:
                prices['diesel'] = diesel_match.group(1)
        
        # 如果還是找不到，使用預設值
        if not prices or len(prices) < 4:
            missing_keys = set(['gasoline_92', 'gasoline_95', 'gasoline_98', 'diesel']) - set(prices.keys())
            print(f"部分油價數據缺失: {missing_keys}，使用預設值")
            
            if 'gasoline_92' not in prices:
                prices['gasoline_92'] = 'N/A'
            if 'gasoline_95' not in prices:
                prices['gasoline_95'] = 'N/A'
            if 'gasoline_98' not in prices:
                prices['gasoline_98'] = 'N/A'
            if 'diesel' not in prices:
                prices['diesel'] = 'N/A'
        
        return prices
        
    except Exception as e:
        print(f"爬取中油油價時發生錯誤: {e}")
        # 若爬取失敗，返回預設值
        return {
            'gasoline_92': 'N/A',
            'gasoline_95': 'N/A',
            'gasoline_98': 'N/A',
            'diesel': 'N/A'
        }

def scrape_fpg_prices():
    """爬取台塑石化的油價資訊"""
    try:
        # 台塑油價專頁
        url = "https://oil.com.tw/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        print(f"油價網站狀態碼: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = {}
        
        # 尋找台塑油價信息 (這個網站包含了台塑的資料)
        fpg_prices = soup.select('.price_fpcc li')
        
        if fpg_prices:
            print(f"找到台塑油價元素，數量: {len(fpg_prices)}")
            
            for item in fpg_prices:
                text = item.get_text().strip()
                print(f"台塑價格項目: {text}")
                
                if '92無鉛' in text or '92汽油' in text:
                    prices['gasoline_92'] = extract_price(text)
                elif '95無鉛' in text or '95汽油' in text:
                    prices['gasoline_95'] = extract_price(text)
                elif '98無鉛' in text or '98汽油' in text:
                    prices['gasoline_98'] = extract_price(text)
                elif '柴油' in text:
                    prices['diesel'] = extract_price(text)
        
        # 如果上述方法找不到，嘗試使用官方網站
        if not prices or len(prices) < 4:
            print("從油價網站找不到完整台塑油價，嘗試官方網站...")
            
            # 台塑官網
            fpg_url = "https://www.fpcc.com.tw/tw/price"
            response = requests.get(fpg_url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到油價表格
            table = soup.select_one('table.rwd-table')
            
            if table:
                rows = table.select('tr')
                print(f"找到台塑官網表格，共有 {len(rows)} 行")
                
                for row in rows:
                    cols = row.select('td')
                    if len(cols) >= 2:
                        name = cols[0].get_text().strip()
                        price = cols[1].get_text().strip()
                        
                        print(f"台塑表格項目: {name} - {price}")
                        
                        if '92無鉛汽油' in name or '92汽油' in name:
                            prices['gasoline_92'] = extract_price(price)
                        elif '95無鉛汽油' in name or '95汽油' in name:
                            prices['gasoline_95'] = extract_price(price)
                        elif '98無鉛汽油' in name or '98汽油' in name:
                            prices['gasoline_98'] = extract_price(price)
                        elif '超級柴油' in name or '柴油' in name:
                            prices['diesel'] = extract_price(price)
        
        # 如果還是找不到，使用預設值
        if not prices or len(prices) < 4:
            missing_keys = set(['gasoline_92', 'gasoline_95', 'gasoline_98', 'diesel']) - set(prices.keys())
            print(f"部分台塑油價數據缺失: {missing_keys}，使用預設值")
            
            if 'gasoline_92' not in prices:
                prices['gasoline_92'] = 'N/A'
            if 'gasoline_95' not in prices:
                prices['gasoline_95'] = 'N/A'
            if 'gasoline_98' not in prices:
                prices['gasoline_98'] = 'N/A'
            if 'diesel' not in prices:
                prices['diesel'] = 'N/A'
        
        return prices
    except Exception as e:
        print(f"爬取台塑油價時發生錯誤: {e}")
        # 若爬取失敗，返回預設值
        return {
            'gasoline_92': 'N/A',
            'gasoline_95': 'N/A',
            'gasoline_98': 'N/A',
            'diesel': 'N/A'
        }

def extract_price(text):
    """從文字中提取價格"""
    # 嘗試使用正則表達式提取數字
    match = re.search(r'(\d+\.\d+)', text)
    if match:
        return match.group(1)
    # 如果沒有找到小數點格式，嘗試整數
    match = re.search(r'(\d+)', text)
    if match:
        return match.group(1)
    return 'N/A'

def fallback_prices():
    """如果爬蟲失敗，使用第三方API獲取油價"""
    try:
        url = "https://raw.githubusercontent.com/GoneToneStudio/oil-price-api/master/data/data.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        cpc_prices = {
            'gasoline_92': str(data.get('cpc', {}).get('92', 'N/A')),
            'gasoline_95': str(data.get('cpc', {}).get('95', 'N/A')),
            'gasoline_98': str(data.get('cpc', {}).get('98', 'N/A')),
            'diesel': str(data.get('cpc', {}).get('diesel', 'N/A'))
        }
        
        fpg_prices = {
            'gasoline_92': str(data.get('fpcc', {}).get('92', 'N/A')),
            'gasoline_95': str(data.get('fpcc', {}).get('95', 'N/A')),
            'gasoline_98': str(data.get('fpcc', {}).get('98', 'N/A')),
            'diesel': str(data.get('fpcc', {}).get('diesel', 'N/A'))
        }
        
        return cpc_prices, fpg_prices
    except Exception as e:
        print(f"使用備用API獲取油價失敗: {e}")
        return None, None

def main():
    # 爬取油價
    print("開始爬取中油油價...")
    cpc_prices = scrape_cpc_prices()
    
    print("開始爬取台塑油價...")
    fpg_prices = scrape_fpg_prices()
    
    # 檢查爬取結果是否有效
    cpc_valid = all(price != 'N/A' for price in cpc_prices.values())
    fpg_valid = all(price != 'N/A' for price in fpg_prices.values())
    
    # 如果爬蟲失敗，使用備用API
    if not (cpc_valid and fpg_valid):
        print("爬蟲結果不完整，嘗試使用備用API...")
        fallback_cpc, fallback_fpg = fallback_prices()
        
        if fallback_cpc and fallback_fpg:
            print("成功從備用API獲取油價")
            if not cpc_valid:
                cpc_prices = fallback_cpc
            if not fpg_valid:
                fpg_prices = fallback_fpg
    
    # 獲取目前時間
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 建立油價資料
    oil_data = {
        'cpc': cpc_prices,
        'fpg': fpg_prices,
        'update_time': now
    }
    
    # 確保輸出目錄存在
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 將資料寫入JSON檔案
    with open(os.path.join(output_dir, 'oil_prices.json'), 'w', encoding='utf-8') as f:
        json.dump(oil_data, f, ensure_ascii=False, indent=2)
    
    print(f"油價資料已更新: {now}")
    print(f"中油油價: {cpc_prices}")
    print(f"台塑油價: {fpg_prices}")

if __name__ == "__main__":
    # 添加重試機制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"執行爬蟲 (嘗試 {attempt+1}/{max_retries})...")
            main()
            print("爬蟲成功完成")
            break
        except Exception as e:
            print(f"執行爬蟲時發生錯誤: {e}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                print("已達最大重試次數，爬蟲失敗")

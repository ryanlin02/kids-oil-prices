# scrape_oil_prices.py
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os

def scrape_cpc_prices():
    """爬取台灣中油的油價資訊"""
    try:
        url = "https://www.cpc.com.tw/zh-tw/index.html"
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到油價表格區域
        price_div = soup.find('div', {'class': 'price'})
        
        if not price_div:
            raise Exception("找不到中油油價表格")
            
        prices = {}
        
        # 尋找各種油品的價格
        price_items = price_div.find_all('li')
        
        for item in price_items:
            text = item.get_text().strip()
            
            if '92無鉛' in text:
                prices['gasoline_92'] = extract_price(text)
            elif '95無鉛' in text:
                prices['gasoline_95'] = extract_price(text)
            elif '98無鉛' in text:
                prices['gasoline_98'] = extract_price(text)
            elif '超級柴油' in text:
                prices['diesel'] = extract_price(text)
        
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
        url = "https://www.fpg.com.tw/tw/price"
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到油價表格
        table = soup.find('table', {'class': 'rwd-table'})
        
        if not table:
            raise Exception("找不到台塑油價表格")
            
        prices = {}
        
        # 尋找各種油品的價格
        rows = table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                name = cols[0].get_text().strip()
                price = cols[1].get_text().strip()
                
                if '92無鉛汽油' in name:
                    prices['gasoline_92'] = extract_price(price)
                elif '95無鉛汽油' in name:
                    prices['gasoline_95'] = extract_price(price)
                elif '98無鉛汽油' in name:
                    prices['gasoline_98'] = extract_price(price)
                elif '超級柴油' in name:
                    prices['diesel'] = extract_price(price)
        
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
    return 'N/A'

def main():
    # 爬取油價
    cpc_prices = scrape_cpc_prices()
    fpg_prices = scrape_fpg_prices()
    
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

if __name__ == "__main__":
    main()

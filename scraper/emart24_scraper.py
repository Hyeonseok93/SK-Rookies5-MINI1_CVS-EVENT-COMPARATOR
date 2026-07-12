import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import re
from datetime import datetime

class Emart24Scraper:
    def __init__(self):
        self.brand = "emart24"
        self.base_url = "https://emart24.co.kr/goods/event"
        # 1: 1+1, 2: 2+1, 3: 3+1 카테고리까지 수집하도록 설정
        self.categories = {1: '1+1', 2: '2+1', 3: '3+1'}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }

    def run(self):
        start_ts = datetime.now()
        print(f"🚀 [{self.brand}] 데이터 수집을 시작합니다...")
        
        data_list = []

        for seq, label in self.categories.items():
            page = 1
            print(f" 📦 {label} 카테고리 수집 중...")
            
            while True:
                params = {'page': page, 'category_seq': seq}
                try:
                    res = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    items = soup.find_all('div', class_='itemWrap')
                except Exception: break

                if not items: break

                for item in items:
                    try:
                        name = item.select_one('.itemtitle p a').text.strip()
                        # 가격 데이터에서 숫자만 추출하여 정수형으로 변환
                        price_text = item.select_one('.price').text.strip()
                        price = int(re.sub(r'[^0-9]', '', price_text))
                        
                        event = item.select_one('.itemTit span.floatR').text.strip() if item.select_one('.itemTit span.floatR') else label
                        img_raw = item.select_one('.itemSpImg img')['src']
                        img_url = img_raw if img_raw.startswith('http') else f"https://emart24.co.kr{img_raw}"
                        data_list.append({'brand': self.brand, 'name': name, 'price': price, 'event': event, 'img_url': img_url})
                    except Exception: continue
                page += 1
                time.sleep(random.uniform(0.1, 0.3))
            
        self._save_to_csv(data_list, start_ts)

    def _save_to_csv(self, data_list, start_ts):
        from scraper.base import save_products
        save_products(pd.DataFrame(data_list), self.brand, start_ts=start_ts)

def scrape():
    scraper = Emart24Scraper()
    scraper.run()

if __name__ == "__main__":
    scrape()

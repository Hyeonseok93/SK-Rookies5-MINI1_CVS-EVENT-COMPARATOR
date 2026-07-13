import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
from datetime import datetime

class CUCrawler:
    def __init__(self):
        self.brand = "CU"
        self.base_url = "https://cu.bgfretail.com/event/plusAjax.do"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://cu.bgfretail.com/event/plus.do"
        }
        self.product_list = []

    def fetch_page(self, page_index):
        payload = {"pageIndex": page_index, "listType": "0", "searchCondition": "", "searchWord": ""}
        try:
            response = requests.post(self.base_url, data=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception: return None

    def parse_data(self, html):
        if not html: return False
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("li.prod_list")
        if not items: return False
        for item in items:
            try:
                name = item.select_one(".name p").get_text(strip=True)
                price_raw = item.select_one(".price strong").get_text(strip=True)
                price = int(re.sub(r"[^\d]", "", price_raw))
                event_element = item.select_one(".badge span")
                event = event_element.get_text(strip=True) if event_element else "행사정보없음"
                img_url = item.select_one(".prod_img img")['src']
                if img_url.startswith("//"): img_url = "https:" + img_url
                self.product_list.append({"brand": self.brand, "name": name, "price": price, "event": event, "img_url": img_url})
            except Exception: continue 
        return True

    def run(self, max_pages=150):
        start_ts = datetime.now()
        t0 = time.perf_counter()
        print(f"🚀 [{self.brand}] 데이터 수집을 시작합니다...")
        
        for page in range(1, max_pages + 1):
            html = self.fetch_page(page)
            if not self.parse_data(html): break
            if page % 10 == 0: print(f" 📦 {page}페이지 수집 중... (누적: {len(self.product_list)}건)")
            time.sleep(0.5)

        self._save_to_csv(start_ts, t0)

    def _save_to_csv(self, start_ts, t0):
        from scraper.base import save_products
        save_products(
            pd.DataFrame(self.product_list),
            self.brand,
            start_ts=start_ts,
            t0=t0,
            dedupe_subset=['name', 'price', 'event'],
        )

def scrape():
    crawler = CUCrawler()
    crawler.run()

if __name__ == "__main__":
    scrape()

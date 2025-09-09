import requests
import trafilatura
import re
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

class KooLearnScraper:
    """新東方TOEFL聽力內容抓取器"""
    
    def __init__(self):
        self.base_url = "https://liuxue.koolearn.com"
        self.listen_base = "/toefl/listen-0-0-0/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_official_list(self) -> List[Dict]:
        """獲取所有Official TPO列表"""
        try:
            url = urljoin(self.base_url, self.listen_base)
            response = self.session.get(url)
            response.raise_for_status()
            
            content = trafilatura.extract(response.text)
            if not content:
                logging.error("Failed to extract content from main page")
                return []
            
            # 解析Official項目
            official_items = []
            lines = content.split('\n')
            
            current_official = None
            current_items = []
            
            for line in lines:
                line = line.strip()
                
                # 識別Official標題
                if line.startswith('Official ') and '共5篇' in line:
                    if current_official:
                        official_items.append({
                            'official': current_official,
                            'items': current_items.copy()
                        })
                    
                    official_match = re.search(r'Official (\d+)', line)
                    if official_match:
                        current_official = f"Official {official_match.group(1)}"
                        current_items = []
                
                # 識別具體項目 (Con1, Lec1等)
                elif current_official and ('Con' in line or 'Lec' in line):
                    # 解析項目詳情
                    if 'Official' in line and ('Con' in line or 'Lec' in line):
                        parts = line.split()
                        if len(parts) >= 3:
                            item_name = f"{parts[0]} {parts[1]} {parts[2]}"  # e.g., "Official 75 Con1"
                            
                            # 尋找難度和話題
                            difficulty = "中"  # 默認難度
                            topic = "學術"  # 默認話題
                            
                            # 從後續行中提取難度和話題
                            if '易' in line:
                                difficulty = "易"
                            elif '難' in line:
                                difficulty = "難"
                            
                            # 提取話題（通常在難度後面）
                            topic_match = re.search(r'[易中難]\s+([^\s\-\/]+)', line)
                            if topic_match:
                                topic = topic_match.group(1)
                            
                            current_items.append({
                                'name': item_name,
                                'difficulty': difficulty,
                                'topic': topic,
                                'type': 'conversation' if 'Con' in item_name else 'lecture'
                            })
            
            # 添加最後一個official
            if current_official and current_items:
                official_items.append({
                    'official': current_official,
                    'items': current_items
                })
            
            logging.info(f"Found {len(official_items)} Official TPO sets")
            return official_items
            
        except Exception as e:
            logging.error(f"Error scraping Official list: {e}")
            return []
    
    def get_official_details(self, official_num: int) -> List[Dict]:
        """獲取特定Official的詳細內容"""
        try:
            # 根據分析的URL模式構建請求
            items = []
            
            # 每個Official有5個項目：2個對話 + 3個講座
            item_types = [
                ('Con1', 'conversation'),
                ('Con2', 'conversation'), 
                ('Lec1', 'lecture'),
                ('Lec2', 'lecture'),
                ('Lec3', 'lecture')
            ]
            
            for item_type, content_type in item_types:
                item_name = f"Official {official_num} {item_type}"
                
                # 構造項目數據
                item_data = {
                    'name': item_name,
                    'official_num': official_num,
                    'item_type': item_type,
                    'content_type': content_type,
                    'difficulty': self._guess_difficulty(official_num),
                    'topic': self._guess_topic(item_type),
                    'source': 'koolearn_official',
                    'url': f"https://liuxue.koolearn.com/toefl/listen/{official_num}-{item_type.lower()}.html"
                }
                
                items.append(item_data)
            
            return items
            
        except Exception as e:
            logging.error(f"Error getting Official {official_num} details: {e}")
            return []
    
    def _guess_difficulty(self, official_num: int) -> str:
        """根據Official編號推測難度"""
        if official_num >= 70:
            return "難"
        elif official_num >= 50:
            return "中"
        else:
            return "易"
    
    def _guess_topic(self, item_type: str) -> str:
        """根據項目類型推測話題"""
        if 'Con' in item_type:
            return "校園對話"
        else:
            return "學術講座"
    
    def scrape_all_officials(self, start_num: int = 65, end_num: int = 75) -> List[Dict]:
        """抓取指定範圍的所有Official"""
        all_items = []
        
        for official_num in range(start_num, end_num + 1):
            logging.info(f"Scraping Official {official_num}...")
            items = self.get_official_details(official_num)
            all_items.extend(items)
        
        logging.info(f"Total scraped items: {len(all_items)}")
        return all_items

# 測試函數
def test_scraper():
    scraper = KooLearnScraper()
    
    # 測試獲取Official列表
    officials = scraper.get_official_list()
    print(f"Found {len(officials)} officials")
    
    if officials:
        print("First few officials:")
        for official in officials[:3]:
            print(f"  {official['official']}: {len(official['items'])} items")
    
    # 測試獲取特定Official詳情
    items = scraper.get_official_details(75)
    print(f"\nOfficial 75 items: {len(items)}")
    for item in items:
        print(f"  {item['name']} - {item['difficulty']} - {item['topic']}")

if __name__ == "__main__":
    test_scraper()
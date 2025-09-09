"""
新東方 Koolearn TPO 聽力內容爬蟲
用於獲取 TPO 01-64 的官方聽力內容並加入資料庫
"""
import requests
import time
import re
from bs4 import BeautifulSoup
from models import ContentSource, db
from app import app
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoolearnTPOScraper:
    def __init__(self):
        self.base_url = "https://liuxue.koolearn.com/toefl/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_tpo_list_urls(self):
        """獲取所有 TPO 列表頁面的 URL"""
        tpo_urls = []
        # TPO 分組 URL 模式
        tpo_groups = [
            ('listen-0-667-0', 'TPO 10-1'),    # TPO 10-1
            ('listen-0-656-0', 'TPO 20-11'),   # TPO 20-11  
            ('listen-0-645-0', 'TPO 30-21'),   # TPO 30-21
            ('listen-0-634-0', 'TPO 40-31'),   # TPO 40-31
            ('listen-0-623-0', 'TPO 50-41'),   # TPO 50-41
            ('listen-0-618-0', 'TPO 58-51'),   # TPO 58-51
            ('listen-0-1157-0', 'TPO 64-60'),  # TPO 64-60
        ]
        
        for url_path, name in tpo_groups:
            tpo_urls.append({
                'url': f"{self.base_url}{url_path}/",
                'name': name
            })
            
        return tpo_urls

    def parse_tpo_content(self, html_content):
        """解析 TPO 頁面內容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        tpo_items = []
        
        # 查找所有 TPO 項目
        for section in soup.find_all('div', {'class': re.compile(r'.*tpo.*', re.I)}):
            # 尋找 TPO 標題
            title_element = section.find(['h2', 'h3', 'h4'], string=re.compile(r'Official \d+'))
            if not title_element:
                continue
                
            tpo_number = re.search(r'Official (\d+)', title_element.text).group(1)
            
            # 查找該 TPO 下的所有聽力項目
            items = section.find_all('a', href=re.compile(r'/listen/\d+-\d+-q0\.html'))
            
            for item in items:
                try:
                    # 提取項目信息
                    name = item.text.strip()
                    url = item.get('href')
                    if not url.startswith('http'):
                        url = f"https://liuxue.koolearn.com{url}"
                    
                    # 查找難度和話題
                    difficulty = "中"  # 默認難度
                    topic = "聽力練習"  # 默認話題
                    
                    # 從頁面中提取更多信息
                    parent = item.find_parent()
                    if parent:
                        # 查找難度信息
                        difficulty_elem = parent.find(string=re.compile(r'[易中難]'))
                        if difficulty_elem:
                            difficulty = difficulty_elem.strip()
                            
                        # 查找話題信息
                        topic_elem = parent.find(string=re.compile(r'[心理學|動物|天文學|音樂|環境科學|建筑學|考古|工程學|哲學|植物|圖書館|美術|化學|商業|歷史|舞蹈|人類學]'))
                        if topic_elem:
                            topic = topic_elem.strip()
                    
                    tpo_items.append({
                        'tpo_number': int(tpo_number),
                        'name': name,
                        'url': url,
                        'difficulty': difficulty,
                        'topic': topic,
                        'type': 'conversation' if 'Con' in name else 'lecture'
                    })
                    
                except Exception as e:
                    logger.error(f"解析項目失敗: {e}")
                    continue
                    
        return tpo_items
    
    def fetch_tpo_details(self, item_url):
        """獲取單個 TPO 項目的詳細信息"""
        try:
            response = self.session.get(item_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取音檔 URL
            audio_url = None
            audio_element = soup.find('audio') or soup.find('source')
            if audio_element:
                audio_url = audio_element.get('src')
                if audio_url and not audio_url.startswith('http'):
                    audio_url = f"https://liuxue.koolearn.com{audio_url}"
            
            # 提取題目和選項
            questions = []
            question_elements = soup.find_all('div', {'class': re.compile(r'question')})
            
            for q_elem in question_elements:
                question_text = q_elem.get_text(strip=True)
                if question_text:
                    questions.append(question_text)
            
            return {
                'audio_url': audio_url,
                'questions': questions
            }
            
        except Exception as e:
            logger.error(f"獲取詳細信息失敗 {item_url}: {e}")
            return None
    
    def save_to_database(self, tpo_items):
        """將 TPO 項目保存到資料庫"""
        saved_count = 0
        
        with app.app_context():
            for item in tpo_items:
                try:
                    # 檢查是否已存在
                    existing = ContentSource.query.filter_by(
                        name=item['name'], 
                        type='tpo_official'
                    ).first()
                    
                    if existing:
                        logger.info(f"跳過已存在項目: {item['name']}")
                        continue
                    
                    # 創建新的內容項目
                    content = ContentSource(
                        name=item['name'],
                        description=f"TOEFL TPO {item['tpo_number']} Official Listening Practice - {item['topic']}",
                        url=item['url'],
                        type='tpo_official',
                        difficulty_level=item['difficulty'],
                        topic=item['topic'],
                        duration=300,  # 默認 5 分鐘
                        content_format='audio'
                    )
                    
                    db.session.add(content)
                    saved_count += 1
                    
                    logger.info(f"保存 TPO 項目: {item['name']}")
                    
                except Exception as e:
                    logger.error(f"保存失敗 {item['name']}: {e}")
                    continue
            
            try:
                db.session.commit()
                logger.info(f"成功保存 {saved_count} 個 TPO 項目到資料庫")
            except Exception as e:
                db.session.rollback()
                logger.error(f"資料庫提交失敗: {e}")
                
        return saved_count
    
    def scrape_all_tpo(self):
        """爬取所有 TPO 1-64 內容"""
        logger.info("開始爬取新東方 TPO 1-64 聽力內容...")
        
        all_items = []
        tpo_urls = self.get_tpo_list_urls()
        
        for url_info in tpo_urls:
            logger.info(f"爬取 {url_info['name']}: {url_info['url']}")
            
            try:
                response = self.session.get(url_info['url'], timeout=15)
                response.raise_for_status()
                
                items = self.parse_tpo_content(response.content)
                all_items.extend(items)
                
                logger.info(f"從 {url_info['name']} 獲取了 {len(items)} 個項目")
                
                # 避免過於頻繁的請求
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"爬取失敗 {url_info['url']}: {e}")
                continue
        
        # 過濾只保留 TPO 1-64
        tpo_1_64_items = [item for item in all_items if 1 <= item['tpo_number'] <= 64]
        
        logger.info(f"共獲取 {len(tpo_1_64_items)} 個 TPO 1-64 項目")
        
        if tpo_1_64_items:
            saved_count = self.save_to_database(tpo_1_64_items)
            logger.info(f"爬取完成！保存了 {saved_count} 個項目")
        
        return tpo_1_64_items

def main():
    """主函數"""
    scraper = KoolearnTPOScraper()
    scraper.scrape_all_tpo()

if __name__ == "__main__":
    main()
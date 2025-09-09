"""
重建Official TPO Collection - 使用真實的Koolearn URL結構
"""
import os
import psycopg2
import requests
from bs4 import BeautifulSoup
import re

def extract_tpo_items_from_url(url):
    """從Koolearn頁面提取TPO項目"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        items = []
        # 查找所有TPO項目鏈接
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 匹配Official TPO項目
            if 'Official' in text and ('Con' in text or 'Lec' in text):
                if '/toefl/listen/' in href and '-q0.html' in href:
                    # 提取難度和話題信息
                    difficulty = "中"  # 默認中等難度
                    topic = "General"  # 默認話題
                    
                    # 在同一行查找難度和話題
                    parent = link.find_parent()
                    if parent:
                        parent_text = parent.get_text()
                        if '易' in parent_text:
                            difficulty = "易"
                        elif '難' in parent_text:
                            difficulty = "難"
                        
                        # 提取話題
                        topics = ['學術', '社團', '食宿', '圖書館', '選課咨詢', '其它咨詢', 
                                '動物', '植物', '美術', '歷史', '地質地理學', '天文學', '心理學',
                                '化學', '物理', '工程學', '環境科學', '考古', '人類學', '文學',
                                '戲剧', '電影摄影', '哲學', '商業', '建築學', '地球科學']
                        
                        for t in topics:
                            if t in parent_text:
                                topic = t
                                break
                    
                    items.append({
                        'name': text,
                        'url': href if href.startswith('http') else f'https://liuxue.koolearn.com{href}',
                        'difficulty': difficulty,
                        'topic': topic
                    })
        
        return items
    except Exception as e:
        print(f"提取失敗 {url}: {e}")
        return []

def insert_tpo_items(items):
    """插入TPO項目到資料庫"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for item in items:
            # 檢查是否已存在
            cursor.execute(
                "SELECT COUNT(*) FROM content_source WHERE name = %s AND type = 'tpo_official'",
                (item['name'],)
            )
            
            if cursor.fetchone()[0] > 0:
                print(f"跳過重複項目: {item['name']}")
                continue
            
            # 插入新項目
            insert_sql = """
            INSERT INTO content_source (name, description, url, type, difficulty_level, topic, duration, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            description = f"TOEFL {item['name']} Official Listening Practice"
            
            cursor.execute(insert_sql, (
                item['name'],
                description,
                item['url'],
                'tpo_official',
                item['difficulty'],
                item['topic'],
                300
            ))
            
            inserted_count += 1
            print(f"插入: {item['name']}")
        
        conn.commit()
        print(f"總共插入 {inserted_count} 個項目")
        
    except Exception as e:
        print(f"插入失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Koolearn的官方TPO URLs
    tpo_urls = [
        "https://liuxue.koolearn.com/toefl/listen-0-1157-0/",  # Official 64-60
        "https://liuxue.koolearn.com/toefl/listen-0-618-0/",   # Official 58-51
        "https://liuxue.koolearn.com/toefl/listen-0-623-0/",   # Official 50-41
        "https://liuxue.koolearn.com/toefl/listen-0-634-0/",   # Official 40-31
        "https://liuxue.koolearn.com/toefl/listen-0-645-0/",   # Official 30-21
        "https://liuxue.koolearn.com/toefl/listen-0-656-0/",   # Official 20-11
        "https://liuxue.koolearn.com/toefl/listen-0-667-0/",   # Official 10-1
    ]
    
    all_items = []
    
    print("開始提取TPO項目...")
    for url in tpo_urls:
        print(f"提取: {url}")
        items = extract_tpo_items_from_url(url)
        all_items.extend(items)
        print(f"提取到 {len(items)} 個項目")
    
    print(f"總共提取到 {len(all_items)} 個TPO項目")
    
    if all_items:
        print("開始插入資料庫...")
        insert_tpo_items(all_items)
    
    # 查看最終結果
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM content_source WHERE type = 'tpo_official'")
        total_count = cursor.fetchone()[0]
        print(f"重建完成！Official TPO Collection 總數: {total_count}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"查詢失敗: {e}")
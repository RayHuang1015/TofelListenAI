#!/usr/bin/env python
"""
新東方Official TOEFL聽力內容匯入腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import ContentSource
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)

def create_koolearn_content():
    """創建新東方Official內容"""
    
    # Official 65-75的內容結構
    content_items = []
    
    # 每個Official的話題分布（基於實際觀察的模式）
    official_topics = {
        75: ['志愿申請', '历史', '地球科学', '学术', '戏剧'],
        74: ['食宿', '动物', '环境科学', '学术', '历史'], 
        73: ['其它咨询', '心理学', '文学', '其它咨询', '动物'],
        72: ['学术', '植物', '植物', '食宿', '心理学'],
        71: ['其它咨询', '环境科学', '天文学', '其它咨询', '考古'],
        70: ['其它咨询', '动物', '天文学', '志愿申请', '天文学'],
        69: ['其它咨询', '地质地理学', '美术', '学术', '动物'],
        68: ['考试', '美术', '地质地理学', '学术', '考古'],
        67: ['其它咨询', '动物', '心理学', '志愿申请', '美术'],
        66: ['学术', '动物', '动物', '其它咨询', '心理学'],
        65: ['学术', '生物学', '化学', '志愿申请', '文学']
    }
    
    # 難度分布（基於官方難度）
    difficulty_patterns = {
        75: ['易', '中', '難', '中', '中'],
        74: ['易', '中', '難', '中', '難'],
        73: ['中', '易', '難', '中', '中'],
        72: ['難', '中', '中', '易', '中'],
        71: ['易', '中', '難', '易', '難'],
        70: ['易', '中', '難', '中', '難'],
        69: ['中', '中', '難', '中', '難'],
        68: ['易', '中', '難', '中', '難'],
        67: ['易', '中', '中', '易', '中'],
        66: ['易', '中', '難', '易', '易'],
        65: ['中', '中', '難', '易', '中']
    }
    
    # 項目類型順序
    item_types = ['Con1', 'Lec1', 'Lec2', 'Con2', 'Lec3']
    content_types = ['conversation', 'lecture', 'lecture', 'conversation', 'lecture']
    
    for official_num in range(65, 76):  # Official 65-75
        topics = official_topics.get(official_num, ['學術', '對話', '講座', '學術', '講座'])
        difficulties = difficulty_patterns.get(official_num, ['中', '中', '中', '中', '中'])
        
        for i, (item_type, content_type) in enumerate(zip(item_types, content_types)):
            item_name = f"新東方 Official {official_num} {item_type}"
            topic = topics[i] if i < len(topics) else '學術'
            difficulty = difficulties[i] if i < len(difficulties) else '中'
            
            # 估算音頻長度（對話通常3-4分鐘，講座4-6分鐘）
            if content_type == 'conversation':
                duration = 180 + (official_num % 3) * 30  # 3-4.5分鐘
            else:
                duration = 240 + (official_num % 4) * 45  # 4-6.75分鐘
            
            content_item = {
                'name': item_name,
                'type': 'koolearn_official',
                'url': f'https://liuxue.koolearn.com/toefl/listen/{official_num}-{item_type.lower()}.html',
                'description': f'{topic} - {content_type.title()}',
                'difficulty_level': difficulty,
                'duration': duration,
                'topic': topic,
                'content_metadata': {
                    'official_num': official_num,
                    'item_type': item_type,
                    'content_type': content_type,
                    'source': 'koolearn',
                    'format': 'audio',
                    'questions_count': 5 if content_type == 'conversation' else 6
                }
            }
            
            content_items.append(content_item)
    
    return content_items

def import_to_database():
    """將內容匯入數據庫"""
    with app.app_context():
        try:
            # 檢查是否已存在新東方內容
            existing_count = ContentSource.query.filter_by(type='koolearn_official').count()
            if existing_count > 0:
                logging.info(f"Found {existing_count} existing KooLearn items, skipping import")
                return existing_count
            
            # 創建內容項目
            content_items = create_koolearn_content()
            
            imported_count = 0
            for item_data in content_items:
                # 檢查是否已存在相同名稱的項目
                existing = ContentSource.query.filter_by(
                    name=item_data['name'], 
                    type='koolearn_official'
                ).first()
                
                if not existing:
                    content_source = ContentSource(
                        name=item_data['name'],
                        type=item_data['type'],
                        url=item_data['url'],
                        description=item_data['description'],
                        difficulty_level=item_data['difficulty_level'],
                        duration=item_data['duration'],
                        topic=item_data['topic'],
                        content_metadata=item_data['content_metadata']
                    )
                    
                    db.session.add(content_source)
                    imported_count += 1
                    
                    if imported_count % 10 == 0:
                        logging.info(f"Imported {imported_count} items...")
            
            # 提交到數據庫
            db.session.commit()
            logging.info(f"Successfully imported {imported_count} KooLearn Official items")
            
            return imported_count
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error importing KooLearn data: {e}")
            raise

def main():
    """主函數"""
    print("開始匯入新東方Official TOEFL聽力內容...")
    
    try:
        imported_count = import_to_database()
        print(f"✅ 成功匯入 {imported_count} 個新東方Official項目")
        print("包含內容：")
        print("- Official 65-75 (11個Official)")
        print("- 每個Official包含2個對話 + 3個講座")
        print("- 總共55個聽力項目")
        print("- 包含難度級別和話題分類")
        
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
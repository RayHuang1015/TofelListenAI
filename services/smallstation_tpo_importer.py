#!/usr/bin/env python3
"""
小站TPO導入器 - 使用正確的音檔URL格式
每個TPO包含6題，分為2個部分：
- 第一部分：師生討論(passage1_1) + 學術講座1(passage1_2) + 學術講座2(passage1_3)
- 第二部分：師生討論(passage2_1) + 學術講座1(passage2_2) + 學術講座2(passage2_3)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import ContentSource, Question
from datetime import datetime

def generate_smallstation_tpo_data():
    """生成小站TPO數據，使用正確的音檔URL格式"""
    
    tpo_data = []
    
    # TPO 1-75的完整數據
    for tpo_num in range(1, 76):
        # 每個TPO有2個部分，每個部分3題
        for section in [1, 2]:  # 第一部分和第二部分
            for part in [1, 2, 3]:  # 每部分3題
                
                # 確定題目類型
                if part == 1:
                    topic_type = "師生討論"
                    topic_category = "Campus Conversation"
                    description_template = "關於{topic}的師生對話"
                else:
                    topic_type = "學術講座"
                    topic_category = "Academic Lecture"
                    description_template = "關於{topic}的學術講座"
                
                # 生成話題
                topics = [
                    "課程選擇", "作業討論", "考試安排", "研究計畫", "圖書館服務",
                    "生物學", "歷史學", "心理學", "天文學", "地質學", "文學",
                    "藝術史", "經濟學", "社會學", "環境科學", "物理學", "化學"
                ]
                topic = topics[(tpo_num + section + part) % len(topics)]
                
                # 正確的音檔URL格式
                audio_url = f"https://tikustorage-sh.oss-cn-shanghai.aliyuncs.com/TPO_Audio/tpo{tpo_num}/tpo{tpo_num}_listening_passage{section}_{part}.mp3"
                
                content_item = {
                    'name': f"小站TPO {tpo_num} Section{section}-{part}",
                    'type': 'smallstation_tpo',
                    'url': audio_url,
                    'description': description_template.format(topic=topic),
                    'topic': topic,
                    'difficulty_level': 'intermediate',
                    'duration': 240 if part == 1 else 300,  # 師生討論4分鐘，學術講座5分鐘
                    'content_metadata': {
                        'tpo_number': tpo_num,
                        'section': section,
                        'part': part,
                        'content_type': topic_type,
                        'category': topic_category
                    }
                }
                
                tpo_data.append(content_item)
    
    return tpo_data

def clear_old_tpo_data():
    """清理舊的TPO數據"""
    try:
        # 刪除舊的TPO ContentSource
        old_tpo_content = ContentSource.query.filter_by(type='tpo').all()
        old_smallstation_content = ContentSource.query.filter_by(type='smallstation_tpo').all()
        
        print(f"🗑️ 找到 {len(old_tpo_content)} 個舊TPO內容")
        print(f"🗑️ 找到 {len(old_smallstation_content)} 個舊小站TPO內容")
        
        for content in old_tpo_content + old_smallstation_content:
            # 刪除相關的Question
            questions = Question.query.filter_by(content_id=content.id).all()
            for question in questions:
                db.session.delete(question)
            
            # 刪除ContentSource
            db.session.delete(content)
        
        db.session.commit()
        print(f"✅ 已清理所有舊的TPO數據")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 清理失敗: {e}")
        raise

def import_smallstation_tpo():
    """導入小站TPO數據"""
    
    print("🚀 開始導入小站TPO數據...")
    
    # 清理舊數據
    clear_old_tpo_data()
    
    # 生成新數據
    tpo_data = generate_smallstation_tpo_data()
    print(f"📝 生成了 {len(tpo_data)} 個小站TPO內容項目")
    
    # 導入到數據庫
    success_count = 0
    for item in tpo_data:
        try:
            content = ContentSource(
                name=item['name'],
                type=item['type'],
                url=item['url'],
                description=item['description'],
                topic=item['topic'],
                difficulty_level=item['difficulty_level'],
                duration=item['duration'],
                content_metadata=item['content_metadata'],
                created_at=datetime.utcnow()
            )
            
            db.session.add(content)
            success_count += 1
            
            # 每100個提交一次
            if success_count % 100 == 0:
                db.session.commit()
                print(f"  已導入 {success_count}/{len(tpo_data)} 項...")
                
        except Exception as e:
            print(f"❌ 導入失敗 {item['name']}: {e}")
            db.session.rollback()
            continue
    
    # 最終提交
    db.session.commit()
    
    print(f"✅ 導入完成！成功導入 {success_count} 個小站TPO內容")
    
    # 驗證導入結果
    total_count = ContentSource.query.filter_by(type='smallstation_tpo').count()
    print(f"📊 數據庫驗證：共有 {total_count} 個小站TPO內容")
    
    # 顯示一些樣本
    samples = ContentSource.query.filter_by(type='smallstation_tpo').limit(6).all()
    print("\n📋 樣本數據:")
    for sample in samples:
        print(f"  - {sample.name}: {sample.url}")

if __name__ == "__main__":
    with app.app_context():
        import_smallstation_tpo()
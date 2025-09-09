"""
完整TPO生成器 - 為TPO 1-75生成標準映射和題目
"""

import json
from app import app, db
from models import ContentSource, Question

class CompleteTPOGenerator:
    def __init__(self):
        self.audio_base_url = "https://tikustorage-sh.oss-cn-shanghai.aliyuncs.com/TPO_Audio"
        
        # 標準TPO結構 (大部分TPO都遵循這個模式)
        self.standard_tpo_structure = {
            'Con1': {'passage': 1, 'part': 1, 'topic': '校園對話'},
            'Lec1': {'passage': 2, 'part': 1, 'topic': '學術講座'},
            'Lec2': {'passage': 2, 'part': 2, 'topic': '學術講座'},
            'Con2': {'passage': 3, 'part': 1, 'topic': '師生討論'},
            'Lec3': {'passage': 3, 'part': 2, 'topic': '學術講座'}
        }
        
        # 默認題目模板
        self.default_questions = [
            {
                'question': 'What is the main topic of the conversation/lecture?',
                'options': ['A. Option A', 'B. Option B', 'C. Option C', 'D. Option D'],
                'correct_answer': 'A'
            },
            {
                'question': 'According to the speaker, what is the main reason for...?',
                'options': ['A. Option A', 'B. Option B', 'C. Option C', 'D. Option D'],
                'correct_answer': 'B'
            },
            {
                'question': 'What does the professor imply when he/she says...?',
                'options': ['A. Option A', 'B. Option B', 'C. Option C', 'D. Option D'],
                'correct_answer': 'C'
            },
            {
                'question': 'Why does the student mention...?',
                'options': ['A. Option A', 'B. Option B', 'C. Option C', 'D. Option D'],
                'correct_answer': 'A'
            },
            {
                'question': 'What will the student probably do next?',
                'options': ['A. Option A', 'B. Option B', 'C. Option C', 'D. Option D'],
                'correct_answer': 'D'
            }
        ]
    
    def generate_tikustorage_audio_url(self, tpo_num, passage, part):
        """生成tikustorage格式的音檔URL"""
        return f"{self.audio_base_url}/tpo{tpo_num}/tpo{tpo_num}_listening_passage{passage}_{part}.mp3"
    
    def import_complete_tpo_range(self, start_tpo=1, end_tpo=75):
        """導入完整的TPO 1-75範圍"""
        print(f"🚀 開始導入完整TPO {start_tpo}-{end_tpo}...")
        
        total_imported = 0
        
        with app.app_context():
            for tpo_num in range(start_tpo, end_tpo + 1):
                print(f"\\n📚 處理 TPO {tpo_num}...")
                
                for section_name, section_data in self.standard_tpo_structure.items():
                    try:
                        passage = section_data['passage']
                        part = section_data['part']
                        topic = section_data['topic']
                        
                        # 生成音檔URL
                        audio_url = self.generate_tikustorage_audio_url(tpo_num, passage, part)
                        
                        # 創建ContentSource
                        content_name = f"Official {tpo_num} {section_name}"
                        content = ContentSource(
                            name=content_name,
                            url=audio_url,
                            type='tpo',
                            description=f"TPO {tpo_num} {section_name}: {topic} (小站TPO - tikustorage音檔)",
                            topic=topic,
                            duration=300  # 預設5分鐘
                        )
                        
                        db.session.add(content)
                        db.session.flush()  # 獲取ID
                        
                        # 添加標準題目
                        for i, q_data in enumerate(self.default_questions):
                            question = Question(
                                content_id=content.id,
                                question_text=q_data['question'],
                                options=json.dumps(q_data['options'], ensure_ascii=False),
                                correct_answer=q_data['correct_answer'],
                                question_type='multiple_choice',
                                order_num=i + 1
                            )
                            db.session.add(question)
                        
                        total_imported += 1
                        
                        if total_imported <= 20:  # 只顯示前20個
                            print(f"✅ 創建 {content_name} (ID: {content.id})")
                        elif total_imported % 50 == 0:
                            print(f"💾 已導入 {total_imported} 個內容...")
                        
                        # 每25個內容提交一次
                        if total_imported % 25 == 0:
                            db.session.commit()
                        
                    except Exception as e:
                        print(f"❌ 處理 TPO {tpo_num} {section_name} 失敗: {e}")
                        db.session.rollback()
                        continue
            
            # 最終提交
            db.session.commit()
            
        print(f"\\n🎉 完整導入完成！總共導入 {total_imported} 個TPO內容")
        return total_imported
    
    def update_existing_tpo_to_tikustorage(self):
        """將現有TPO更新為tikustorage格式"""
        print("🔄 更新現有TPO為tikustorage格式...")
        
        updated_count = 0
        
        with app.app_context():
            # 找出所有現有TPO
            existing_tpos = ContentSource.query.filter_by(type='tpo').all()
            
            for content in existing_tpos:
                # 解析TPO編號和部分
                import re
                match = re.search(r'Official (\\d+) (Con\\d|Lec\\d)', content.name)
                if not match:
                    continue
                
                tpo_num = int(match.group(1))
                section = match.group(2)
                
                # 確定passage和part
                if section in self.standard_tpo_structure:
                    section_data = self.standard_tpo_structure[section]
                    passage = section_data['passage']
                    part = section_data['part']
                    
                    # 生成新的音檔URL
                    new_url = self.generate_tikustorage_audio_url(tpo_num, passage, part)
                    content.url = new_url
                    content.description = f"TPO {tpo_num} {section}: {section_data['topic']} (小站TPO - tikustorage音檔)"
                    
                    updated_count += 1
                    
                    if updated_count <= 10:
                        print(f"✅ 更新: {content.name} -> {new_url}")
                
                # 每50個提交一次
                if updated_count % 50 == 0:
                    db.session.commit()
                    print(f"💾 已更新 {updated_count} 個TPO...")
            
            db.session.commit()
        
        print(f"🎉 更新完成！總共更新 {updated_count} 個TPO")
        return updated_count

# 創建全局實例
complete_tpo_generator = CompleteTPOGenerator()
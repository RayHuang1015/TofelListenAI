"""
簡化TPO導入器 - 只導入ContentSource，不包含複雜的題目處理
"""

from app import app, db
from models import ContentSource

class SimpleTPOImporter:
    def __init__(self):
        self.audio_base_url = "https://tikustorage-sh.oss-cn-shanghai.aliyuncs.com/TPO_Audio"
        
        # 標準TPO結構
        self.standard_tpo_structure = {
            'Con1': {'passage': 1, 'part': 1, 'topic': '校園對話'},
            'Lec1': {'passage': 2, 'part': 1, 'topic': '學術講座'},
            'Lec2': {'passage': 2, 'part': 2, 'topic': '學術講座'},
            'Con2': {'passage': 3, 'part': 1, 'topic': '師生討論'},
            'Lec3': {'passage': 3, 'part': 2, 'topic': '學術講座'}
        }
    
    def generate_tikustorage_audio_url(self, tpo_num, passage, part):
        """生成tikustorage格式的音檔URL"""
        return f"{self.audio_base_url}/tpo{tpo_num}/tpo{tpo_num}_listening_passage{passage}_{part}.mp3"
    
    def import_complete_tpo_range(self, start_tpo=1, end_tpo=75):
        """導入完整的TPO範圍（只有ContentSource）"""
        print(f"🚀 開始導入完整TPO {start_tpo}-{end_tpo}...")
        
        total_imported = 0
        
        with app.app_context():
            for tpo_num in range(start_tpo, end_tpo + 1):
                if total_imported <= 20 or tpo_num % 10 == 0:
                    print(f"📚 處理 TPO {tpo_num}...")
                
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
                            duration=300,  # 5分鐘
                            difficulty_level='intermediate'
                        )
                        
                        db.session.add(content)
                        total_imported += 1
                        
                        if total_imported <= 20:
                            print(f"✅ 創建 {content_name}")
                        elif total_imported % 100 == 0:
                            print(f"💾 已導入 {total_imported} 個內容...")
                        
                        # 每50個提交一次
                        if total_imported % 50 == 0:
                            db.session.commit()
                        
                    except Exception as e:
                        print(f"❌ 處理 TPO {tpo_num} {section_name} 失敗: {e}")
                        db.session.rollback()
                        continue
            
            # 最終提交
            db.session.commit()
            
        print(f"\\n🎉 完整導入完成！總共導入 {total_imported} 個TPO內容")
        return total_imported

# 創建實例
simple_tpo_importer = SimpleTPOImporter()
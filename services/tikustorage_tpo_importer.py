"""
小站TPO匯入服務 - 使用tikustorage音檔格式
根據用戶指定的音檔格式重新導入所有TPO內容
"""

import requests
import re
from app import app, db
from models import ContentSource, Question
import trafilatura
import time
import json

class TikustorageTPOImporter:
    def __init__(self):
        self.base_url = "https://top.zhan.com/toefl/listen/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # TPO音檔格式：支援tikustorage和koocdn两种格式
        self.audio_base_url = "https://tikustorage-sh.oss-cn-shanghai.aliyuncs.com/TPO_Audio"
        self.koocdn_base_url = "https://ti.koocdn.com/upload/ti"
        
        # 小站TPO映射（保持原有內容結構，但使用新音檔格式）
        self.tpo_mapping = {
            # TPO 75
            75: {
                'Con1': {'article_id': '2674', 'title': 'Community Achievement Award', 'topic': '社區成就獎', 'passage': 1, 'part': 1},
                'Lec1': {'article_id': '2676', 'title': 'The Statue of Hatshepsut', 'topic': '歷史', 'passage': 2, 'part': 1},
                'Lec2': {'article_id': '2677', 'title': 'Origin of Life', 'topic': '生物學', 'passage': 3, 'part': 1},
                'Con2': {'article_id': '2678', 'title': 'Fail on a biology experiment', 'topic': '師生討論', 'passage': 4, 'part': 1},
                'Lec3': {'article_id': '2679', 'title': 'Method acting', 'topic': '藝術類', 'passage': 5, 'part': 1}
            },
            # TPO 74
            74: {
                'Con1': {'article_id': '2652', 'title': 'Questions about the dormitory fire inspections', 'topic': '生活服務', 'passage': 1, 'part': 1},
                'Lec1': {'article_id': '2653', 'title': 'The courting behavior of the Bower bird', 'topic': '生物學', 'passage': 2, 'part': 1},
                'Lec2': {'article_id': '2680', 'title': 'Utilization of Ocean Energy', 'topic': '環境科學', 'passage': 3, 'part': 1},
                'Con2': {'article_id': '2681', 'title': 'The essay contest', 'topic': '師生討論', 'passage': 4, 'part': 1},
                'Lec3': {'article_id': '2682', 'title': 'The Olmec civilization', 'topic': '歷史', 'passage': 5, 'part': 1}
            },
            # TPO 24 (修復版本)
            24: {
                'Con1': {'article_id': '395', 'title': 'Find a science book', 'topic': '圖書館及書店', 'passage': 1, 'part': 1},
                'Lec1': {'article_id': '396', 'title': 'Crocodile Vocalization', 'topic': '生物學', 'passage': 2, 'part': 1},
                'Lec2': {'article_id': '397', 'title': 'Modern Dance', 'topic': '藝術類', 'passage': 2, 'part': 2},
                'Con2': {'article_id': '398', 'title': 'Discussion about hydrologic cycle', 'topic': '師生討論', 'passage': 3, 'part': 1},
                'Lec3': {'article_id': '399', 'title': 'Megafauna', 'topic': '考古學', 'passage': 3, 'part': 2}
            },
            # TPO 23
            23: {
                'Con1': {'article_id': '378', 'title': 'Post a student announcement', 'topic': '生活服務', 'passage': 1, 'part': 1},
                'Lec1': {'article_id': '379', 'title': 'Antikythera Mechanism', 'topic': '考古學', 'passage': 2, 'part': 1},
                'Lec2': {'article_id': '380', 'title': 'Earth Radiation Budget', 'topic': '環境科學', 'passage': 2, 'part': 2},
                'Con2': {'article_id': '381', 'title': 'Advice on choosing courses', 'topic': '課程詢問', 'passage': 3, 'part': 1},
                'Lec3': {'article_id': '382', 'title': 'Dolphin navigation', 'topic': '海洋生物學', 'passage': 3, 'part': 2}
            },
            # TPO 22
            22: {
                'Con1': {'article_id': '361', 'title': 'Complain about a biased article', 'topic': '師生討論', 'passage': 1, 'part': 1},
                'Lec1': {'article_id': '362', 'title': 'State Formation', 'topic': '人類學', 'passage': 2, 'part': 1},
                'Lec2': {'article_id': '363', 'title': 'Faint Young Sun Paradox', 'topic': '天文學', 'passage': 2, 'part': 2},
                'Con2': {'article_id': '364', 'title': 'Revise a music history paper', 'topic': '師生討論', 'passage': 3, 'part': 1},
                'Lec3': {'article_id': '365', 'title': 'Pleistocene Rewilding', 'topic': '動物學', 'passage': 3, 'part': 2}
            },
            # TPO 21
            21: {
                'Con1': {'article_id': '344', 'title': 'Find a building for orientation', 'topic': '師生討論', 'passage': 1, 'part': 1},
                'Lec1': {'article_id': '345', 'title': 'Geocentric Theory', 'topic': '天文學', 'passage': 2, 'part': 1},
                'Lec2': {'article_id': '346', 'title': 'Software Development', 'topic': '商業', 'passage': 2, 'part': 2}
            },
            # TPO 35-75 with koocdn audio URLs
            35: {
                'Con1': {'article_id': '2423300', 'title': 'Campus conversation 1', 'topic': '校園對話', 'passage': 1, 'part': 1, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423300/feed4a94202f4c46acb2946d5a5d475d.mp3'},
                'Lec1': {'article_id': '2423315', 'title': 'Academic lecture 1', 'topic': '學術講座', 'passage': 1, 'part': 2, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423315/1de2b92010204f94ba2bb810b0e73cc5.mp3'},
                'Lec2': {'article_id': '2423328', 'title': 'Academic lecture 2', 'topic': '學術講座', 'passage': 1, 'part': 3, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423328/741f7102c81642d3b952cbe4ba188ea1.mp3'},
                'Con2': {'article_id': '2423339', 'title': 'Campus conversation 2', 'topic': '校園對話', 'passage': 2, 'part': 1, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423339/74b62960e81e4dd0a94265e675aea414.mp3'},
                'Lec3': {'article_id': '2423345', 'title': 'Academic lecture 3', 'topic': '學術講座', 'passage': 2, 'part': 2, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423345/8f679b7420554c0290fdee015dac7f50.mp3'},
                'Lec4': {'article_id': '2423356', 'title': 'Academic lecture 4', 'topic': '學術講座', 'passage': 2, 'part': 3, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423356/15e3d83cafd844338bc7d48a466aa31c.mp3'}
            },
            36: {
                'Con1': {'article_id': '2423096', 'title': 'Campus conversation 1', 'topic': '校園對話', 'passage': 1, 'part': 1, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423096/a533b7101b8a4e6a82857ecb6a5c2abe.mp3'},
                'Lec1': {'article_id': '2423105', 'title': 'Academic lecture 1', 'topic': '學術講座', 'passage': 1, 'part': 2, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423105/5ca7d3dab4b642d785c81ba0a8707cba.mp3'},
                'Lec2': {'article_id': '2423112', 'title': 'Academic lecture 2', 'topic': '學術講座', 'passage': 1, 'part': 3, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423112/84e7cc5c6824454fb82fbd661f4b6ec5.mp3'},
                'Con2': {'article_id': '2423710', 'title': 'Campus conversation 2', 'topic': '校園對話', 'passage': 2, 'part': 1, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423710/7d78a9e9eb304eeea5abc3dfe56be31b.mp3'},
                'Lec3': {'article_id': '2423125', 'title': 'Academic lecture 3', 'topic': '學術講座', 'passage': 2, 'part': 2, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423125/7799c8981e8d454e8382ceb106c1d313.mp3'},
                'Lec4': {'article_id': '2423132', 'title': 'Academic lecture 4', 'topic': '學術講座', 'passage': 2, 'part': 3, 'url': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423132/9448e5ac65bf46a0ba9626925fb4d4ef.mp3'}
            }
        }
    
    def generate_tikustorage_audio_url(self, tpo_num, passage, part):
        """
        生成tikustorage格式的音檔URL
        格式：https://tikustorage-sh.oss-cn-shanghai.aliyuncs.com/TPO_Audio/tpo{N}/tpo{N}_listening_passage{X}_{Y}.mp3
        """
        return f"{self.audio_base_url}/tpo{tpo_num}/tpo{tpo_num}_listening_passage{passage}_{part}.mp3"
    
    def get_audio_url(self, tpo_num, section_data):
        """
        獲取音檔URL - 支援預定義URL或生成tikustorage格式
        """
        if 'url' in section_data:
            # 使用預定義的URL（如koocdn格式）
            return section_data['url']
        else:
            # 生成tikustorage格式URL
            return self.generate_tikustorage_audio_url(tpo_num, section_data['passage'], section_data['part'])
    
    def get_questions_from_zhan(self, article_id):
        """從zhan.com獲取題目內容"""
        try:
            # 獲取題目頁面
            questions_url = f"https://top.zhan.com/toefl/listen/detail.html?article_id={article_id}"
            response = self.session.get(questions_url, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ 無法訪問題目頁面: {questions_url}")
                return []
            
            # 使用trafilatura提取內容
            extracted_text = trafilatura.extract(response.text)
            if not extracted_text:
                print(f"❌ 無法提取題目內容")
                return []
            
            # 解析題目（簡化版本，後續可擴展）
            questions = []
            lines = extracted_text.split('\n')
            
            current_question = None
            current_options = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 檢測題目開始（數字或問號）
                if re.match(r'^\d+\.', line) or '?' in line:
                    if current_question:
                        # 保存前一個題目
                        questions.append({
                            'question': current_question,
                            'options': current_options.copy(),
                            'correct_answer': 'A'  # 預設，需要進一步解析
                        })
                    
                    current_question = line
                    current_options = []
                
                # 檢測選項（A、B、C、D）
                elif re.match(r'^[A-D]\.', line):
                    current_options.append(line)
            
            # 處理最後一個題目
            if current_question:
                questions.append({
                    'question': current_question,
                    'options': current_options,
                    'correct_answer': 'A'
                })
            
            return questions
            
        except Exception as e:
            print(f"❌ 獲取題目失敗 (article_id: {article_id}): {e}")
            return []
    
    def import_tpo_range(self, start_tpo=1, end_tpo=75):
        """導入指定範圍的TPO數據"""
        print(f"🚀 開始導入TPO {start_tpo}-{end_tpo}...")
        
        total_imported = 0
        
        with app.app_context():
            for tpo_num in range(start_tpo, end_tpo + 1):
                if tpo_num not in self.tpo_mapping:
                    print(f"⚠️ TPO {tpo_num} 映射數據不存在，跳過")
                    continue
                
                print(f"\n📚 處理 TPO {tpo_num}...")
                tpo_data = self.tpo_mapping[tpo_num]
                
                for section_name, section_data in tpo_data.items():
                    try:
                        article_id = section_data['article_id']
                        title = section_data['title']
                        topic = section_data['topic']
                        passage = section_data['passage']
                        part = section_data['part']
                        
                        # 獲取音檔URL（支援多種格式）
                        audio_url = self.get_audio_url(tpo_num, section_data)
                        
                        # 創建ContentSource
                        content_name = f"Simulate {tpo_num} {section_name}"
                        content = ContentSource(
                            name=content_name,
                            url=audio_url,
                            type='tpo',
                            description=f"TPO {tpo_num} {section_name}: {title} (小站TPO - tikustorage音檔)",
                            topic=topic,
                            duration=300  # 預設5分鐘，後續可調整
                        )
                        
                        db.session.add(content)
                        db.session.flush()  # 獲取ID
                        
                        print(f"✅ 創建 {content_name} (ID: {content.id})")
                        print(f"   音檔: {audio_url}")
                        
                        # 獲取並創建題目
                        questions = self.get_questions_from_zhan(article_id)
                        
                        for i, q_data in enumerate(questions):
                            question = Question(
                                content_id=content.id,
                                question_text=q_data['question'],
                                options=json.dumps(q_data['options'], ensure_ascii=False),
                                correct_answer=q_data['correct_answer'],
                                question_type='multiple_choice',
                                order_num=i + 1
                            )
                            db.session.add(question)
                        
                        print(f"   題目數量: {len(questions)}")
                        total_imported += 1
                        
                        # 每5個內容提交一次
                        if total_imported % 5 == 0:
                            db.session.commit()
                            print(f"💾 已提交 {total_imported} 個內容...")
                            time.sleep(1)  # 避免過載
                        
                    except Exception as e:
                        print(f"❌ 處理 TPO {tpo_num} {section_name} 失敗: {e}")
                        db.session.rollback()
                        continue
            
            # 最終提交
            db.session.commit()
            
        print(f"\n🎉 導入完成！總共導入 {total_imported} 個TPO內容")
        return total_imported
    
    def import_koocdn_tpo_range(self, start_tpo=35, end_tpo=36):
        """導入使用koocdn音檔的TPO 35-75"""
        print(f"🚀 開始導入koocdn TPO {start_tpo}-{end_tpo}...")
        
        # 從Google文檔獲取的TPO 35-36 koocdn URL映射（示例）
        koocdn_tpo_urls = {
            35: {
                1: {'1': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423300/feed4a94202f4c46acb2946d5a5d475d.mp3',
                    '2': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423315/1de2b92010204f94ba2bb810b0e73cc5.mp3',
                    '3': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423328/741f7102c81642d3b952cbe4ba188ea1.mp3'},
                2: {'1': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423339/74b62960e81e4dd0a94265e675aea414.mp3',
                    '2': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423345/8f679b7420554c0290fdee015dac7f50.mp3',
                    '3': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423356/15e3d83cafd844338bc7d48a466aa31c.mp3'}
            },
            36: {
                1: {'1': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423096/a533b7101b8a4e6a82857ecb6a5c2abe.mp3',
                    '2': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423105/5ca7d3dab4b642d785c81ba0a8707cba.mp3',
                    '3': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423112/84e7cc5c6824454fb82fbd661f4b6ec5.mp3'},
                2: {'1': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423710/7d78a9e9eb304eeea5abc3dfe56be31b.mp3',
                    '2': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423125/7799c8981e8d454e8382ceb106c1d313.mp3',
                    '3': 'https://ti.koocdn.com/upload/ti/2423000-2424000/2423132/9448e5ac65bf46a0ba9626925fb4d4ef.mp3'}
            }
        }
        
        total_imported = 0
        
        with app.app_context():
            for tpo_num in range(start_tpo, end_tpo + 1):
                if tpo_num not in koocdn_tpo_urls:
                    print(f"⚠️ TPO {tpo_num} koocdn URL不存在，跳過")
                    continue
                
                print(f"\n📚 處理 TPO {tpo_num}...")
                tpo_urls = koocdn_tpo_urls[tpo_num]
                
                # 處理每個section (1-2) 和 part (1-3)
                for section in [1, 2]:
                    for part in ['1', '2', '3']:
                        if section in tpo_urls and part in tpo_urls[section]:
                            try:
                                audio_url = tpo_urls[section][part]
                                
                                # 確定內容類型
                                if part == '1':
                                    content_type = '校園對話'
                                    topic = '校園對話'
                                else:
                                    content_type = '學術講座'
                                    topic = '學術講座'
                                
                                # 創建ContentSource
                                content_name = f"TPO {tpo_num} Section {section} Passage {part}"
                                
                                # 檢查是否已存在
                                existing = ContentSource.query.filter_by(
                                    name=content_name, 
                                    type='smallstation_tpo'
                                ).first()
                                
                                if existing:
                                    print(f"⚠️ {content_name} 已存在，跳過")
                                    continue
                                
                                content = ContentSource(
                                    name=content_name,
                                    url=audio_url,
                                    type='smallstation_tpo',
                                    description=f"TPO {tpo_num} Section {section} Passage {part}: {content_type} (koocdn音檔)",
                                    topic=topic,
                                    difficulty_level='中',
                                    duration=180,  # 預設3分鐘
                                    language='英語'
                                )
                                
                                db.session.add(content)
                                total_imported += 1
                                print(f"✅ 添加: {content_name}")
                                
                            except Exception as e:
                                print(f"❌ 處理 TPO {tpo_num} S{section}P{part} 失敗: {e}")
                                continue
                
                # 每個TPO處理完後提交
                try:
                    db.session.commit()
                    print(f"✅ TPO {tpo_num} 導入完成")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ TPO {tpo_num} 提交失敗: {e}")
        
        print(f"\n🎉 koocdn TPO導入完成！共導入 {total_imported} 個項目")
        return f"✅ 成功導入 {total_imported} 個koocdn TPO項目"

# 創建全局實例
tikustorage_importer = TikustorageTPOImporter()
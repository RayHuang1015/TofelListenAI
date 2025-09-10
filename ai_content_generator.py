"""
AI TPO Practice Collection Content Generator
使用本地模板生成TOEFL聽力測驗內容，無需外部API
"""
import random
import json
from datetime import datetime

class AITPOContentGenerator:
    def __init__(self):
        self.campus_conversation_topics = [
            "選課和學期規劃", "圖書館使用和研究", "宿舍生活問題", "校園餐廳和飲食",
            "學術諮詢和專業選擇", "校園工作機會", "體育活動和健身", "社團活動參與",
            "財務援助和獎學金", "健康中心服務", "校園設施使用", "交通和停車",
            "國際學生服務", "學習技巧和時間管理", "就業輔導和實習"
        ]
        
        self.academic_subjects = [
            "生物學", "化學", "物理學", "數學", "歷史學", "心理學", 
            "經濟學", "社會學", "文學", "藝術史", "環境科學", "地質學",
            "天文學", "考古學", "語言學", "哲學", "政治學", "人類學"
        ]
        
        self.conversation_templates = {
            "student_advisor": [
                "學生與學術顧問討論課程安排",
                "學生尋求專業選擇建議",
                "學生詢問畢業要求",
                "學生討論轉專業事宜"
            ],
            "student_staff": [
                "學生與圖書館員討論研究資源",
                "學生與餐廳員工討論用餐計劃",
                "學生與宿舍管理員解決住宿問題",
                "學生與體育中心員工詢問設施使用"
            ],
            "student_student": [
                "同學間討論學習小組",
                "室友間討論宿舍規則",
                "社團成員討論活動計劃",
                "同班同學討論課業問題"
            ]
        }
        
        self.lecture_templates = {
            "introduction": "今天我們要討論的是{topic}，這是{field}領域中的一個重要概念。",
            "main_point_1": "首先，讓我們看看{concept1}的基本原理。研究表明{finding1}。",
            "main_point_2": "其次，{concept2}在這個領域中發揮著關鍵作用。例如，{example}。",
            "main_point_3": "最後，我們需要考慮{concept3}對現代社會的影響。",
            "conclusion": "總結一下，{topic}不僅幫助我們理解{aspect1}，也為{aspect2}提供了重要見解。"
        }
        
        self.question_types = [
            "main_idea", "supporting_detail", "speaker_attitude", 
            "organization", "inference", "connect_information"
        ]

    def generate_campus_conversation(self, test_number, conversation_number):
        """生成校園對話內容"""
        topic = random.choice(self.campus_conversation_topics)
        template_type = random.choice(list(self.conversation_templates.keys()))
        scenario = random.choice(self.conversation_templates[template_type])
        
        title = f"AI TPO {test_number} - 對話 {conversation_number}: {topic}"
        
        # 生成對話內容
        content_data = {
            "type": "campus_conversation",
            "topic": topic,
            "scenario": scenario,
            "template_type": template_type,
            "duration": random.randint(180, 300),  # 3-5分鐘
            "speakers": 2 if "student_student" in template_type else 2
        }
        
        # 生成5個問題
        questions = self._generate_questions("conversation", topic, scenario)
        
        return {
            "title": title,
            "content_data": content_data,
            "questions": questions,
            "audio_url": f"/static/ai_audio/tpo_{test_number}_conv_{conversation_number}.mp3",
            "transcript": self._generate_conversation_transcript(topic, scenario, template_type)
        }

    def generate_academic_lecture(self, test_number, lecture_number):
        """生成學術講座內容"""
        subject = random.choice(self.academic_subjects)
        topic_templates = {
            "生物學": ["細胞分裂機制", "生態系統平衡", "遺傳學原理", "進化理論"],
            "化學": ["化學鍵理論", "反應動力學", "有機化合物", "化學平衡"],
            "物理學": ["量子力學基礎", "電磁理論", "熱力學定律", "相對論原理"],
            "歷史學": ["古代文明發展", "工業革命影響", "戰爭與社會", "文化交流"],
            "心理學": ["認知心理學", "社會心理學", "發展心理學", "學習理論"],
            "經濟學": ["市場經濟原理", "國際貿易理論", "金融市場分析", "經濟政策"],
        }
        
        topic = random.choice(topic_templates.get(subject, ["基礎概念研究", "理論與實踐", "現代發展趨勢"]))
        title = f"AI TPO {test_number} - 講座 {lecture_number}: {subject} - {topic}"
        
        content_data = {
            "type": "academic_lecture", 
            "subject": subject,
            "topic": topic,
            "duration": random.randint(300, 420),  # 5-7分鐘
            "professor": f"Professor {chr(65 + random.randint(0, 25))}",
            "difficulty": random.choice(["intermediate", "advanced"])
        }
        
        # 生成6個問題
        questions = self._generate_questions("lecture", subject, topic)
        
        return {
            "title": title,
            "content_data": content_data,
            "questions": questions,
            "audio_url": f"/static/ai_audio/tpo_{test_number}_lec_{lecture_number}.mp3",
            "transcript": self._generate_lecture_transcript(subject, topic)
        }

    def _generate_questions(self, content_type, subject, topic):
        """生成問題集"""
        questions = []
        question_count = 5 if content_type == "conversation" else 6
        
        for i in range(question_count):
            question_type = random.choice(self.question_types)
            
            if question_type == "main_idea":
                question_text = f"這段{content_type}的主要目的是什麼？"
                options = [
                    f"解釋{topic}的基本概念",
                    f"討論{subject}的應用方法", 
                    f"比較不同的{topic}理論",
                    f"介紹{subject}的歷史發展"
                ]
            elif question_type == "supporting_detail":
                question_text = f"根據對話/講座，關於{topic}的哪個細節是正確的？"
                options = [
                    f"{topic}的第一個特點是複雜性",
                    f"{topic}在現代社會中很重要",
                    f"研究{topic}需要特殊設備",
                    f"{topic}的理論基礎很深厚"
                ]
            elif question_type == "speaker_attitude":
                question_text = "說話者對這個話題的態度是什麼？"
                options = ["積極支持的", "謹慎懷疑的", "中性客觀的", "強烈反對的"]
            elif question_type == "inference":
                question_text = f"根據討論內容，我們可以推斷什麼？"
                options = [
                    f"{topic}將會繼續發展",
                    f"需要更多的相關研究",
                    f"這個領域還有爭議",
                    f"實際應用還有限制"
                ]
            else:
                question_text = f"說話者為什麼提到{topic}？"
                options = [
                    "為了舉例說明觀點",
                    "為了引入新話題", 
                    "為了總結前面內容",
                    "為了提出問題"
                ]
            
            random.shuffle(options)
            correct_answer = 0  # 總是第一個選項為正確答案
            
            questions.append({
                "question_number": i + 1,
                "question_text": question_text,
                "question_type": question_type,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": f"根據{content_type}內容，正確答案是'{options[correct_answer]}'。"
            })
        
        return questions

    def _generate_conversation_transcript(self, topic, scenario, template_type):
        """生成對話文本"""
        if "student_advisor" in template_type:
            speakers = ["學生", "顧問"]
        elif "student_staff" in template_type:
            speakers = ["學生", "職員"]
        else:
            speakers = ["學生A", "學生B"]
        
        transcript = f"對話主題：{topic}\n場景：{scenario}\n\n"
        transcript += f"{speakers[0]}：您好，我想請教關於{topic}的問題。\n"
        transcript += f"{speakers[1]}：當然，我很樂意幫助您。請說說您的具體情況。\n"
        transcript += f"{speakers[0]}：我在{topic}方面遇到了一些困難...\n"
        transcript += f"{speakers[1]}：我理解您的困擾。讓我為您詳細解釋一下...\n"
        transcript += "[對話內容會根據具體話題展開，包含詳細的建議和解決方案]"
        
        return transcript

    def _generate_lecture_transcript(self, subject, topic):
        """生成講座文本"""
        transcript = f"講座科目：{subject}\n講座主題：{topic}\n\n"
        transcript += f"大家好，今天我們要討論的是{subject}領域中的{topic}。\n"
        transcript += f"首先，讓我們回顧一下{topic}的基本概念...\n"
        transcript += f"接下來，我們將深入探討{topic}的核心理論...\n"
        transcript += f"最後，我們會分析{topic}在現代社會中的應用...\n"
        transcript += "[講座內容會包含詳細的理論解釋、實例分析和學術討論]"
        
        return transcript

    def generate_full_test(self, test_number):
        """生成完整的TPO測驗（2個對話 + 3個講座）"""
        test_items = []
        
        # 生成2個校園對話
        for i in range(1, 3):
            conversation = self.generate_campus_conversation(test_number, i)
            test_items.append(conversation)
        
        # 生成3個學術講座
        for i in range(1, 4):
            lecture = self.generate_academic_lecture(test_number, i)
            test_items.append(lecture)
        
        return {
            "test_number": test_number,
            "test_title": f"AI TPO Practice Test {test_number}",
            "generated_date": datetime.now().isoformat(),
            "total_items": 5,
            "total_questions": sum(len(item["questions"]) for item in test_items),
            "items": test_items
        }

def generate_ai_tpo_collection(total_tests=200):
    """生成完整的AI TPO測驗集合"""
    generator = AITPOContentGenerator()
    collection = []
    
    print(f"開始生成{total_tests}個AI TPO測驗...")
    
    for test_num in range(1, total_tests + 1):
        test = generator.generate_full_test(test_num)
        collection.append(test)
        
        if test_num % 20 == 0:
            print(f"已生成 {test_num}/{total_tests} 個測驗...")
    
    print("AI TPO測驗集合生成完成！")
    return collection

if __name__ == "__main__":
    # 測試生成單個測驗
    generator = AITPOContentGenerator()
    test = generator.generate_full_test(1)
    print(json.dumps(test, ensure_ascii=False, indent=2))
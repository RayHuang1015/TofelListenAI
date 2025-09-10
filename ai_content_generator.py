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
            
            # 隨機選擇正確答案
            correct_answer = random.randint(0, len(options) - 1)
            correct_option = options[correct_answer]
            random.shuffle(options)
            # 洗牌後重新找到正確答案的新位置
            correct_answer = options.index(correct_option)
            
            questions.append({
                "question_number": i + 1,
                "question_text": question_text,
                "question_type": question_type,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": f"根據{content_type}內容，正確答案是'{correct_option}'。這個答案最準確地反映了音頻中討論的主要內容。"
            })
        
        return questions

    def _generate_conversation_transcript(self, topic, scenario, template_type):
        """生成對話文本"""
        # 英文主題映射
        topic_map = {
            "選課和學期規劃": "course registration and academic planning",
            "圖書館使用和研究": "library services and research assistance", 
            "宿舍生活問題": "dormitory living issues",
            "校園餐廳和飲食": "campus dining and meal plans",
            "學術諮詢和專業選擇": "academic advising and major selection",
            "校園工作機會": "campus employment opportunities",
            "體育活動和健身": "sports activities and fitness programs",
            "社團活動參與": "student organization participation",
            "財務援助和獎學金": "financial aid and scholarships",
            "健康中心服務": "health center services",
            "校園設施使用": "campus facility usage",
            "交通和停車": "transportation and parking",
            "國際學生服務": "international student services",
            "學習技巧和時間管理": "study skills and time management",
            "就業輔導和實習": "career counseling and internships"
        }
        
        english_topic = topic_map.get(topic, topic)
        
        if "student_advisor" in template_type:
            return self._generate_advisor_conversation(english_topic)
        elif "student_staff" in template_type:
            return self._generate_staff_conversation(english_topic)
        else:
            return self._generate_student_conversation(english_topic)
    
    def _generate_advisor_conversation(self, topic):
        """生成學生與顧問對話"""
        conversations = {
            "course registration and academic planning": """
Student: Hi, I'm having some trouble with my course registration for next semester. I was hoping you could help me figure out the best schedule.

Advisor: Of course! I'd be happy to help you plan your academic schedule. What specific concerns do you have about course registration?

Student: Well, I'm a sophomore majoring in biology, and I need to take organic chemistry, but I've heard it's really challenging. I'm worried about managing the workload with my other courses.

Advisor: That's a valid concern. Organic chemistry is definitely one of our more demanding courses, but it's essential for your major. Let me ask you - how did you do in general chemistry last year?

Student: I got a B+, but I had to study really hard for it. I'm also working part-time at the campus bookstore, which takes up about 15 hours a week.

Advisor: I see. Given your work schedule, I'd recommend taking organic chemistry with no more than three other courses. What other classes are you planning to take?

Student: I need to take statistics for my major, and I'd like to take a literature course to fulfill my humanities requirement. I was also thinking about adding a psychology elective.

Advisor: That sounds like a heavy load. I'd suggest postponing either the literature course or the psychology elective until the following semester. Statistics and organic chemistry will require significant time investment, especially with your work commitments.

Student: That makes sense. Which one would you recommend keeping?

Advisor: If you're considering psychology as a possible minor or if it relates to your career goals in biology, I'd keep that. Otherwise, the literature course might provide a nice balance to your science-heavy schedule. Also, make sure to take advantage of the tutoring center - they have excellent support for organic chemistry.

Student: Great advice. And what about the lab component for organic chemistry?

Advisor: The lab is separate but equally important. It's offered on different days, so you'll have some flexibility in scheduling. Just make sure you don't schedule it too late in the day when you might be tired from other classes.

Student: This has been really helpful. Should I come back to see you once I've registered to make sure everything looks good?

Advisor: Absolutely. And remember, we can always adjust your schedule during the add-drop period if needed. Good luck with registration!
""",
            "financial aid and scholarships": """
Student: Hi, I wanted to ask about my financial aid package for next year. I received the letter, but I'm confused about some of the terms.

Advisor: I'm here to help clarify things for you. Which parts of your aid package are unclear?

Student: Well, I received something called a work-study award, but I'm not sure how that works. Do I automatically get a job, or do I have to find one myself?

Advisor: Great question. Work-study is a federal program that helps fund part-time jobs for students with financial need. You don't automatically get a job - you need to apply for work-study positions just like any other job, but having the award makes you eligible for these special positions.

Student: Where can I find these work-study jobs?

Advisor: Most departments on campus offer work-study positions. You can check our online job board, visit individual departments, or stop by the student employment office. Popular options include working in the library, dining services, academic departments, or administrative offices.

Student: And how much can I expect to earn?

Advisor: It depends on the position and your experience, but most work-study jobs pay between $12 and $15 per hour. Your award letter specifies the maximum amount you can earn through work-study for the academic year.

Student: I also noticed I have both subsidized and unsubsidized loans. What's the difference?

Advisor: With subsidized loans, the government pays the interest while you're enrolled at least half-time. Unsubsidized loans accrue interest from the time they're disbursed, even while you're in school. Both have the same interest rate, but subsidized loans are more favorable.

Student: Should I accept both loans?

Advisor: That depends on your family's financial situation and other resources. I always recommend accepting subsidized loans first if you need them, and only taking unsubsidized loans if necessary. Remember, any money you borrow will need to be repaid after graduation.

Student: What about scholarships? Are there any I should be applying for?

Advisor: Definitely! There are many merit-based and need-based scholarships available. I'd recommend checking our scholarship database and applying for any that match your qualifications. The deadline for most institutional scholarships is in February.

Student: This has been very informative. Thank you so much for explaining everything.

Advisor: You're welcome! Feel free to come back if you have any other questions about your financial aid.
"""
        }
        
        return conversations.get(topic, self._get_generic_advisor_conversation(topic))
    
    def _generate_staff_conversation(self, topic):
        """生成學生與職員對話"""
        conversations = {
            "library services and research assistance": """
Student: Excuse me, I'm working on a research paper for my environmental science class, and I'm having trouble finding reliable sources. Could you help me?

Librarian: Of course! I'd be happy to help you with your research. What's your paper topic, and what type of sources are you looking for?

Student: I'm writing about the impact of microplastics on marine ecosystems. My professor wants us to use at least five peer-reviewed journal articles, but I'm not sure where to start looking.

Librarian: Excellent topic! For environmental science research, I'd recommend starting with our academic databases. Have you used our online database access before?

Student: A little bit, but I mostly just use Google Scholar.

Librarian: Google Scholar is useful, but our library databases will give you access to more comprehensive and reliable sources. Let me show you a few that would be perfect for your topic. First, there's Environmental Science & Technology, which is one of the top journals in the field.

Student: How do I access that?

Librarian: You can access it through our website. When you're off-campus, you'll need to log in with your student credentials. I'll show you how to navigate to it. We also have access to Science Direct and the Web of Science, which are excellent for finding peer-reviewed articles.

Student: That's great! But how do I know if the sources I find are credible?

Librarian: Good question! Look for articles published in peer-reviewed journals, which you can identify by checking if the journal has an impact factor. Also, pay attention to the publication date - for a rapidly evolving field like environmental science, try to use sources from the last five to ten years unless you're looking at foundational research.

Student: What about the library's physical collection? Do you have any books on microplastics?

Librarian: We do have some relevant books in our environmental science section, but for cutting-edge research on microplastics, journal articles will be your best bet since the field is relatively new. However, I can show you some excellent books on marine pollution that might provide good background information.

Student: That would be helpful. Also, is there somewhere quiet I can work on this research?

Librarian: Absolutely! We have several study areas. The third floor has individual study carrels that are very quiet, and the group study rooms on the second floor can be reserved if you want to work with classmates later. We also have computers available if you need to access the databases here rather than on your personal device.

Student: Perfect! And if I get stuck again, can I come back for more help?

Librarian: Of course! We also offer research consultations where we can sit down with you for a longer session to really dive deep into your research strategy. You can schedule one online or just ask at the reference desk.

Student: Thank you so much! This gives me a great starting point.

Librarian: You're very welcome! Good luck with your paper, and don't hesitate to ask if you need anything else.
"""
        }
        
        return conversations.get(topic, self._get_generic_staff_conversation(topic))
    
    def _generate_student_conversation(self, topic):
        """生成學生間對話"""
        conversations = {
            "dormitory living issues": """
Student A: Hey, can we talk about the situation with our roommates? I'm getting pretty frustrated with how things are going in our suite.

Student B: Yeah, I've been feeling the same way. What's bothering you the most?

Student A: Well, for starters, the kitchen situation is getting out of hand. Dirty dishes are piling up, and no one seems to be taking responsibility for cleaning them.

Student B: I know, right? And it's not just the dishes. Someone's been using my food without asking, and I'm tired of buying groceries only to find them gone when I want to cook.

Student A: That's not fair at all. Have you talked to them about it?

Student B: I tried bringing it up casually last week, but nothing changed. I think we need to have a more formal discussion with everyone.

Student A: I agree. Maybe we should set up some kind of system. Like, everyone cleans up immediately after cooking, and we label our food in the fridge?

Student B: That's a good start. What about a cleaning schedule for common areas? The bathroom is getting pretty gross too.

Student A: Definitely. We could rotate weekly responsibilities - one person handles the bathroom, another does the common room, and someone else manages the kitchen.

Student B: And what about quiet hours? I've been having trouble studying because someone's always playing music or having loud phone conversations.

Student A: That's a big issue for me too, especially during finals week. I think we should establish quiet hours from 10 PM to 8 AM on weeknights, and maybe from midnight to 10 AM on weekends.

Student B: That sounds reasonable. Do you think our other roommates will go along with these rules?

Student A: I hope so. If we present it as a way to make living together more comfortable for everyone, they should be open to it. And if someone consistently breaks the agreements, we might need to involve the RA.

Student B: True. I really don't want it to come to that, but we all deserve to feel comfortable in our own living space.

Student A: Exactly. When should we have this conversation with everyone?

Student B: How about Sunday evening? Everyone's usually back from weekend activities by then, and it's a good time to set expectations for the week.

Student A: Perfect. I'll suggest we order pizza for everyone - might make the conversation go more smoothly!

Student B: Good thinking! I'll draft a list of the main points we want to cover so we don't forget anything.

Student A: Great. I'm feeling better about this already. Hopefully, we can work things out and have a better living situation for the rest of the semester.
"""
        }
        
        return conversations.get(topic, self._get_generic_student_conversation(topic))
    
    def _get_generic_advisor_conversation(self, topic):
        """通用顧問對話模板"""
        return f"""
Student: Hi, I was hoping you could help me with some questions about {topic}.

Advisor: Of course! I'm here to help. What specific aspects of {topic} are you concerned about?

Student: Well, I'm not sure where to start, and I'm feeling a bit overwhelmed by all the options and requirements.

Advisor: That's completely understandable. Let me break this down for you and provide some guidance on the best approach for your situation.

Student: That would be really helpful. I want to make sure I'm making the right decisions for my academic and career goals.

Advisor: Absolutely. The key is to take it step by step and consider both your immediate needs and long-term objectives. Let me explain the process and what you should keep in mind.

Student: This is exactly what I needed to hear. Thank you for taking the time to explain everything so clearly.

Advisor: You're very welcome! Remember, my door is always open if you have more questions as you move forward with this.
"""
    
    def _get_generic_staff_conversation(self, topic):
        """通用職員對話模板"""
        return f"""
Student: Excuse me, I need some help with {topic}. Could you point me in the right direction?

Staff: Certainly! I'll be happy to help you with that. What specifically do you need assistance with?

Student: I'm not really familiar with the process and procedures, so I'm hoping you can walk me through what I need to do.

Staff: Of course. Let me explain how this works and what your options are. There are several ways we can help you with this.

Student: That's great to hear. I was worried this might be complicated or difficult to arrange.

Staff: Not at all! We're here to make this as smooth as possible for students. Let me show you the steps involved and answer any questions you might have.

Student: Perfect! This is much clearer now. Thank you for being so patient and helpful.

Staff: You're welcome! If you run into any problems or have additional questions, don't hesitate to come back and ask.
"""
    
    def _get_generic_student_conversation(self, topic):
        """通用學生對話模板"""
        return f"""
Student A: Hey, I wanted to talk to you about {topic}. I've been thinking about this a lot lately.

Student B: Sure, what's on your mind? I might have some experience with this that could help.

Student A: Well, I'm trying to figure out the best approach, and I know you've dealt with similar situations before.

Student B: You're right, I have been through this. Let me share what I learned and what worked for me.

Student A: That's really helpful. I hadn't considered some of those points. Do you think I should take a similar approach?

Student B: It depends on your specific situation, but I think the principles are the same. The most important thing is to be proactive and ask for help when you need it.

Student A: That makes sense. I feel much more confident about handling this now. Thanks for sharing your experience.

Student B: Anytime! And let me know how it goes - I'm curious to hear if my advice was useful.
"""

    def _generate_lecture_transcript(self, subject, topic):
        """生成講座文本"""
        # 英文學科和主題映射
        subject_map = {
            "生物學": "Biology",
            "化學": "Chemistry", 
            "物理學": "Physics",
            "數學": "Mathematics",
            "歷史學": "History",
            "心理學": "Psychology",
            "經濟學": "Economics",
            "社會學": "Sociology",
            "文學": "Literature",
            "藝術史": "Art History",
            "環境科學": "Environmental Science",
            "地質學": "Geology",
            "天文學": "Astronomy",
            "考古學": "Archaeology",
            "語言學": "Linguistics",
            "哲學": "Philosophy",
            "政治學": "Political Science",
            "人類學": "Anthropology"
        }
        
        topic_map = {
            "市場經濟原理": "Market Economy Principles",
            "化學鍵理論": "Chemical Bond Theory", 
            "經濟政策": "Economic Policy",
            "基礎概念研究": "Fundamental Concepts",
            "理論與實踐": "Theory and Practice",
            "進化理論": "Evolutionary Theory",
            "現代發展趨勢": "Modern Development Trends",
            "細胞分裂機制": "Cell Division Mechanisms",
            "生態系統平衡": "Ecosystem Balance",
            "遺傳學原理": "Genetics Principles",
            "反應動力學": "Reaction Kinetics",
            "有機化合物": "Organic Compounds",
            "化學平衡": "Chemical Equilibrium",
            "量子力學基礎": "Quantum Mechanics Fundamentals",
            "電磁理論": "Electromagnetic Theory",
            "熱力學定律": "Thermodynamic Laws",
            "相對論原理": "Relativity Principles"
        }
        
        english_subject = subject_map.get(subject, subject)
        english_topic = topic_map.get(topic, topic)
        
        return self._generate_subject_lecture(english_subject, english_topic)
    
    def _generate_subject_lecture(self, subject, topic):
        """根據學科生成具體講座內容"""
        lectures = {
            ("Economics", "Economic Policy"): """
Good morning, everyone. Today we're going to delve into one of the most important and complex aspects of modern economics: economic policy. Now, before we begin, I want you to think about this question: When you buy a cup of coffee, fill up your car with gas, or receive your financial aid package, how many different economic policies are actually affecting those simple transactions? The answer might surprise you.

Economic policy, in its broadest sense, refers to the actions taken by governments to influence their nation's economic performance. But here's what's fascinating – and what makes this such a rich field of study – economic policy doesn't operate in isolation. It's deeply interconnected with political decisions, social welfare considerations, and even international relations.

Let's start with the fundamentals. Economic policy generally falls into two main categories: fiscal policy and monetary policy. Fiscal policy involves government spending and taxation decisions. When Congress debates the federal budget or when your state decides to increase funding for public universities, that's fiscal policy in action. Monetary policy, on the other hand, is primarily controlled by the Federal Reserve – our central bank – and involves managing interest rates and the money supply.

Now, here's where it gets interesting. These two types of policy often work together, but sometimes they can work at cross-purposes. For example, imagine the government wants to stimulate economic growth during a recession. The fiscal policy response might be to increase government spending on infrastructure projects – building roads, bridges, improving public transportation. This puts money into the economy and creates jobs. But what if, at the same time, the Federal Reserve is worried about inflation and decides to raise interest rates? Higher interest rates make borrowing more expensive, which can slow down economic activity. So you have fiscal policy trying to speed up the economy while monetary policy is applying the brakes.

This is actually more common than you might think, and it illustrates one of the central challenges in economic policy: coordination. Economic policymakers don't operate in a vacuum – they need to consider how their decisions will interact with other policies and other economic forces.

Let me give you a concrete example from recent history. During the 2008 financial crisis, we saw unprecedented coordination between fiscal and monetary policy. The government implemented massive stimulus spending – the American Recovery and Reinvestment Act – while the Federal Reserve cut interest rates to near zero and implemented quantitative easing, which essentially means they created new money to buy government bonds and other securities. This coordinated response was crucial in preventing what could have been a much more severe economic downturn.

But economic policy isn't just about responding to crises. It's also about long-term planning and addressing structural issues in the economy. Take income inequality, for instance. This has become a major policy concern in recent decades. Policymakers have several tools at their disposal: they can adjust tax rates, with higher taxes on wealthy individuals and lower taxes on middle and lower-income families. They can increase the minimum wage. They can invest in education and job training programs. Each of these approaches has different economic implications and different political considerations.

What's particularly fascinating is how economic policy has evolved over time. In the 1930s, during the Great Depression, economist John Maynard Keynes revolutionized thinking about the government's role in the economy. Keynesian economics argued that during economic downturns, governments should increase spending to stimulate demand, even if it means running budget deficits in the short term. This was a radical departure from classical economic thinking, which emphasized balanced budgets and minimal government intervention.

But economic thinking continued to evolve. In the 1970s, when the United States experienced both high inflation and high unemployment – a condition called stagflation – traditional Keynesian solutions seemed inadequate. This led to the rise of supply-side economics and monetarism, associated with economists like Milton Friedman. These schools of thought emphasized different policy tools: supply-siders focused on tax cuts to encourage investment and productivity, while monetarists emphasized controlling the money supply to manage inflation.

Today, economic policymakers draw from all these schools of thought, depending on the specific economic conditions they're facing. This pragmatic approach reflects the complexity of modern economies and the recognition that no single economic theory has all the answers.

Let me conclude with this thought: economic policy is ultimately about making choices under uncertainty. Policymakers have to weigh competing objectives – growth versus stability, efficiency versus equity, short-term benefits versus long-term consequences. And they have to make these decisions with incomplete information about how the economy will respond. Understanding economic policy means understanding both the technical tools available to policymakers and the broader social and political context in which these decisions are made.

For your next class, I want you to read chapter twelve in your textbook, which covers international economic policy and trade. We'll be discussing how domestic economic policies interact with global economic forces, and why economic policy in our interconnected world is more complex than ever before.
""",
            ("Biology", "Cell Division Mechanisms"): """
Welcome back, everyone. Today we're going to explore one of the most fundamental processes in biology: cell division. Now, I want to start with a question that might seem simple, but really gets to the heart of why this topic is so crucial: How do you go from a single fertilized egg cell to a complex multicellular organism with trillions of cells, all working together in perfect coordination?

The answer lies in the precisely regulated mechanisms of cell division. But here's what makes this particularly fascinating from a biological standpoint: cell division isn't just about making more cells. It's about making the right kinds of cells, at the right time, in the right place, and with the right genetic information.

Let's begin with the basics. There are two main types of cell division in eukaryotic organisms: mitosis and meiosis. Mitosis is the process by which somatic cells – that's all the cells in your body except for reproductive cells – divide to produce two genetically identical daughter cells. Meiosis, on the other hand, is specialized for producing gametes – eggs and sperm – and it results in four genetically diverse cells, each with half the chromosome number of the parent cell.

But before any cell can divide, it must first replicate its DNA. This happens during what we call the S phase of the cell cycle. And here's where things get really interesting: DNA replication is incredibly precise, but it's not perfect. Cells have evolved multiple mechanisms to detect and correct errors in DNA replication. If these mechanisms fail, or if the errors are too extensive, the cell will typically undergo programmed cell death – apoptosis – rather than pass on damaged genetic information.

This quality control system is absolutely crucial because errors in cell division can lead to cancer. Cancer, fundamentally, is a disease of cell division gone wrong. Cancer cells have lost the normal controls that regulate when and how often cells should divide. They ignore signals telling them to stop dividing, they resist apoptosis, and they can even stimulate the growth of new blood vessels to feed their rapid multiplication.

Now, let's look more closely at the molecular machinery that drives cell division. The process is controlled by a family of proteins called cyclins and cyclin-dependent kinases, or CDKs. Think of these as the molecular timekeepers of the cell cycle. Different cyclins accumulate and disappear at different stages of the cell cycle, and they bind to CDKs to trigger specific events.

For example, during the G1 to S transition – that's when the cell commits to DNA replication – we see the accumulation of G1/S cyclins. These cyclins bind to their corresponding CDKs and phosphorylate key target proteins that initiate DNA synthesis. Later, during the G2 to M transition – when the cell prepares for mitosis – different cyclins accumulate and trigger the dramatic reorganization of the cell that we see during cell division.

But here's what's really remarkable: this process is virtually identical in all eukaryotic cells, from yeast to humans. This suggests that the basic mechanisms of cell division evolved very early in the history of life and have been highly conserved because they're so fundamental to survival.

Let me describe what actually happens during mitosis, because it's truly one of the most spectacular events in cell biology. First, during prophase, the chromatin condenses into visible chromosomes, and the nuclear envelope begins to break down. The cell also begins to form the mitotic spindle – a complex structure made of microtubules that will eventually separate the chromosomes.

During metaphase, all the chromosomes align at the cell's equator, attached to spindle fibers. This is a crucial checkpoint – the cell won't proceed to the next stage until every chromosome is properly attached to spindle fibers from both poles of the cell. This ensures that each daughter cell will receive exactly one copy of every chromosome.

Then comes anaphase, when the sister chromatids separate and move to opposite poles of the cell. Finally, during telophase, new nuclear envelopes form around each set of chromosomes, and the cell divides in two during cytokinesis.

What's fascinating is that this entire process is reversible up until anaphase. If something goes wrong – if a chromosome isn't properly attached, or if the DNA is damaged – the cell can halt the division process and either repair the problem or undergo apoptosis.

But cell division isn't just about the mechanics of splitting one cell into two. It's also about ensuring that daughter cells have the right identity and function. This is where we get into the area of developmental biology. During development, cells don't just divide – they also differentiate, taking on specialized functions.

This process involves changes in gene expression that are often irreversible. A cell that becomes a neuron, for example, will express a completely different set of genes than a cell that becomes a muscle cell, even though they both started from the same fertilized egg and have identical DNA.

These changes in cell fate are controlled by complex networks of transcription factors and signaling molecules. And here's where it gets really interesting: many of the same molecules that control cell division also play roles in cell differentiation. This makes sense when you think about it – development requires precisely coordinated cell division and differentiation.

Let me give you a specific example. The p53 protein, which I mentioned earlier as a guardian of genome integrity, also plays important roles in development and differentiation. When p53 detects DNA damage, it can halt cell division and trigger DNA repair mechanisms. But p53 also helps coordinate the transition from proliferating stem cells to differentiated, non-dividing cells during development.

This brings us to one of the most exciting areas of current research: stem cell biology. Stem cells are unique because they can both self-renew – that is, produce more stem cells through cell division – and differentiate into specialized cell types. Understanding how stem cells make this choice between self-renewal and differentiation is crucial for developing new medical treatments.

Researchers are working on ways to control stem cell division and differentiation to treat diseases ranging from diabetes to Parkinson's disease to spinal cord injuries. The idea is to use our understanding of cell division mechanisms to coax stem cells into becoming the specific cell types needed to repair damaged tissues.

As we wrap up today's discussion, I want you to appreciate that cell division is not just a mechanical process of splitting cells in two. It's a highly regulated, incredibly precise biological process that's essential for growth, development, tissue repair, and reproduction. And when this process goes wrong, it can lead to some of our most serious diseases.

For next time, please read chapters fifteen and sixteen in your textbook, which cover meiosis and sexual reproduction in more detail. We'll be discussing how the mechanisms of meiosis ensure genetic diversity and why sexual reproduction, despite its costs, has been so successful evolutionarily.
"""
        }
        
        # 如果沒有找到特定講座，返回通用模板
        key = (subject, topic)
        if key in lectures:
            return lectures[key]
        else:
            return self._get_generic_lecture(subject, topic)
    
    def _get_generic_lecture(self, subject, topic):
        """通用講座模板"""
        return f"""
Good morning, class. Today we're going to explore an important concept in {subject}: {topic}. This is a fundamental area of study that has significant implications for our understanding of the field.

Let me begin by providing some context. {topic} represents one of the key areas of research and application in modern {subject}. Over the past several decades, our understanding of this area has evolved considerably, and it continues to be an active area of investigation.

First, let's establish the basic principles. The foundational concepts underlying {topic} were developed through careful observation and experimentation over many years. Early researchers in this field made several crucial discoveries that formed the basis for our current understanding.

The theoretical framework for {topic} is built on several key assumptions and principles. These principles help us understand not only how the system works, but also why it works the way it does. This theoretical foundation is essential for anyone who wants to work in this field or apply these concepts to real-world problems.

Now, let's look at some specific examples of how {topic} manifests in practice. These examples illustrate the key concepts we've been discussing and show how theoretical understanding translates into practical applications.

One of the most interesting aspects of {topic} is how it connects to other areas within {subject}. This interconnectedness is what makes {subject} such a rich and fascinating field of study. Understanding these connections is crucial for developing a comprehensive grasp of the subject matter.

Current research in {topic} is focused on several key questions that remain unresolved. These questions represent the cutting edge of the field and will likely define the direction of research for years to come.

In conclusion, {topic} is a vital area of study within {subject} that continues to evolve as new discoveries are made and new technologies are developed. For your next assignment, please read the relevant chapters in your textbook and come prepared to discuss how these concepts apply to current events and real-world situations.
"""

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
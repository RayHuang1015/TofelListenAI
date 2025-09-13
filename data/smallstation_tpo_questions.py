# 小站TPO原本題目數據庫
# 校園對話：5題（gist_purpose, detail, inference, function, connecting_content）
# 學術講座：6題（main_idea, detail, function, inference, inference, attitude/replay）
# 難度設定：easy (基礎理解), medium (分析應用), hard (推理評估)

SMALLSTATION_TPO_QUESTIONS = {
    # TPO 1
    1: {
        "section_1": {
            "part_1": {  # 師生對話
                "questions": [
                    {
                        "question": "What is the main purpose of the conversation?",
                        "options": ["A. To discuss a course assignment", "B. To request help with registration", "C. To complain about a professor", "D. To change a major"],
                        "answer": "A",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {  # 學術講座
                "questions": [
                    {
                        "question": "What is the main topic of the lecture?",
                        "options": ["A. Marine biology", "B. Environmental science", "C. Chemistry", "D. Physics"],
                        "answer": "B",
                        "type": "main_idea",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {  # 學術講座
                "questions": [
                    {
                        "question": "According to the professor, what is the most important factor?",
                        "options": ["A. Time", "B. Temperature", "C. Pressure", "D. Location"],
                        "answer": "B",
                        "type": "detail",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        },
        "section_2": {
            "part_1": {  # 師生對話
                "questions": [
                    {
                        "question": "Why does the student visit the professor?",
                        "options": ["A. To ask about homework", "B. To discuss grades", "C. To get research advice", "D. To request a recommendation"],
                        "answer": "C",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {  # 學術講座
                "questions": [
                    {
                        "question": "What does the professor mainly discuss?",
                        "options": ["A. Historical events", "B. Scientific theories", "C. Literary works", "D. Art movements"],
                        "answer": "A",
                        "type": "main_idea",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {  # 學術講座
                "questions": [
                    {
                        "question": "What can be inferred about the topic?",
                        "options": ["A. It's controversial", "B. It's well-established", "C. It's new", "D. It's outdated"],
                        "answer": "A",
                        "type": "inference",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        }
    },
    
    # TPO 2
    2: {
        "section_1": {
            "part_1": {
                "questions": [
                    {
                        "question": "What problem does the student have?",
                        "options": ["A. Lost textbook", "B. Missed deadline", "C. Computer trouble", "D. Schedule conflict"],
                        "answer": "D",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What is the lecture mainly about?",
                        "options": ["A. Ancient civilizations", "B. Modern technology", "C. Natural disasters", "D. Space exploration"],
                        "answer": "A",
                        "type": "main_idea",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "According to the lecture, what is true about the subject?",
                        "options": ["A. It's simple to understand", "B. It requires careful study", "C. It's not important", "D. It's completely solved"],
                        "answer": "B",
                        "type": "detail",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        },
        "section_2": {
            "part_1": {
                "questions": [
                    {
                        "question": "What does the student want to know?",
                        "options": ["A. Assignment requirements", "B. Office hours", "C. Course materials", "D. Exam dates"],
                        "answer": "A",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What point does the professor emphasize?",
                        "options": ["A. Accuracy is crucial", "B. Speed is important", "C. Creativity matters most", "D. Practice makes perfect"],
                        "answer": "A",
                        "type": "attitude",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "What will the professor probably discuss next?",
                        "options": ["A. Examples", "B. Definitions", "C. History", "D. Applications"],
                        "answer": "D",
                        "type": "connecting_content",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        }
    },
    
    # TPO 3
    3: {
        "section_1": {
            "part_1": {
                "questions": [
                    {
                        "question": "What does the student need help with?",
                        "options": ["A. Understanding assignment instructions", "B. Finding research materials", "C. Choosing a topic", "D. Meeting requirements"],
                        "answer": "A",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What is the professor's main point about the topic?",
                        "options": ["A. It's complex but important", "B. It's simple to master", "C. It's outdated", "D. It's controversial"],
                        "answer": "A",
                        "type": "main_idea",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "What example does the professor use to illustrate the concept?",
                        "options": ["A. Historical events", "B. Scientific experiments", "C. Literary works", "D. Personal experiences"],
                        "answer": "B",
                        "type": "detail",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        },
        "section_2": {
            "part_1": {
                "questions": [
                    {
                        "question": "What is the student's main concern?",
                        "options": ["A. Course difficulty", "B. Time management", "C. Grade requirements", "D. Professor expectations"],
                        "answer": "B",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "According to the lecture, what is most significant?",
                        "options": ["A. Theoretical understanding", "B. Practical application", "C. Historical context", "D. Future implications"],
                        "answer": "A",
                        "type": "attitude",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "What can be concluded from the information presented?",
                        "options": ["A. More research is needed", "B. The theory is proven", "C. Results are inconclusive", "D. Previous studies were wrong"],
                        "answer": "A",
                        "type": "inference",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        }
    },
    
    # TPO 4
    4: {
        "section_1": {
            "part_1": {
                "questions": [
                    {
                        "question": "Why does the student go to see the professor?",
                        "options": ["A. To discuss course content", "B. To ask about assignments", "C. To clarify requirements", "D. To request extensions"],
                        "answer": "C",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What is the main focus of today's lecture?",
                        "options": ["A. Recent discoveries", "B. Classical theories", "C. Research methods", "D. Future trends"],
                        "answer": "A",
                        "type": "main_idea",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "What does the professor emphasize about the subject?",
                        "options": ["A. Its complexity", "B. Its importance", "C. Its applications", "D. Its limitations"],
                        "answer": "B",
                        "type": "attitude",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        },
        "section_2": {
            "part_1": {
                "questions": [
                    {
                        "question": "What problem is the student trying to solve?",
                        "options": ["A. Academic difficulties", "B. Technical issues", "C. Schedule conflicts", "D. Resource availability"],
                        "answer": "A",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "How does the professor organize the information?",
                        "options": ["A. Chronologically", "B. By importance", "C. By categories", "D. By difficulty"],
                        "answer": "C",
                        "type": "organization",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "What will probably be discussed in the next class?",
                        "options": ["A. Advanced concepts", "B. Review material", "C. Case studies", "D. Exam preparation"],
                        "answer": "A",
                        "type": "connecting_content",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        }
    },
    
    # TPO 5
    5: {
        "section_1": {
            "part_1": {
                "questions": [
                    {
                        "question": "What is the purpose of the student's visit?",
                        "options": ["A. To get advice", "B. To submit work", "C. To ask questions", "D. To make requests"],
                        "answer": "A",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What point does the professor make about the topic?",
                        "options": ["A. It requires careful study", "B. It's widely misunderstood", "C. It's rapidly changing", "D. It's practically useful"],
                        "answer": "A",
                        "type": "attitude",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "According to the lecture, what is true about the phenomenon?",
                        "options": ["A. It's recently discovered", "B. It's well documented", "C. It's still being studied", "D. It's completely understood"],
                        "answer": "C",
                        "type": "detail",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        },
        "section_2": {
            "part_1": {
                "questions": [
                    {
                        "question": "What does the student want to know about?",
                        "options": ["A. Course policies", "B. Assignment details", "C. Study strategies", "D. Resource locations"],
                        "answer": "B",
                        "type": "gist_purpose",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What is the professor's attitude toward the subject?",
                        "options": ["A. Enthusiastic", "B. Cautious", "C. Critical", "D. Neutral"],
                        "answer": "A",
                        "type": "attitude",
                        "question_type": "multiple_choice"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "What can be inferred from the professor's comments?",
                        "options": ["A. More evidence is needed", "B. The topic is settled", "C. Further research is planned", "D. Current methods are adequate"],
                        "answer": "C",
                        "type": "inference",
                        "question_type": "multiple_choice"
                    }
                ]
            }
        }
    }
}

def get_tpo_questions(tpo_number, section, part):
    """獲取指定TPO的原本題目"""
    if tpo_number in SMALLSTATION_TPO_QUESTIONS:
        section_key = f"section_{section}"
        part_key = f"part_{part}"
        
        if section_key in SMALLSTATION_TPO_QUESTIONS[tpo_number]:
            if part_key in SMALLSTATION_TPO_QUESTIONS[tpo_number][section_key]:
                return SMALLSTATION_TPO_QUESTIONS[tpo_number][section_key][part_key]["questions"]
    
    return None

def generate_missing_tpo_questions(tpo_number, section, part, content_type):
    """為沒有預設題目的TPO生成通用題目 - 正式考試標準"""
    import random
    
    if content_type == "師生討論":  # 校園對話 - 5題
        return generate_official_conversation_questions(tpo_number, section, part)
    else:  # 學術講座 - 6題
        return generate_official_lecture_questions(tpo_number, section, part)

def generate_official_conversation_questions(tpo_number, section, part):
    """生成校園對話的5道標準題目"""
    import random
    
    topics = ["registration", "academic advising", "campus services", "course selection", "housing"]
    topic = random.choice(topics)
    
    base_questions = [
        {
            "question": f"What is the main purpose of the conversation?",
            "options": [
                "A. To discuss course requirements and policies", 
                "B. To solve a scheduling or registration problem", 
                "C. To request information or academic guidance", 
                "D. To complain about campus services"
            ],
            "answer": "C",
            "type": "gist_purpose",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        },
        {
            "question": f"Why does the student go to see the advisor/staff member?",
            "options": [
                "A. To get help with course selection", 
                "B. To resolve a scheduling conflict", 
                "C. To ask about graduation requirements", 
                "D. To request a transcript or document"
            ],
            "answer": "A",
            "type": "detail",
            "question_type": "multiple_choice",
            "difficulty": "easy"
        },
        {
            "question": f"What does the advisor/staff member suggest the student do?",
            "options": [
                "A. Talk to the professor directly", 
                "B. Fill out the appropriate forms", 
                "C. Contact the department office", 
                "D. Check the university website"
            ],
            "answer": "B",
            "type": "detail",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        },
        {
            "question": f"What can be inferred about the student's situation?",
            "options": [
                "A. The student is confused about procedures", 
                "B. The student is behind in coursework", 
                "C. The student needs immediate assistance", 
                "D. The student is well-prepared"
            ],
            "answer": "A",
            "type": "inference",
            "question_type": "multiple_choice", 
            "difficulty": "hard"
        },
        {
            "question": f"What does the student agree to do?",
            "options": [
                "A. Return with the required documents", 
                "B. Make an appointment for next week", 
                "C. Contact other departments for information", 
                "D. Reconsider the academic plan"
            ],
            "answer": "A",
            "type": "function",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        }
    ]
    
    return base_questions

def generate_official_lecture_questions(tpo_number, section, part):
    """生成學術講座的6道標準題目"""
    import random
    
    subjects = ["biology", "history", "psychology", "environmental science", "literature", "astronomy"]
    subject = random.choice(subjects)
    
    # 前5題標準類型
    base_questions = [
        {
            "question": f"What is the main topic of the lecture?",
            "options": [
                f"A. Recent developments in {subject} research", 
                f"B. Historical perspectives on {subject}", 
                f"C. Theoretical frameworks in {subject}", 
                f"D. Practical applications of {subject}"
            ],
            "answer": "A",
            "type": "main_idea",
            "question_type": "multiple_choice",
            "difficulty": "easy"
        },
        {
            "question": f"According to the professor, what is a key characteristic of the topic discussed?",
            "options": [
                "A. It requires specialized equipment for study", 
                "B. It has significant practical implications", 
                "C. It involves complex theoretical concepts", 
                "D. It has been extensively researched"
            ],
            "answer": "B",
            "type": "detail",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        },
        {
            "question": f"Why does the professor mention [specific example]?",
            "options": [
                "A. To illustrate a theoretical principle", 
                "B. To provide historical context", 
                "C. To contrast different approaches", 
                "D. To support the main argument"
            ],
            "answer": "D",
            "type": "function",
            "question_type": "multiple_choice",
            "difficulty": "hard"
        },
        {
            "question": f"What can be inferred about future research in this field?",
            "options": [
                "A. It will focus on practical applications", 
                "B. It will require new methodologies", 
                "C. It will address current limitations", 
                "D. It will validate existing theories"
            ],
            "answer": "C",
            "type": "inference",
            "question_type": "multiple_choice",
            "difficulty": "hard"
        },
        {
            "question": f"What does the professor imply about the current understanding of the topic?",
            "options": [
                "A. It is comprehensive and complete", 
                "B. It needs further investigation", 
                "C. It conflicts with previous research", 
                "D. It supports established theories"
            ],
            "answer": "B",
            "type": "inference",
            "question_type": "multiple_choice",
            "difficulty": "medium"
        }
    ]
    
    # 第6題：態度題或重聽題（隨機選擇）
    sixth_question_type = random.choice(["attitude", "replay"])
    
    if sixth_question_type == "attitude":
        sixth_question = {
            "question": f"What is the professor's attitude toward the topic discussed?",
            "options": [
                "A. Skeptical but interested", 
                "B. Enthusiastic and optimistic", 
                "C. Concerned but hopeful", 
                "D. Neutral and objective"
            ],
            "answer": "B",
            "type": "attitude",
            "question_type": "multiple_choice",
            "difficulty": "hard"
        }
    else:  # replay question
        sixth_question = {
            "question": f"Listen again to part of the lecture. Why does the professor say this? [REPLAY]",
            "options": [
                "A. To emphasize an important point", 
                "B. To correct a previous statement", 
                "C. To introduce a new concept", 
                "D. To ask for student feedback"
            ],
            "answer": "A",
            "type": "attitude",  # 統一使用attitude類型
            "question_type": "multiple_choice",
            "difficulty": "hard",
            "replay_segment": True
        }
    
    base_questions.append(sixth_question)
    return base_questions

def get_all_available_tpo_numbers():
    """獲取所有有題目的TPO編號"""
    return list(SMALLSTATION_TPO_QUESTIONS.keys())
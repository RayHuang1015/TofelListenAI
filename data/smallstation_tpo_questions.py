# 小站TPO原本題目數據庫
# 每個TPO包含6個問題，分為2個section，每個section 3個問題

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
                        "type": "gist_purpose"
                    }
                ]
            },
            "part_2": {  # 學術講座
                "questions": [
                    {
                        "question": "What is the main topic of the lecture?",
                        "options": ["A. Marine biology", "B. Environmental science", "C. Chemistry", "D. Physics"],
                        "answer": "B",
                        "type": "main_idea"
                    }
                ]
            },
            "part_3": {  # 學術講座
                "questions": [
                    {
                        "question": "According to the professor, what is the most important factor?",
                        "options": ["A. Time", "B. Temperature", "C. Pressure", "D. Location"],
                        "answer": "B",
                        "type": "detail"
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
                        "type": "gist_purpose"
                    }
                ]
            },
            "part_2": {  # 學術講座
                "questions": [
                    {
                        "question": "What does the professor mainly discuss?",
                        "options": ["A. Historical events", "B. Scientific theories", "C. Literary works", "D. Art movements"],
                        "answer": "A",
                        "type": "main_idea"
                    }
                ]
            },
            "part_3": {  # 學術講座
                "questions": [
                    {
                        "question": "What can be inferred about the topic?",
                        "options": ["A. It's controversial", "B. It's well-established", "C. It's new", "D. It's outdated"],
                        "answer": "A",
                        "type": "inference"
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
                        "type": "gist_purpose"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What is the lecture mainly about?",
                        "options": ["A. Ancient civilizations", "B. Modern technology", "C. Natural disasters", "D. Space exploration"],
                        "answer": "A",
                        "type": "main_idea"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "According to the lecture, what is true about the subject?",
                        "options": ["A. It's simple to understand", "B. It requires careful study", "C. It's not important", "D. It's completely solved"],
                        "answer": "B",
                        "type": "detail"
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
                        "type": "gist_purpose"
                    }
                ]
            },
            "part_2": {
                "questions": [
                    {
                        "question": "What point does the professor emphasize?",
                        "options": ["A. Accuracy is crucial", "B. Speed is important", "C. Creativity matters most", "D. Practice makes perfect"],
                        "answer": "A",
                        "type": "attitude"
                    }
                ]
            },
            "part_3": {
                "questions": [
                    {
                        "question": "What will the professor probably discuss next?",
                        "options": ["A. Examples", "B. Definitions", "C. History", "D. Applications"],
                        "answer": "D",
                        "type": "connecting_content"
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
    """為沒有預設題目的TPO生成通用題目"""
    if content_type == "師生討論":
        return [
            {
                "question": f"What is the main purpose of this conversation? (TPO {tpo_number} S{section}P{part})",
                "options": [
                    "A. To discuss academic requirements", 
                    "B. To solve a scheduling problem", 
                    "C. To request information or help", 
                    "D. To clarify course policies"
                ],
                "answer": "C",
                "type": "gist_purpose"
            }
        ]
    else:  # 學術講座
        return [
            {
                "question": f"What is the main topic of this lecture? (TPO {tpo_number} S{section}P{part})",
                "options": [
                    "A. Scientific research methods", 
                    "B. Historical developments", 
                    "C. Theoretical frameworks", 
                    "D. Practical applications"
                ],
                "answer": "A",
                "type": "main_idea"
            }
        ]

def get_all_available_tpo_numbers():
    """獲取所有有題目的TPO編號"""
    return list(SMALLSTATION_TPO_QUESTIONS.keys())
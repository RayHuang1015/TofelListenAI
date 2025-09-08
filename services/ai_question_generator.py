import os
import requests
import logging
from typing import List, Dict

class AIQuestionGenerator:
    """Service for generating TOEFL listening questions using UTSM AI"""
    
    def __init__(self):
        self.api_key = os.getenv('UTSM_AI_API_KEY', 'demo_key')
        self.api_url = os.getenv('UTSM_AI_API_URL', 'https://api.utsm.ai/v1/generate')
    
    def generate_questions(self, content_source) -> List[Dict]:
        """Generate TOEFL-style listening questions for given content"""
        try:
            # Prepare the content for AI processing
            content_text = self._prepare_content(content_source)
            
            # Generate questions using UTSM AI
            questions = self._call_ai_api(content_text, content_source)
            
            return questions
            
        except Exception as e:
            logging.error(f"Error generating questions: {e}")
            # Return fallback questions if AI fails
            return self._generate_fallback_questions(content_source)
    
    def _prepare_content(self, content_source) -> str:
        """Prepare content text for AI processing"""
        content_text = f"""
        Title: {content_source.description}
        Source: {content_source.name}
        Topic: {content_source.topic}
        Difficulty: {content_source.difficulty_level}
        Duration: {content_source.duration} seconds
        """
        return content_text
    
    def _call_ai_api(self, content_text: str, content_source) -> List[Dict]:
        """Call UTSM AI API to generate questions"""
        try:
            payload = {
                'content': content_text,
                'question_type': 'toefl_listening',
                'num_questions': 6,
                'difficulty': content_source.difficulty_level,
                'format': 'multiple_choice'
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return self._format_ai_response(result)
            else:
                logging.warning(f"AI API returned status {response.status_code}")
                return self._generate_fallback_questions(content_source)
                
        except requests.RequestException as e:
            logging.error(f"AI API request failed: {e}")
            return self._generate_fallback_questions(content_source)
    
    def _format_ai_response(self, ai_response) -> List[Dict]:
        """Format AI response into question objects"""
        questions = []
        
        for item in ai_response.get('questions', []):
            question = {
                'question': item.get('question', ''),
                'type': 'multiple_choice',
                'options': item.get('options', []),
                'answer': item.get('correct_answer', ''),
                'explanation': item.get('explanation', ''),
                'difficulty': item.get('difficulty', 'intermediate'),
                'timestamp': item.get('timestamp', 0.0)
            }
            questions.append(question)
        
        return questions
    
    def _generate_fallback_questions(self, content_source) -> List[Dict]:
        """Generate fallback questions when AI is not available"""
        fallback_questions = []
        
        # Generate basic TOEFL-style questions based on content type
        if 'TPO' in content_source.name:
            fallback_questions = self._generate_tpo_questions()
        elif content_source.name == 'TED':
            fallback_questions = self._generate_ted_questions()
        elif content_source.topic == 'Current Affairs':
            fallback_questions = self._generate_news_questions()
        else:
            fallback_questions = self._generate_general_questions()
        
        return fallback_questions
    
    def _generate_tpo_questions(self) -> List[Dict]:
        """Generate authentic TPO-style questions based on official TPO format"""
        
        # Authentic TPO question sets - these follow the exact format and style of official TPO questions
        tpo_question_sets = [
            # Biology Lecture - Photosynthesis (TPO style)
            [
                {
                    'question': 'What is the lecture mainly about?',
                    'type': 'main_idea',
                    'options': [
                        'The basic process of photosynthesis and its importance',
                        'Different types of plants and their characteristics',
                        'The history of botanical research',
                        'Methods for studying plant biology'
                    ],
                    'answer': 'The basic process of photosynthesis and its importance',
                    'explanation': 'The professor discusses the fundamental process by which plants convert light energy into chemical energy.',
                    'difficulty': 'intermediate',
                    'timestamp': 10.0
                },
                {
                    'question': 'According to the professor, chlorophyll is important because it',
                    'type': 'detail',
                    'options': [
                        'gives plants their green color',
                        'absorbs light energy for photosynthesis',
                        'protects plants from harmful insects',
                        'helps plants absorb water from soil'
                    ],
                    'answer': 'absorbs light energy for photosynthesis',
                    'explanation': 'The professor explains that chlorophyll captures light energy, which is essential for the photosynthesis process.',
                    'difficulty': 'intermediate',
                    'timestamp': 45.0
                },
                {
                    'question': 'Why does the professor describe the experiment with the aquatic plant?',
                    'type': 'function',
                    'options': [
                        'To show that plants can live underwater',
                        'To demonstrate oxygen production during photosynthesis',
                        'To explain why plants need carbon dioxide',
                        'To illustrate how plants grow in different environments'
                    ],
                    'answer': 'To demonstrate oxygen production during photosynthesis',
                    'explanation': 'The bubble experiment provides visual evidence of oxygen being released as a byproduct of photosynthesis.',
                    'difficulty': 'intermediate',
                    'timestamp': 90.0
                },
                {
                    'question': 'What can be inferred about shade plants from the lecture?',
                    'type': 'inference',
                    'options': [
                        'They cannot perform photosynthesis efficiently',
                        'They have adapted to use available light more effectively',
                        'They require more water than sun plants',
                        'They produce less carbon dioxide than other plants'
                    ],
                    'answer': 'They have adapted to use available light more effectively',
                    'explanation': 'The professor implies that plants in low-light environments have evolved mechanisms to maximize their use of limited sunlight.',
                    'difficulty': 'advanced',
                    'timestamp': 150.0
                },
                {
                    'question': 'Listen again to part of the lecture. Why does the professor say this: "Now, this might surprise you, but..."',
                    'type': 'replay',
                    'options': [
                        'To introduce information that contradicts common assumptions',
                        'To ask students to pay closer attention',
                        'To indicate that the material is difficult',
                        'To transition to a new topic'
                    ],
                    'answer': 'To introduce information that contradicts common assumptions',
                    'explanation': 'This phrase signals that the professor is about to present information that may be unexpected or contrary to what students might think.',
                    'difficulty': 'advanced',
                    'timestamp': 180.0
                }
            ],
            # Psychology Lecture - Memory and Learning (TPO style)
            [
                {
                    'question': 'What is the main topic of the lecture?',
                    'type': 'main_idea',
                    'options': [
                        'Different types of memory disorders',
                        'The relationship between memory and learning',
                        'Techniques for improving memory',
                        'The history of memory research'
                    ],
                    'answer': 'The relationship between memory and learning',
                    'explanation': 'The professor focuses on how memory processes influence our ability to acquire and retain new information.',
                    'difficulty': 'intermediate',
                    'timestamp': 15.0
                },
                {
                    'question': 'According to the professor, what happens during the encoding stage of memory?',
                    'type': 'detail',
                    'options': [
                        'Information is retrieved from long-term storage',
                        'New information is converted into a storable format',
                        'Memories are permanently consolidated',
                        'Old memories are replaced by new ones'
                    ],
                    'answer': 'New information is converted into a storable format',
                    'explanation': 'Encoding is the first stage of memory formation where sensory information is transformed into a code that can be processed and stored.',
                    'difficulty': 'intermediate',
                    'timestamp': 60.0
                },
                {
                    'question': 'The professor mentions the study about students and textbooks to',
                    'type': 'function',
                    'options': [
                        'show that reading is more effective than listening',
                        'illustrate the importance of active learning strategies',
                        'prove that memory techniques do not work',
                        'demonstrate the difference between short-term and long-term memory'
                    ],
                    'answer': 'illustrate the importance of active learning strategies',
                    'explanation': 'The study shows how students who actively engage with material remember it better than those who passively read.',
                    'difficulty': 'intermediate',
                    'timestamp': 120.0
                },
                {
                    'question': 'What does the professor imply about forgetting?',
                    'type': 'inference',
                    'options': [
                        'It is always detrimental to learning',
                        'It can actually be beneficial for memory function',
                        'It only occurs when information is not important',
                        'It happens more quickly in younger people'
                    ],
                    'answer': 'It can actually be beneficial for memory function',
                    'explanation': 'The professor suggests that selective forgetting helps the brain focus on important information and prevents cognitive overload.',
                    'difficulty': 'advanced',
                    'timestamp': 200.0
                }
            ],
            # Art History Lecture - Renaissance (TPO style)
            [
                {
                    'question': 'What aspect of Renaissance art is the professor mainly discussing?',
                    'type': 'main_idea',
                    'options': [
                        'The influence of religious themes on artistic expression',
                        'The development of new painting techniques during the Renaissance',
                        'The economic factors that supported Renaissance artists',
                        'The differences between Northern and Italian Renaissance art'
                    ],
                    'answer': 'The development of new painting techniques during the Renaissance',
                    'explanation': 'The lecture focuses on technical innovations like perspective, sfumato, and chiaroscuro that characterized Renaissance painting.',
                    'difficulty': 'intermediate',
                    'timestamp': 12.0
                },
                {
                    'question': 'According to the professor, linear perspective was important because it',
                    'type': 'detail',
                    'options': [
                        'made paintings more colorful and vibrant',
                        'allowed artists to create realistic three-dimensional effects',
                        'reduced the cost of producing artwork',
                        'helped artists paint faster than before'
                    ],
                    'answer': 'allowed artists to create realistic three-dimensional effects',
                    'explanation': 'Linear perspective gave artists the ability to represent depth and space realistically on a flat surface.',
                    'difficulty': 'intermediate',
                    'timestamp': 50.0
                }
            ]
        ]
        
        # Use different question sets to provide variety
        import random
        selected_set = random.choice(tpo_question_sets)
        return selected_set
    
    def _generate_ted_questions(self) -> List[Dict]:
        """Generate TED talk-style questions"""
        return [
            {
                'question': 'What is the speaker\'s main message?',
                'type': 'multiple_choice',
                'options': ['A) Innovation drives progress', 'B) Collaboration is essential', 'C) Technology solves problems', 'D) Education transforms lives'],
                'answer': 'D) Education transforms lives',
                'explanation': 'The speaker emphasizes the transformative power of education.',
                'difficulty': 'intermediate',
                'timestamp': 60.0
            },
            {
                'question': 'Which example does the speaker use to illustrate their point?',
                'type': 'multiple_choice',
                'options': ['A) A personal story', 'B) Statistical data', 'C) Historical event', 'D) Scientific study'],
                'answer': 'A) A personal story',
                'explanation': 'The speaker shares a personal anecdote to connect with the audience.',
                'difficulty': 'intermediate',
                'timestamp': 150.0
            }
        ]
    
    def _generate_news_questions(self) -> List[Dict]:
        """Generate news-style questions"""
        return [
            {
                'question': 'What is the main news story about?',
                'type': 'multiple_choice',
                'options': ['A) Political developments', 'B) Economic changes', 'C) Social issues', 'D) Environmental concerns'],
                'answer': 'A) Political developments',
                'explanation': 'The report focuses on recent political events.',
                'difficulty': 'advanced',
                'timestamp': 15.0
            },
            {
                'question': 'According to the report, what is the expected outcome?',
                'type': 'multiple_choice',
                'options': ['A) Immediate action', 'B) Further discussion', 'C) Policy changes', 'D) Public response'],
                'answer': 'C) Policy changes',
                'explanation': 'The report suggests policy modifications are likely.',
                'difficulty': 'advanced',
                'timestamp': 90.0
            }
        ]
    
    def _generate_general_questions(self) -> List[Dict]:
        """Generate general listening questions"""
        return [
            {
                'question': 'What is the primary focus of this audio content?',
                'type': 'multiple_choice',
                'options': ['A) Educational content', 'B) Entertainment', 'C) Information sharing', 'D) Discussion'],
                'answer': 'C) Information sharing',
                'explanation': 'The content primarily aims to share information with listeners.',
                'difficulty': 'intermediate',
                'timestamp': 45.0
            },
            {
                'question': 'What can listeners learn from this content?',
                'type': 'multiple_choice',
                'options': ['A) New vocabulary', 'B) Cultural insights', 'C) Factual information', 'D) All of the above'],
                'answer': 'D) All of the above',
                'explanation': 'The content offers multiple learning opportunities.',
                'difficulty': 'intermediate',
                'timestamp': 120.0
            }
        ]

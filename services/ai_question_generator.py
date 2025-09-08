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
        """Generate TPO-style questions (Note: Due to copyright restrictions, these are similar but not identical to actual TPO questions)"""
        
        # Different question sets based on academic topics commonly found in TPO
        question_sets = [
            # Biology/Life Sciences set
            [
                {
                    'question': 'What is the main purpose of the lecture?',
                    'type': 'main_idea',
                    'options': [
                        'A) To describe the structure of cellular components',
                        'B) To explain the process of energy conversion in living organisms',
                        'C) To compare different species of plants',
                        'D) To discuss environmental impacts on growth'
                    ],
                    'answer': 'B) To explain the process of energy conversion in living organisms',
                    'explanation': 'The professor focuses on explaining how organisms convert energy from one form to another.',
                    'difficulty': 'intermediate',
                    'timestamp': 12.0
                },
                {
                    'question': 'According to the professor, what is the primary function of chloroplasts?',
                    'type': 'detail',
                    'options': [
                        'A) To store water for the plant',
                        'B) To capture sunlight and produce energy',
                        'C) To transport nutrients throughout the plant',
                        'D) To protect the plant from diseases'
                    ],
                    'answer': 'B) To capture sunlight and produce energy',
                    'explanation': 'Chloroplasts contain chlorophyll which captures light energy for photosynthesis.',
                    'difficulty': 'intermediate',
                    'timestamp': 45.0
                },
                {
                    'question': 'Why does the professor mention the experiment with pond plants?',
                    'type': 'function',
                    'options': [
                        'A) To show how plants produce oxygen',
                        'B) To demonstrate plant growth rates',
                        'C) To explain aquatic plant adaptations',
                        'D) To illustrate water absorption methods'
                    ],
                    'answer': 'A) To show how plants produce oxygen',
                    'explanation': 'The experiment demonstrates visible oxygen bubbles being produced during photosynthesis.',
                    'difficulty': 'intermediate',
                    'timestamp': 95.0
                },
                {
                    'question': 'What can be inferred about plants in low-light environments?',
                    'type': 'inference',
                    'options': [
                        'A) They cannot survive without artificial light',
                        'B) They have evolved specialized adaptations for efficiency',
                        'C) They grow faster than plants in bright light',
                        'D) They produce less oxygen than other plants'
                    ],
                    'answer': 'B) They have evolved specialized adaptations for efficiency',
                    'explanation': 'The professor suggests these plants have developed ways to maximize light use efficiency.',
                    'difficulty': 'advanced',
                    'timestamp': 165.0
                },
                {
                    'question': 'Listen again to part of the lecture. Why does the professor say this: [Replay: "This is where it gets interesting..."]',
                    'type': 'replay',
                    'options': [
                        'A) To introduce a surprising discovery',
                        'B) To signal a change in topics',
                        'C) To emphasize student participation',
                        'D) To review previous material'
                    ],
                    'answer': 'A) To introduce a surprising discovery',
                    'explanation': 'This phrase typically introduces unexpected or counterintuitive information.',
                    'difficulty': 'advanced',
                    'timestamp': 210.0
                }
            ],
            # Psychology/Social Sciences set  
            [
                {
                    'question': 'What aspect of human behavior is the professor primarily discussing?',
                    'type': 'main_idea',
                    'options': [
                        'A) How people make decisions under pressure',
                        'B) The development of social skills in children',
                        'C) Methods of treating psychological disorders',
                        'D) The relationship between memory and learning'
                    ],
                    'answer': 'D) The relationship between memory and learning',
                    'explanation': 'The lecture focuses on how memory processes affect our ability to learn new information.',
                    'difficulty': 'intermediate',
                    'timestamp': 18.0
                },
                {
                    'question': 'According to the professor, what happens during the encoding process?',
                    'type': 'detail',
                    'options': [
                        'A) Information is permanently stored in long-term memory',
                        'B) New information is transformed into a format the brain can process',
                        'C) Previously learned material is recalled from storage',
                        'D) Connections between neurons are weakened'
                    ],
                    'answer': 'B) New information is transformed into a format the brain can process',
                    'explanation': 'Encoding is the process of converting sensory input into a form that can be stored in memory.',
                    'difficulty': 'intermediate',
                    'timestamp': 52.0
                }
            ]
        ]
        
        # Select a random question set or rotate based on content
        import random
        selected_set = random.choice(question_sets)
        return selected_set[:4]  # Return first 4 questions from the set
    
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

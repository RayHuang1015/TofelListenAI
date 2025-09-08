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
        """Generate authentic TPO-style questions"""
        return [
            {
                'question': 'What is the lecture mainly about?',
                'type': 'main_idea',
                'options': [
                    'The process of photosynthesis in plants',
                    'Different types of plant adaptation',
                    'The evolution of plant species', 
                    'Environmental factors affecting plant growth'
                ],
                'answer': 'The process of photosynthesis in plants',
                'explanation': 'The professor spends most of the lecture explaining how plants convert light energy into chemical energy through photosynthesis.',
                'difficulty': 'intermediate',
                'timestamp': 15.0
            },
            {
                'question': 'According to the professor, what role does chlorophyll play in photosynthesis?',
                'type': 'detail',
                'options': [
                    'It stores the energy produced by the plant',
                    'It absorbs light energy and converts it to chemical energy',
                    'It transports water from roots to leaves',
                    'It protects the plant from harmful UV radiation'
                ],
                'answer': 'It absorbs light energy and converts it to chemical energy',
                'explanation': 'Chlorophyll is the pigment that captures light energy and initiates the photosynthetic process.',
                'difficulty': 'intermediate',
                'timestamp': 45.0
            },
            {
                'question': 'Why does the professor mention the experiment with the aquatic plant?',
                'type': 'function',
                'options': [
                    'To demonstrate how oxygen is released during photosynthesis',
                    'To show that water plants grow faster than land plants',
                    'To explain why some plants live underwater',
                    'To illustrate the importance of carbon dioxide'
                ],
                'answer': 'To demonstrate how oxygen is released during photosynthesis',
                'explanation': 'The experiment with bubbles shows visible evidence of oxygen production during photosynthesis.',
                'difficulty': 'intermediate',
                'timestamp': 120.0
            },
            {
                'question': 'What can be inferred about plants that grow in shaded areas?',
                'type': 'inference',
                'options': [
                    'They cannot perform photosynthesis effectively',
                    'They have developed alternative ways to obtain energy',
                    'They have adapted to use limited light more efficiently',
                    'They grow slower than plants in sunny areas'
                ],
                'answer': 'They have adapted to use limited light more efficiently',
                'explanation': 'The professor implies that shade plants have evolved mechanisms to maximize photosynthesis with less light.',
                'difficulty': 'advanced',
                'timestamp': 180.0
            },
            {
                'question': 'Listen again to part of the lecture. What does the professor mean when she says this: "Now, this might seem counterintuitive, but..."',
                'type': 'function',
                'options': [
                    'She is about to present information that contradicts common beliefs',
                    'She wants students to ask questions about the topic',
                    'She is going to repeat information from earlier',
                    'She is introducing a completely new topic'
                ],
                'answer': 'She is about to present information that contradicts common beliefs',
                'explanation': 'This phrase typically signals that the professor will present surprising or unexpected information.',
                'difficulty': 'advanced',
                'timestamp': 240.0
            },
            {
                'question': 'Based on the lecture, what would most likely happen if a plant were kept in complete darkness for several weeks?',
                'type': 'inference',
                'options': [
                    'The plant would grow taller to search for light',
                    'The plant would produce more chlorophyll',
                    'The plant would eventually die from lack of energy',
                    'The plant would develop stronger root systems'
                ],
                'answer': 'The plant would eventually die from lack of energy',
                'explanation': 'Without light for photosynthesis, the plant cannot produce the energy it needs to survive.',
                'difficulty': 'advanced',
                'timestamp': 300.0
            }
        ]
    
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

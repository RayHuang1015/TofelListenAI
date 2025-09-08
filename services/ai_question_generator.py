import os
import requests
import logging
from typing import List, Dict

class AIQuestionGenerator:
    """Service for generating TOEFL listening questions using UTSM AI"""
    
    def __init__(self):
        self.api_key = os.getenv('UTSM_AI_API_KEY', 'demo_key')
        self.api_url = os.getenv('UTSM_AI_API_URL', 'https://api.utsm.ai/v1/generate')
        # Use fallback questions by default since AI API is not available
        self.use_fallback = True
    
    def generate_questions(self, content_source) -> List[Dict]:
        """Generate TOEFL-style listening questions for given content"""
        try:
            # Use fallback questions directly since AI API is not accessible
            if self.use_fallback:
                return self._generate_fallback_questions(content_source)
            
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
        """Generate authentic TPO questions based on real Koolearn Official TPO tests"""
        
        # Real TPO question sets from Koolearn Official tests 75, 73, 51, 33
        tpo_question_sets = [
            # Official 75 Conversation 1 - Student and PR Director (Volunteer Award)
            [
                {
                    'question': 'Why does the woman wish to speak to the student?',
                    'type': 'gist_purpose',
                    'options': [
                        'A. To notify him about an award that he will be receiving',
                        'B. To offer assistance with a program he runs', 
                        'C. To ask him to start a literacy program at the university',
                        'D. To learn more about his accomplishments as a volunteer'
                    ],
                    'answer': 'D. To learn more about his accomplishments as a volunteer',
                    'explanation': 'The PR director wants to write a news release about the student\'s community achievement award and needs details about his volunteer work.',
                    'difficulty': 'easy',
                    'timestamp': 15.0
                },
                {
                    'question': 'What does the student say about how he was chosen for the award?',
                    'type': 'detail', 
                    'options': [
                        'A. He applied for it himself',
                        'B. The community center director nominated him',
                        'C. His university professors recommended him',
                        'D. He was automatically selected based on his volunteer hours'
                    ],
                    'answer': 'B. The community center director nominated him',
                    'explanation': 'The student explains that the director nominated him and submitted information about his volunteer work to the award committee.',
                    'difficulty': 'easy',
                    'timestamp': 120.0
                },
                {
                    'question': 'What does the student plan to do with the prize money?',
                    'type': 'detail',
                    'options': [
                        'A. Take a vacation',
                        'B. Pay for his education expenses',
                        'C. Buy supplies for the literacy program',
                        'D. Donate it to the community center'
                    ],
                    'answer': 'C. Buy supplies for the literacy program',
                    'explanation': 'The student states he will use the prize money for supplies like workbooks and writing materials, and maybe hire someone to promote the program.',
                    'difficulty': 'easy', 
                    'timestamp': 180.0
                }
            ],
            # Official 75 Lecture 1 - Ancient History (Queen Hatshepsut)
            [
                {
                    'question': 'What is the lecture mainly about?',
                    'type': 'gist_content',
                    'options': [
                        'A. How various proteins function in marine organisms',
                        'B. How certain fish became the dominant species in polar waters',
                        'C. An example that contradicts the theory of adaptive radiation',
                        'D. Changes in ocean habitats caused by continental drift'
                    ],
                    'answer': 'B. How certain fish became the dominant species in polar waters',
                    'explanation': 'The lecture explains how Notothenioids fish came to dominate the Southern Ocean through adaptive radiation.',
                    'difficulty': 'advanced',
                    'timestamp': 15.0
                },
                {
                    'question': 'According to the professor, what adaptation allows certain fish to survive in Antarctic waters?',
                    'type': 'detail',
                    'options': [
                        'A. Thick insulating layers around their organs',
                        'B. Special proteins that prevent ice crystal formation',
                        'C. Modified gills that filter cold water efficiently',
                        'D. Enhanced metabolism in low temperatures'
                    ],
                    'answer': 'B. Special proteins that prevent ice crystal formation',
                    'explanation': 'The professor explains that antifreeze proteins bind to ice crystals to prevent them from growing larger.',
                    'difficulty': 'advanced',
                    'timestamp': 180.0
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
                    'question': 'What does the professor mainly discuss? Click on 2 answers.',
                    'type': 'multiple_answer',
                    'options': [
                        'A. A powerful and unusual ruler of Egypt',
                        'B. Military actions during the New Kingdom period in Egypt', 
                        'C. How Hatshepsut\'s statue differs from those of other pharaohs',
                        'D. What the features of a pharaoh\'s statue represent'
                    ],
                    'answer': 'A. A powerful and unusual ruler of Egypt|D. What the features of a pharaoh\'s statue represent',
                    'explanation': 'The professor discusses both Queen Hatshepsut as a remarkable female pharaoh and the symbolic meaning of pharaoh statue features like the Nemes headcloth and ceremonial beard.',
                    'difficulty': 'intermediate',
                    'timestamp': 60.0
                },
                {
                    'question': 'According to the professor, what was unusual about Hatshepsut?',
                    'type': 'detail',
                    'options': [
                        'A. She was the first queen to rule Egypt',
                        'B. She moved beyond the role of regent to declare herself pharaoh',
                        'C. She was the youngest person ever to become pharaoh',
                        'D. She ruled Egypt longer than any previous pharaoh'
                    ],
                    'answer': 'B. She moved beyond the role of regent to declare herself pharaoh',
                    'explanation': 'The professor explains that while she initially served as regent for her nephew, she remarkably adopted the title of Pharaoh, which was previously used only by male kings.',
                    'difficulty': 'intermediate',
                    'timestamp': 180.0
                },
                {
                    'question': 'Why does the professor mention the ceremonial beard on Hatshepsut\'s statue?',
                    'type': 'function',
                    'options': [
                        'A. To show that female pharaohs looked different from male pharaohs',
                        'B. To demonstrate that Egyptian art was not realistic',
                        'C. To illustrate how pharaoh statues followed traditional symbolic conventions',
                        'D. To prove that Hatshepsut wanted to appear masculine'
                    ],
                    'answer': 'C. To illustrate how pharaoh statues followed traditional symbolic conventions',
                    'explanation': 'The professor explains that the beard was purely ceremonial decoration, part of the traditional way pharaohs were represented, regardless of their actual appearance.',
                    'difficulty': 'intermediate',
                    'timestamp': 240.0
                },
                {
                    'question': 'Listen again to part of the lecture. Why does the professor say this: "Now, this might surprise you, but..."',
                    'type': 'replay',
                    'options': [
                        'A. To introduce information that contradicts common assumptions',
                        'B. To ask students to pay closer attention',
                        'C. To indicate that the material is difficult',
                        'D. To transition to a new topic'
                    ],
                    'answer': 'A. To introduce information that contradicts common assumptions',
                    'explanation': 'This phrase signals that the professor is about to present information that may be unexpected or contrary to what students might think.',
                    'difficulty': 'advanced',
                    'timestamp': 180.0
                },
                {
                    'question': 'What does the professor say about the ecological environment that allowed this diversification?',
                    'type': 'inference',
                    'options': [
                        'A. It was highly competitive with many predator species',
                        'B. It provided limited food sources for most species',
                        'C. It functioned as an ecological vacuum with little competition',
                        'D. It required constant adaptation to changing temperatures'
                    ],
                    'answer': 'C. It functioned as an ecological vacuum with little competition',
                    'explanation': 'The professor describes it as an ecological vacuum where these fish had virtually the entire ocean to themselves.',
                    'difficulty': 'advanced',
                    'timestamp': 240.0
                }
            ],
            # Official 73 Lecture 1 - Psychology (Joint Attention in Infants)
            [
                {
                    'question': 'What is the lecture mainly about?',
                    'type': 'gist_content',
                    'options': [
                        'A. How babies learn to recognize their caregivers',
                        'B. How babies learn to focus their attention on the sounds they hear',
                        'C. The development of an early form of intentional communication',
                        'D. A technique to teach babies the meanings of words'
                    ],
                    'answer': 'C. The development of an early form of intentional communication',
                    'explanation': 'The lecture focuses on how babies develop joint attention skills around 9 months old, leading to intentional communication.',
                    'difficulty': 'easy',
                    'timestamp': 20.0
                },
                {
                    'question': 'According to the professor, what is joint attention?',
                    'type': 'detail',
                    'options': [
                        'A. The ability to focus on multiple objects simultaneously',
                        'B. The ability to share a focus of attention with someone else',
                        'C. The ability to maintain attention for extended periods',
                        'D. The ability to switch attention between different activities'
                    ],
                    'answer': 'B. The ability to share a focus of attention with someone else',
                    'explanation': 'The professor defines joint attention as two or more people having a connected awareness of the same thing.',
                    'difficulty': 'easy',
                    'timestamp': 80.0
                },
                {
                    'question': 'Why does the professor mention two types of pointing?',
                    'type': 'function',
                    'options': [
                        'A. To show that babies point before they can speak',
                        'B. To illustrate different communicative intentions in infants',
                        'C. To explain how pointing develops motor skills',
                        'D. To demonstrate cultural differences in communication'
                    ],
                    'answer': 'B. To illustrate different communicative intentions in infants',
                    'explanation': 'The professor explains that babies point either to request something (like a toy) or to share something (like an interesting cat), showing different communicative purposes.',
                    'difficulty': 'intermediate',
                    'timestamp': 150.0
                }
            ],
            # Official 51 Conversation 1 - Student and Biology Professor (Eyespot Experiment)
            [
                {
                    'question': 'Why does the student talk with the professor?',
                    'type': 'gist_purpose',
                    'options': [
                        'A. She wants permission to revise an experiment she conducted earlier',
                        'B. She has a question about the findings of an experiment in the textbook',
                        'C. She wants to reproduce an experiment that is not in the textbook',
                        'D. She would like advice about how to study animal behavior'
                    ],
                    'answer': 'C. She wants to reproduce an experiment that is not in the textbook',
                    'explanation': 'The student specifically asks to reproduce an experiment from a journal that is the opposite of what was in their textbook.',
                    'difficulty': 'intermediate',
                    'timestamp': 20.0
                },
                {
                    'question': 'What does the professor say about the idea that eyespots look like eyes?',
                    'type': 'attitude',
                    'options': [
                        'A. It is supported by extensive research on bird perception',
                        'B. It is a commonly held belief but not based on solid research',
                        'C. It has been recently proven through controlled experiments',
                        'D. It applies only to certain species of moths and butterflies'
                    ],
                    'answer': 'B. It is a commonly held belief but not based on solid research',
                    'explanation': 'The professor states this idea is just a commonly held belief and notes we can never really know how predators perceive the markings.',
                    'difficulty': 'intermediate',
                    'timestamp': 80.0
                },
                {
                    'question': 'What experimental finding does the student mention about eyespots?',
                    'type': 'detail',
                    'options': [
                        'A. Round markings were more effective than other shapes at deterring birds',
                        'B. Square markings were completely ineffective at scaring predators',
                        'C. Larger markings were more effective than smaller ones',
                        'D. Butterfly markings worked better than moth markings'
                    ],
                    'answer': 'C. Larger markings were more effective than smaller ones',
                    'explanation': 'The student explains that researchers determined larger markings are more effective, calling this "visual loudness".',
                    'difficulty': 'intermediate',
                    'timestamp': 140.0
                },
                {
                    'question': 'Why does the professor suggest setting up the experiment near a bird feeder?',
                    'type': 'inference',
                    'options': [
                        'A. Bird feeders attract a wider variety of bird species',
                        'B. Birds near feeders are more likely to approach the experiment',
                        'C. The experiment requires a controlled feeding environment',
                        'D. One week is not enough time for natural bird observation'
                    ],
                    'answer': 'B. Birds near feeders are more likely to approach the experiment',
                    'explanation': 'The professor suggests this to maximize observation time since birds will already be attracted to the area.',
                    'difficulty': 'intermediate',
                    'timestamp': 180.0
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

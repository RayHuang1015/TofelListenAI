import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app import db
from models import Score, Answer, Question, ContentSource, User, PracticeSession

class AIFeedbackService:
    """
    AI智能回饋服務 - 基於Koolearn評分和分析標準
    功能：
    1. 個性化學習建議
    2. 錯誤分析和解釋
    3. 學習路徑推薦
    4. 強弱點分析
    5. 進步策略制定
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # AI回饋配置
        self.feedback_config = {
            'performance_levels': {
                'excellent': {'min': 85, 'label': '優秀', 'color': 'success'},
                'good': {'min': 70, 'label': '良好', 'color': 'info'}, 
                'average': {'min': 60, 'label': '中等', 'color': 'warning'},
                'needs_improvement': {'min': 0, 'label': '需要提升', 'color': 'danger'}
            },
            'question_type_advice': {
                'gist_content': {
                    'tips': ['注意聽取講座的主題和核心觀點', '關注教授的引言和總結部分', '識別關鍵詞和轉折詞'],
                    'practice_focus': '主旨理解練習'
                },
                'gist_purpose': {
                    'tips': ['理解對話的目的和背景', '注意學生的請求或問題', '關注對話雙方的意圖'],
                    'practice_focus': '目的識別練習'
                },
                'detail': {
                    'tips': ['仔細聽取具體信息和數據', '注意時間、地點、人物等細節', '練習記筆記技巧'],
                    'practice_focus': '細節捕捉練習'
                },
                'function': {
                    'tips': ['理解教授說話的用意', '識別修辭手法和語言功能', '注意語調和重音'],
                    'practice_focus': '語言功能分析'
                },
                'attitude': {
                    'tips': ['注意說話者的語調和情感', '識別隱含的態度和觀點', '理解言外之意'],
                    'practice_focus': '態度識別練習'
                },
                'inference': {
                    'tips': ['基於聽到的內容進行邏輯推理', '結合上下文信息', '避免過度推測'],
                    'practice_focus': '推理能力訓練'
                }
            },
            'topic_strategies': {
                '心理学': '注意專業術語和實驗描述',
                '历史': '關注時間線和因果關係',
                '生物': '理解科學概念和過程',
                '地球科学': '掌握地質和環境術語',
                '天文学': '熟悉天體和物理概念',
                '美术': '了解藝術流派和技法',
                '文学': '理解文學作品和評論'
            }
        }
    
    def generate_comprehensive_feedback(self, score_id: int) -> Optional[Dict]:
        """生成全面的AI回饋報告"""
        
        score = Score.query.get(score_id)
        if not score:
            self.logger.error(f"Score {score_id} not found")
            return None
        
        # 解析分析數據
        try:
            analysis_data = json.loads(score.analysis) if score.analysis else {}
        except:
            analysis_data = {}
        
        # 生成各類回饋
        feedback = {
            'overall_assessment': self._generate_overall_assessment(score),
            'performance_breakdown': self._analyze_performance_breakdown(analysis_data),
            'personalized_recommendations': self._generate_personalized_recommendations(score, analysis_data),
            'learning_path': self._suggest_learning_path(score, analysis_data),
            'mistake_analysis': self._analyze_common_mistakes(score),
            'progress_insights': self._generate_progress_insights(score.user_id),
            'motivation_message': self._generate_motivation_message(score),
            'next_steps': self._recommend_next_steps(score, analysis_data)
        }
        
        return feedback
    
    def _generate_overall_assessment(self, score: Score) -> Dict:
        """生成整體評估"""
        
        percentage = score.percentage_score
        level = self._get_performance_level(percentage)
        
        assessment = {
            'score': score.total_score,
            'percentage': percentage,
            'level': level['label'],
            'level_color': level['color'],
            'summary': self._get_performance_summary(percentage),
            'comparison': self._get_score_comparison(score.user_id, percentage)
        }
        
        return assessment
    
    def _get_performance_level(self, percentage: float) -> Dict:
        """獲取表現等級"""
        for level_name, level_info in self.feedback_config['performance_levels'].items():
            if percentage >= level_info['min']:
                return level_info
        return self.feedback_config['performance_levels']['needs_improvement']
    
    def _get_performance_summary(self, percentage: float) -> str:
        """獲取表現總結"""
        if percentage >= 85:
            return "出色的表現！您已經掌握了托福聽力的核心技能，可以挑戰更高難度的內容。"
        elif percentage >= 70:
            return "良好的基礎！繼續保持，針對弱點進行專項練習將幫助您進一步提升。"
        elif percentage >= 60:
            return "有一定基礎，但還有提升空間。建議加強基礎聽力技能和答題策略。"
        else:
            return "需要加強基礎訓練。建議從簡單內容開始，循序漸進地提升聽力能力。"
    
    def _get_score_comparison(self, user_id: int, current_score: float) -> Dict:
        """獲取分數比較"""
        
        # 獲取用戶歷史分數
        recent_scores = Score.query.filter_by(user_id=user_id)\
            .order_by(Score.created_at.desc())\
            .limit(10).all()
        
        if len(recent_scores) < 2:
            return {'trend': 'insufficient_data'}
        
        prev_score = recent_scores[1].percentage_score
        improvement = current_score - prev_score
        
        return {
            'previous_score': prev_score,
            'improvement': improvement,
            'trend': 'improving' if improvement > 0 else 'declining' if improvement < 0 else 'stable'
        }
    
    def _analyze_performance_breakdown(self, analysis_data: Dict) -> Dict:
        """分析表現細分"""
        
        breakdown = {
            'by_question_type': {},
            'by_difficulty': {},
            'by_topic': {},
            'time_analysis': {}
        }
        
        # 題型表現分析
        question_types = analysis_data.get('detailed_analysis', {}).get('by_question_type', {})
        for q_type, stats in question_types.items():
            if stats.get('total', 0) > 0:
                accuracy = stats.get('accuracy', 0)
                breakdown['by_question_type'][q_type] = {
                    'accuracy': accuracy,
                    'performance': self._get_performance_level(accuracy * 100)['label'],
                    'advice': self.feedback_config['question_type_advice'].get(q_type, {})
                }
        
        # 難度表現分析
        by_difficulty = analysis_data.get('detailed_analysis', {}).get('by_difficulty', {})
        for difficulty, stats in by_difficulty.items():
            if stats.get('total', 0) > 0:
                accuracy = stats['correct'] / stats['total']
                breakdown['by_difficulty'][difficulty] = {
                    'accuracy': accuracy,
                    'correct': stats['correct'],
                    'total': stats['total']
                }
        
        # 話題表現分析
        by_topic = analysis_data.get('detailed_analysis', {}).get('by_topic', {})
        for topic, stats in by_topic.items():
            if stats.get('total', 0) > 0:
                accuracy = stats['correct'] / stats['total']
                breakdown['by_topic'][topic] = {
                    'accuracy': accuracy,
                    'strategy': self.feedback_config['topic_strategies'].get(topic, '加強該話題的詞彙和背景知識')
                }
        
        return breakdown
    
    def _generate_personalized_recommendations(self, score: Score, analysis_data: Dict) -> List[Dict]:
        """生成個性化建議"""
        
        recommendations = []
        
        # 基於整體表現的建議
        overall_rec = self._get_overall_recommendation(score.percentage_score)
        if overall_rec:
            recommendations.append(overall_rec)
        
        # 基於弱點的建議
        weakness_recs = self._get_weakness_recommendations(analysis_data)
        recommendations.extend(weakness_recs)
        
        # 基於時間管理的建議
        time_rec = self._get_time_management_recommendation(analysis_data)
        if time_rec:
            recommendations.append(time_rec)
        
        return recommendations
    
    def _get_overall_recommendation(self, percentage: float) -> Optional[Dict]:
        """獲取整體建議"""
        if percentage < 60:
            return {
                'type': 'foundation',
                'priority': 'high',
                'title': '加強基礎聽力訓練',
                'description': '建議從慢速材料開始，重點提升詞彙量和基礎理解能力',
                'action_items': [
                    '每天聽15-20分鐘慢速英語材料',
                    '積累托福聽力高頻詞彙',
                    '練習基礎的筆記技巧'
                ]
            }
        elif percentage < 75:
            return {
                'type': 'skill_building',
                'priority': 'medium',
                'title': '提升專項技能',
                'description': '針對特定題型和話題進行專項練習',
                'action_items': [
                    '重點練習弱勢題型',
                    '熟悉學術聽力的結構模式',
                    '提高答題速度和準確性'
                ]
            }
        return None
    
    def _get_weakness_recommendations(self, analysis_data: Dict) -> List[Dict]:
        """獲取弱點改進建議"""
        
        recommendations = []
        weaknesses = analysis_data.get('areas_for_improvement', [])
        
        for weakness in weaknesses[:3]:  # 最多3個主要弱點
            if '題型' in weakness:
                q_type = self._extract_question_type(weakness)
                if q_type and q_type in self.feedback_config['question_type_advice']:
                    advice = self.feedback_config['question_type_advice'][q_type]
                    recommendations.append({
                        'type': 'skill_improvement',
                        'priority': 'high',
                        'title': f'提升{q_type}題型能力',
                        'description': weakness,
                        'tips': advice['tips'],
                        'practice_focus': advice['practice_focus']
                    })
        
        return recommendations
    
    def _extract_question_type(self, weakness_text: str) -> Optional[str]:
        """從弱點描述中提取題型"""
        for q_type in self.feedback_config['question_type_advice'].keys():
            if q_type in weakness_text:
                return q_type
        return None
    
    def _get_time_management_recommendation(self, analysis_data: Dict) -> Optional[Dict]:
        """獲取時間管理建議"""
        
        performance = analysis_data.get('performance_summary', {})
        avg_time = performance.get('avg_time_per_question', 0)
        
        if avg_time > 90:
            return {
                'type': 'time_management',
                'priority': 'medium',
                'title': '提高答題效率',
                'description': f'當前平均每題用時{avg_time:.0f}秒，建議控制在60-75秒內',
                'strategies': [
                    '練習快速定位關鍵信息',
                    '提前預覽選項，了解題目重點',
                    '避免過度糾結單個題目'
                ]
            }
        
        return None
    
    def _suggest_learning_path(self, score: Score, analysis_data: Dict) -> Dict:
        """建議學習路徑"""
        
        current_level = self._get_performance_level(score.percentage_score)['label']
        
        # 基於當前水平制定學習路徑
        if score.percentage_score < 60:
            path = {
                'current_level': '基礎階段',
                'target_level': '中級水平',
                'estimated_time': '4-6週',
                'milestones': [
                    {'week': 1, 'goal': '掌握基礎詞彙和短對話理解', 'target_score': 45},
                    {'week': 2, 'goal': '提升講座主旨理解能力', 'target_score': 50},
                    {'week': 3, 'goal': '加強細節信息捕捉', 'target_score': 55},
                    {'week': 4, 'goal': '綜合能力提升', 'target_score': 60}
                ]
            }
        elif score.percentage_score < 80:
            path = {
                'current_level': '中級階段', 
                'target_level': '高級水平',
                'estimated_time': '3-4週',
                'milestones': [
                    {'week': 1, 'goal': '強化弱勢題型', 'target_score': score.percentage_score + 5},
                    {'week': 2, 'goal': '提升複雜推理能力', 'target_score': score.percentage_score + 10},
                    {'week': 3, 'goal': '掌握高難度學術內容', 'target_score': 80}
                ]
            }
        else:
            path = {
                'current_level': '高級階段',
                'target_level': '專家水平', 
                'estimated_time': '2-3週',
                'milestones': [
                    {'week': 1, 'goal': '保持穩定高分表現', 'target_score': 85},
                    {'week': 2, 'goal': '挑戰最高難度內容', 'target_score': 90}
                ]
            }
        
        return path
    
    def _analyze_common_mistakes(self, score: Score) -> List[Dict]:
        """分析常見錯誤"""
        
        # 獲取用戶在此session中的錯誤答案
        wrong_answers = Answer.query.join(Question).filter(
            Answer.practice_session_id == score.practice_session_id,
            Answer.answer_text != Question.correct_answer
        ).all()
        
        mistake_analysis = []
        
        for answer in wrong_answers[:5]:  # 分析前5個錯誤
            question = answer.question
            analysis = {
                'question_type': question.question_type,
                'user_answer': answer.answer_text,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation,
                'mistake_category': self._categorize_mistake(answer, question),
                'suggestion': self._get_mistake_suggestion(answer, question)
            }
            mistake_analysis.append(analysis)
        
        return mistake_analysis
    
    def _categorize_mistake(self, answer: Answer, question: Question) -> str:
        """分類錯誤類型"""
        
        # 簡化的錯誤分類邏輯
        if question.question_type == 'detail':
            return '細節理解錯誤'
        elif question.question_type in ['gist_content', 'gist_purpose']:
            return '主旨理解錯誤'
        elif question.question_type == 'inference':
            return '推理判斷錯誤'
        else:
            return '其他理解錯誤'
    
    def _get_mistake_suggestion(self, answer: Answer, question: Question) -> str:
        """獲取錯誤改進建議"""
        
        suggestions = {
            '細節理解錯誤': '建議提高注意力集中度，練習記筆記技巧',
            '主旨理解錯誤': '注意聽取開頭和結尾的總結性語句',
            '推理判斷錯誤': '基於聽到的內容進行邏輯推理，避免主觀臆斷',
            '其他理解錯誤': '加強整體聽力理解能力'
        }
        
        category = self._categorize_mistake(answer, question)
        return suggestions.get(category, '建議多加練習該類題型')
    
    def _generate_progress_insights(self, user_id: int) -> Dict:
        """生成進步洞察"""
        
        # 獲取最近10次練習記錄
        recent_scores = Score.query.filter_by(user_id=user_id)\
            .order_by(Score.created_at.desc())\
            .limit(10).all()
        
        if len(recent_scores) < 3:
            return {'message': '需要更多練習記錄才能分析進步趨勢'}
        
        scores = [s.percentage_score for s in reversed(recent_scores)]
        
        insights = {
            'trend_analysis': self._analyze_score_trend(scores),
            'consistency': self._calculate_score_consistency(scores),
            'improvement_rate': self._calculate_improvement_rate(scores),
            'peak_performance': max(scores),
            'recent_average': sum(scores[-3:]) / 3
        }
        
        return insights
    
    def _analyze_score_trend(self, scores: List[float]) -> str:
        """分析分數趨勢"""
        if len(scores) < 3:
            return '數據不足'
        
        recent_trend = scores[-3:]
        if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
            return '持續上升'
        elif all(recent_trend[i] >= recent_trend[i+1] for i in range(len(recent_trend)-1)):
            return '持續下降'
        else:
            return '波動中'
    
    def _calculate_score_consistency(self, scores: List[float]) -> float:
        """計算分數一致性"""
        if len(scores) < 2:
            return 1.0
        
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        return max(0, 1 - (std_dev / 100))
    
    def _calculate_improvement_rate(self, scores: List[float]) -> float:
        """計算改進速率"""
        if len(scores) < 2:
            return 0
        
        return (scores[-1] - scores[0]) / len(scores)
    
    def _generate_motivation_message(self, score: Score) -> str:
        """生成激勵訊息"""
        
        percentage = score.percentage_score
        
        if percentage >= 85:
            messages = [
                "恭喜！您的表現非常出色，已經達到了托福聽力的高水準！",
                "太棒了！繼續保持這種優秀的狀態，您一定能在真實考試中取得好成績！",
                "您的聽力能力已經相當強了，可以嘗試挑戰更複雜的內容！"
            ]
        elif percentage >= 70:
            messages = [
                "很好的進步！您已經建立了良好的聽力基礎。",
                "表現不錯！繼續努力，您離目標越來越近了！",
                "您的聽力能力正在穩步提升，保持這種學習節奏！"
            ]
        elif percentage >= 60:
            messages = [
                "不錯的開始！每一次練習都是進步的機會。",
                "您正在進步中，請保持耐心和持續的練習！",
                "基礎正在打牢，繼續努力一定會看到明顯的提升！"
            ]
        else:
            messages = [
                "學習是一個過程，每一次練習都很有價值！",
                "不要灰心，持續練習是提升聽力的關鍵！",
                "您已經踏出了重要的第一步，繼續加油！"
            ]
        
        import random
        return random.choice(messages)
    
    def _recommend_next_steps(self, score: Score, analysis_data: Dict) -> List[Dict]:
        """推薦下一步行動"""
        
        next_steps = []
        
        # 基於表現推薦內容難度
        if score.percentage_score < 60:
            next_steps.append({
                'action': 'practice_easy_content',
                'title': '練習基礎內容',
                'description': '選擇簡單難度的TPO對話和講座進行練習',
                'priority': 1
            })
        elif score.percentage_score < 80:
            next_steps.append({
                'action': 'focus_on_weak_types',
                'title': '針對弱項專練',
                'description': '重點練習表現不佳的題型',
                'priority': 1
            })
        
        # 推薦特定練習內容
        weaknesses = analysis_data.get('areas_for_improvement', [])
        if weaknesses:
            next_steps.append({
                'action': 'targeted_practice',
                'title': '專項提升練習',
                'description': f'重點練習：{", ".join(weaknesses[:2])}',
                'priority': 2
            })
        
        # 通用建議
        next_steps.append({
            'action': 'regular_practice',
            'title': '保持規律練習',
            'description': '建議每天練習20-30分鐘，保持聽力敏感度',
            'priority': 3
        })
        
        return sorted(next_steps, key=lambda x: x['priority'])
    
    def generate_quick_feedback(self, session_id: int) -> str:
        """生成快速回饋（用於即時顯示）"""
        
        session = db.session.query(PracticeSession).get(session_id)
        if not session or not session.final_score:
            return "練習完成！請查看詳細分析報告。"
        
        score_percentage = (session.final_score / 30) * 100
        
        if score_percentage >= 80:
            return f"太棒了！得分 {session.final_score}/30，您的聽力水平很高！"
        elif score_percentage >= 60:
            return f"不錯的表現！得分 {session.final_score}/30，繼續保持！"
        else:
            return f"得分 {session.final_score}/30，別灰心，每次練習都是進步的機會！"
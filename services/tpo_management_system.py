import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from flask import current_app
from app import db
from models import ContentSource, Question, PracticeSession, Answer, Score, User
from services.tpo_import_service import TPOImportService
from services.scoring_engine import ScoringEngine
from services.ai_feedback_service import AIFeedbackService

class TPOManagementSystem:
    """
    TPO聽力練習管理系統 - 整合Koolearn架構
    
    核心功能：
    1. 題目管理和匯入
    2. 練習Session管理
    3. 自動評分和分析
    4. AI智能回饋
    5. 進度跟踪
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.import_service = TPOImportService()
        self.scoring_engine = ScoringEngine()
        self.ai_feedback = AIFeedbackService()
    
    def initialize_tpo_system(self) -> Dict:
        """初始化完整的TPO系統"""
        
        try:
            self.logger.info("Starting TPO system initialization...")
            
            # 1. 匯入TPO結構
            import_stats = self.import_service.import_koolearn_tpo_structure()
            
            # 2. 驗證資料完整性
            validation_results = self._validate_system_data()
            
            # 3. 準備系統配置
            system_config = self._prepare_system_config()
            
            initialization_report = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'import_statistics': import_stats,
                'validation_results': validation_results,
                'system_config': system_config
            }
            
            self.logger.info(f"TPO system initialized successfully: {import_stats}")
            return initialization_report
            
        except Exception as e:
            self.logger.error(f"Error initializing TPO system: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def start_practice_session(self, user_id: int, content_source_id: int, 
                              practice_mode: str = 'sequential') -> Optional[PracticeSession]:
        """開始練習Session"""
        
        try:
            # 驗證內容來源
            content_source = ContentSource.query.get(content_source_id)
            if not content_source:
                self.logger.error(f"Content source {content_source_id} not found")
                return None
            
            # 創建新的練習Session
            session = PracticeSession(
                user_id=user_id,
                content_source_id=content_source_id,
                started_at=datetime.now(),
                metadata=json.dumps({
                    'practice_mode': practice_mode,
                    'tpo_format': True,
                    'koolearn_structure': True
                })
            )
            
            db.session.add(session)
            db.session.commit()
            
            self.logger.info(f"Started practice session {session.id} for user {user_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error starting practice session: {e}")
            db.session.rollback()
            return None
    
    def submit_answer(self, session_id: int, question_id: int, 
                     answer_text: str, time_spent: float = None) -> Optional[Answer]:
        """提交答案"""
        
        try:
            # 驗證Session
            session = PracticeSession.query.get(session_id)
            if not session or session.is_completed:
                self.logger.error(f"Invalid or completed session {session_id}")
                return None
            
            # 驗證問題
            question = Question.query.get(question_id)
            if not question:
                self.logger.error(f"Question {question_id} not found")
                return None
            
            # 檢查答案正確性
            is_correct = self._check_answer_correctness(answer_text, question.correct_answer)
            
            # 創建答案記錄
            answer = Answer(
                practice_session_id=session_id,
                question_id=question_id,
                answer_text=answer_text,
                is_correct=is_correct,
                time_spent=time_spent or 30.0,
                answered_at=datetime.now()
            )
            
            db.session.add(answer)
            
            # 更新Session統計
            self._update_session_progress(session)
            
            db.session.commit()
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Error submitting answer: {e}")
            db.session.rollback()
            return None
    
    def complete_practice_session(self, session_id: int) -> Optional[Dict]:
        """完成練習Session並生成評分回饋"""
        
        try:
            session = PracticeSession.query.get(session_id)
            if not session:
                self.logger.error(f"Session {session_id} not found")
                return None
            
            # 標記Session為完成
            session.is_completed = True
            session.completed_at = datetime.now()
            
            # 計算總時間
            if session.started_at:
                duration = (datetime.now() - session.started_at).total_seconds()
                session.duration = duration
            
            # 生成評分
            score = self.scoring_engine.calculate_session_score(session_id)
            if not score:
                self.logger.error(f"Failed to calculate score for session {session_id}")
                return None
            
            # 生成AI回饋
            ai_feedback = self.ai_feedback.generate_comprehensive_feedback(score.id)
            
            # 更新Session最終分數
            session.final_score = score.total_score
            
            db.session.commit()
            
            completion_report = {
                'session_id': session_id,
                'final_score': score.total_score,
                'percentage': score.percentage_score,
                'total_questions': score.total_questions,
                'correct_answers': score.correct_answers,
                'duration_minutes': (session.duration or 0) / 60,
                'ai_feedback': ai_feedback,
                'quick_feedback': self.ai_feedback.generate_quick_feedback(session_id)
            }
            
            self.logger.info(f"Completed session {session_id} with score {score.total_score}")
            return completion_report
            
        except Exception as e:
            self.logger.error(f"Error completing practice session: {e}")
            db.session.rollback()
            return None
    
    def get_practice_recommendations(self, user_id: int) -> Dict:
        """獲取個性化練習推薦"""
        
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # 獲取用戶練習歷史
            recent_scores = Score.query.filter_by(user_id=user_id)\
                .order_by(Score.created_at.desc())\
                .limit(5).all()
            
            if not recent_scores:
                # 新用戶推薦
                return self._get_beginner_recommendations()
            
            # 分析用戶表現
            avg_score = sum(s.percentage_score for s in recent_scores) / len(recent_scores)
            latest_score = recent_scores[0]
            
            # 基於表現推薦內容
            recommendations = {
                'recommended_difficulty': self._recommend_difficulty(avg_score),
                'suggested_topics': self._recommend_topics(user_id),
                'practice_schedule': self._suggest_practice_schedule(user_id),
                'focus_areas': self._identify_focus_areas(recent_scores),
                'next_tpo_tests': self._recommend_next_tpo_tests(user_id, avg_score)
            }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting recommendations for user {user_id}: {e}")
            return {'error': 'Unable to generate recommendations'}
    
    def get_user_dashboard_data(self, user_id: int) -> Dict:
        """獲取用戶儀表板數據"""
        
        try:
            # 基本統計
            total_sessions = PracticeSession.query.filter_by(
                user_id=user_id, is_completed=True
            ).count()
            
            total_questions = db.session.query(Answer).join(PracticeSession).filter(
                PracticeSession.user_id == user_id
            ).count()
            
            correct_answers = db.session.query(Answer).join(PracticeSession).filter(
                PracticeSession.user_id == user_id,
                Answer.is_correct == True
            ).count()
            
            # 最近成績
            recent_scores = Score.query.filter_by(user_id=user_id)\
                .order_by(Score.created_at.desc())\
                .limit(10).all()
            
            # 表現分析
            performance_analysis = self._analyze_user_performance(user_id)
            
            dashboard_data = {
                'basic_stats': {
                    'total_sessions': total_sessions,
                    'total_questions': total_questions,
                    'correct_answers': correct_answers,
                    'overall_accuracy': (correct_answers / total_questions * 100) if total_questions > 0 else 0
                },
                'recent_scores': [
                    {
                        'date': score.created_at.strftime('%Y-%m-%d'),
                        'score': score.total_score,
                        'percentage': score.percentage_score
                    } for score in recent_scores
                ],
                'performance_analysis': performance_analysis,
                'achievement_badges': self._get_achievement_badges(user_id),
                'learning_streak': self._calculate_learning_streak(user_id)
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data for user {user_id}: {e}")
            return {'error': 'Unable to load dashboard data'}
    
    def _validate_system_data(self) -> Dict:
        """驗證系統資料完整性"""
        
        validation = {
            'tpo_content_count': ContentSource.query.filter_by(type='tpo').count(),
            'total_questions': Question.query.join(ContentSource).filter(
                ContentSource.type == 'tpo'
            ).count(),
            'difficulty_distribution': {},
            'topic_distribution': {}
        }
        
        # 難度分佈
        for difficulty in ['easy', 'intermediate', 'advanced']:
            count = ContentSource.query.filter_by(
                type='tpo', 
                difficulty_level=difficulty
            ).count()
            validation['difficulty_distribution'][difficulty] = count
        
        # 話題分佈
        topic_counts = db.session.query(
            ContentSource.topic, 
            db.func.count(ContentSource.id)
        ).filter_by(type='tpo').group_by(ContentSource.topic).all()
        
        validation['topic_distribution'] = dict(topic_counts)
        
        return validation
    
    def _prepare_system_config(self) -> Dict:
        """準備系統配置"""
        
        return {
            'supported_difficulties': ['easy', 'intermediate', 'advanced'],
            'supported_question_types': [
                'gist_content', 'gist_purpose', 'detail', 
                'function', 'attitude', 'inference', 'multiple_answer'
            ],
            'scoring_enabled': True,
            'ai_feedback_enabled': True,
            'progress_tracking_enabled': True
        }
    
    def _check_answer_correctness(self, user_answer: str, correct_answer: str) -> bool:
        """檢查答案正確性"""
        
        user_answer = user_answer.strip().upper()
        correct_answer = correct_answer.strip().upper()
        
        # 處理多選題
        if '|' in correct_answer:
            correct_options = set(opt.strip() for opt in correct_answer.split('|'))
            user_options = set(opt.strip() for opt in user_answer.split('|'))
            return user_options == correct_options
        
        # 單選題
        return user_answer == correct_answer
    
    def _update_session_progress(self, session: PracticeSession):
        """更新Session進度"""
        
        total_answers = Answer.query.filter_by(
            practice_session_id=session.id
        ).count()
        
        # 獲取該內容來源的總題目數
        expected_questions = Question.query.filter_by(
            content_source_id=session.content_source_id
        ).count()
        
        # 更新Session metadata
        metadata = json.loads(session.metadata or '{}')
        metadata.update({
            'answered_questions': total_answers,
            'expected_questions': expected_questions,
            'progress_percentage': (total_answers / expected_questions * 100) if expected_questions > 0 else 0
        })
        session.metadata = json.dumps(metadata)
    
    def _get_beginner_recommendations(self) -> Dict:
        """獲取新手推薦"""
        
        return {
            'recommended_difficulty': 'easy',
            'suggested_topics': ['志愿申请', '食宿', '心理学'],
            'practice_schedule': '每天15-20分鐘',
            'focus_areas': ['基礎聽力理解', '詞彙積累'],
            'next_tpo_tests': ['Official 1 Con1', 'Official 1 Con2']
        }
    
    def _recommend_difficulty(self, avg_score: float) -> str:
        """推薦難度等級"""
        
        if avg_score >= 80:
            return 'advanced'
        elif avg_score >= 60:
            return 'intermediate'
        else:
            return 'easy'
    
    def _recommend_topics(self, user_id: int) -> List[str]:
        """推薦話題"""
        
        # 獲取用戶表現較差的話題
        weak_topics = db.session.query(
            ContentSource.topic,
            db.func.avg(Score.percentage_score).label('avg_score')
        ).join(PracticeSession).join(Score).filter(
            Score.user_id == user_id
        ).group_by(ContentSource.topic).having(
            db.func.avg(Score.percentage_score) < 70
        ).order_by('avg_score').limit(3).all()
        
        if weak_topics:
            return [topic[0] for topic in weak_topics]
        
        # 默認推薦
        return ['心理学', '历史', '动物']
    
    def _suggest_practice_schedule(self, user_id: int) -> str:
        """建議練習時間表"""
        
        # 基於用戶活躍度建議
        recent_sessions = PracticeSession.query.filter_by(user_id=user_id)\
            .filter(PracticeSession.started_at >= datetime.now().replace(
                day=datetime.now().day-7
            )).count()
        
        if recent_sessions >= 5:
            return '保持當前節奏，每天練習'
        elif recent_sessions >= 2:
            return '建議增加到每天練習20-30分鐘'
        else:
            return '建議每天至少練習15分鐘'
    
    def _identify_focus_areas(self, scores: List[Score]) -> List[str]:
        """識別重點改進領域"""
        
        focus_areas = []
        
        if scores:
            avg_score = sum(s.percentage_score for s in scores) / len(scores)
            
            if avg_score < 60:
                focus_areas.extend(['基礎聽力理解', '詞彙積累'])
            elif avg_score < 80:
                focus_areas.extend(['特定題型練習', '答題速度'])
            else:
                focus_areas.extend(['高難度內容', '一致性保持'])
        
        return focus_areas
    
    def _recommend_next_tpo_tests(self, user_id: int, avg_score: float) -> List[str]:
        """推薦下一個TPO測試"""
        
        # 根據分數推薦合適的TPO範圍
        if avg_score >= 80:
            tpo_range = '75-70'  # 最新最難的測試
        elif avg_score >= 60:
            tpo_range = '50-41'  # 中等難度
        else:
            tpo_range = '30-21'  # 較簡單的測試
        
        # 獲取該範圍內用戶未做過的測試
        completed_content = db.session.query(ContentSource.name).join(
            PracticeSession
        ).filter(
            PracticeSession.user_id == user_id,
            PracticeSession.is_completed == True,
            ContentSource.type == 'tpo'
        ).subquery()
        
        available_tests = ContentSource.query.filter(
            ContentSource.type == 'tpo',
            ~ContentSource.name.in_(completed_content)
        ).limit(5).all()
        
        return [test.name for test in available_tests]
    
    def _analyze_user_performance(self, user_id: int) -> Dict:
        """分析用戶表現"""
        
        # 獲取最近的分數記錄
        scores = Score.query.filter_by(user_id=user_id)\
            .order_by(Score.created_at.desc())\
            .limit(10).all()
        
        if not scores:
            return {'message': 'No performance data available'}
        
        performance_data = [s.percentage_score for s in reversed(scores)]
        
        return {
            'trend': 'improving' if performance_data[-1] > performance_data[0] else 'stable',
            'average_score': sum(performance_data) / len(performance_data),
            'best_score': max(performance_data),
            'consistency': self._calculate_consistency(performance_data),
            'recent_improvement': performance_data[-1] - performance_data[0] if len(performance_data) > 1 else 0
        }
    
    def _calculate_consistency(self, scores: List[float]) -> float:
        """計算分數一致性"""
        if len(scores) < 2:
            return 1.0
        
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        return max(0, 1 - (std_dev / 100))
    
    def _get_achievement_badges(self, user_id: int) -> List[Dict]:
        """獲取成就徽章"""
        
        badges = []
        
        # 總Session數徽章
        total_sessions = PracticeSession.query.filter_by(
            user_id=user_id, is_completed=True
        ).count()
        
        if total_sessions >= 100:
            badges.append({'name': '練習達人', 'description': '完成100次練習'})
        elif total_sessions >= 50:
            badges.append({'name': '努力學習', 'description': '完成50次練習'})
        elif total_sessions >= 10:
            badges.append({'name': '初學有成', 'description': '完成10次練習'})
        
        # 高分徽章
        high_scores = Score.query.filter(
            Score.user_id == user_id,
            Score.percentage_score >= 85
        ).count()
        
        if high_scores >= 10:
            badges.append({'name': '聽力高手', 'description': '獲得10次85分以上成績'})
        elif high_scores >= 5:
            badges.append({'name': '表現優異', 'description': '獲得5次85分以上成績'})
        
        return badges
    
    def _calculate_learning_streak(self, user_id: int) -> int:
        """計算學習連續天數"""
        
        # 獲取最近30天的練習記錄
        from datetime import timedelta
        
        sessions = PracticeSession.query.filter(
            PracticeSession.user_id == user_id,
            PracticeSession.is_completed == True,
            PracticeSession.started_at >= datetime.now() - timedelta(days=30)
        ).order_by(PracticeSession.started_at.desc()).all()
        
        if not sessions:
            return 0
        
        # 簡化的連續天數計算
        unique_dates = set(s.started_at.date() for s in sessions)
        return len(unique_dates)
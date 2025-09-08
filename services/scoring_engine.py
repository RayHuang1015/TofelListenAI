import logging
from typing import Dict, List
from models import Answer, Question, PracticeSession

class ScoringEngine:
    """Service for scoring practice sessions and providing detailed feedback"""
    
    def analyze_performance(self, practice_session: PracticeSession) -> Dict:
        """Analyze user performance and provide detailed feedback"""
        try:
            answers = Answer.query.filter_by(session_id=practice_session.id).all()
            
            # Calculate basic metrics
            total_questions = len(answers)
            correct_answers = sum(1 for a in answers if a.is_correct)
            accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            # Analyze by question type
            question_type_analysis = self._analyze_by_question_type(answers)
            
            # Analyze timing patterns
            timing_analysis = self._analyze_timing(answers)
            
            # Identify strengths and weaknesses
            strengths = self._identify_strengths(answers, accuracy)
            weaknesses = self._identify_weaknesses(answers, accuracy)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(strengths, weaknesses, timing_analysis)
            
            feedback = {
                'accuracy': accuracy,
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'question_type_analysis': question_type_analysis,
                'timing_analysis': timing_analysis,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'recommendations': recommendations,
                'performance_level': self._determine_performance_level(accuracy)
            }
            
            return feedback
            
        except Exception as e:
            logging.error(f"Error analyzing performance: {e}")
            return self._generate_default_feedback()
    
    def _analyze_by_question_type(self, answers: List[Answer]) -> Dict:
        """Analyze performance by question type"""
        type_stats = {}
        
        for answer in answers:
            question = Question.query.get(answer.question_id)
            q_type = question.question_type
            
            if q_type not in type_stats:
                type_stats[q_type] = {'total': 0, 'correct': 0}
            
            type_stats[q_type]['total'] += 1
            if answer.is_correct:
                type_stats[q_type]['correct'] += 1
        
        # Calculate accuracy for each type
        for q_type in type_stats:
            total = type_stats[q_type]['total']
            correct = type_stats[q_type]['correct']
            type_stats[q_type]['accuracy'] = (correct / total * 100) if total > 0 else 0
        
        return type_stats
    
    def _analyze_timing(self, answers: List[Answer]) -> Dict:
        """Analyze timing patterns"""
        times = [a.time_taken for a in answers if a.time_taken]
        
        if not times:
            return {'average_time': 0, 'fastest': 0, 'slowest': 0}
        
        return {
            'average_time': sum(times) / len(times),
            'fastest': min(times),
            'slowest': max(times),
            'total_time': sum(times)
        }
    
    def _identify_strengths(self, answers: List[Answer], overall_accuracy: float) -> List[str]:
        """Identify user's strengths"""
        strengths = []
        
        if overall_accuracy >= 80:
            strengths.append("Excellent overall comprehension")
        elif overall_accuracy >= 65:
            strengths.append("Good listening comprehension")
        
        # Analyze timing
        times = [a.time_taken for a in answers if a.time_taken]
        if times:
            avg_time = sum(times) / len(times)
            if avg_time < 30:  # Less than 30 seconds per question
                strengths.append("Quick response time")
        
        # Analyze question types
        correct_types = []
        for answer in answers:
            if answer.is_correct:
                question = Question.query.get(answer.question_id)
                correct_types.append(question.question_type)
        
        type_counts = {}
        for q_type in correct_types:
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        if type_counts.get('multiple_choice', 0) >= 3:
            strengths.append("Strong performance on multiple choice questions")
        
        return strengths if strengths else ["Completed the practice session"]
    
    def _identify_weaknesses(self, answers: List[Answer], overall_accuracy: float) -> List[str]:
        """Identify areas for improvement"""
        weaknesses = []
        
        if overall_accuracy < 50:
            weaknesses.append("Overall listening comprehension needs improvement")
        elif overall_accuracy < 65:
            weaknesses.append("Moderate listening comprehension - room for improvement")
        
        # Analyze incorrect answers
        incorrect_answers = [a for a in answers if not a.is_correct]
        if len(incorrect_answers) > len(answers) * 0.5:  # More than 50% incorrect
            weaknesses.append("Difficulty with main idea questions")
        
        # Analyze timing issues
        times = [a.time_taken for a in answers if a.time_taken]
        if times:
            avg_time = sum(times) / len(times)
            if avg_time > 90:  # More than 90 seconds per question
                weaknesses.append("Taking too much time per question")
        
        return weaknesses if weaknesses else ["Minor areas for improvement"]
    
    def _generate_recommendations(self, strengths: List[str], weaknesses: List[str], timing_analysis: Dict) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Based on weaknesses
        if "Overall listening comprehension needs improvement" in weaknesses:
            recommendations.extend([
                "Practice with easier content first (beginner level)",
                "Focus on vocabulary building",
                "Listen to English content daily for at least 30 minutes"
            ])
        
        if "Taking too much time per question" in weaknesses:
            recommendations.extend([
                "Practice time management during listening exercises",
                "Try to answer questions while listening, not after",
                "Work on quick note-taking skills"
            ])
        
        if "Difficulty with main idea questions" in weaknesses:
            recommendations.extend([
                "Practice identifying topic sentences and main ideas",
                "Focus on the introduction and conclusion of audio content",
                "Practice summarizing short audio clips"
            ])
        
        # General recommendations
        recommendations.extend([
            "Continue regular practice with varied content types",
            "Try content from different sources (news, academic, casual)",
            "Practice with content at your current level before advancing"
        ])
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _determine_performance_level(self, accuracy: float) -> str:
        """Determine performance level based on accuracy"""
        if accuracy >= 85:
            return "Excellent"
        elif accuracy >= 70:
            return "Good"
        elif accuracy >= 55:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _generate_default_feedback(self) -> Dict:
        """Generate default feedback when analysis fails"""
        return {
            'accuracy': 0,
            'total_questions': 0,
            'correct_answers': 0,
            'question_type_analysis': {},
            'timing_analysis': {'average_time': 0, 'fastest': 0, 'slowest': 0},
            'strengths': ["Completed the practice session"],
            'weaknesses': ["Analysis unavailable"],
            'recommendations': ["Try another practice session", "Check your internet connection"],
            'performance_level': "Unknown"
        }

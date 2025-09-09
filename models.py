from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Text, JSON

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    practice_sessions = db.relationship('PracticeSession', backref='user', lazy=True)
    scores = db.relationship('Score', backref='user', lazy=True)

class ContentSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # TPO, TED, CNN, BBC, etc.
    type = db.Column(db.String(20), nullable=False)  # audio, video, podcast
    url = db.Column(db.String(500))
    description = db.Column(Text)
    difficulty_level = db.Column(db.String(20))  # beginner, intermediate, advanced
    duration = db.Column(db.Integer)  # in seconds
    topic = db.Column(db.String(100))
    content_metadata = db.Column(JSON)  # For storing additional metadata like TPO structure
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    practice_sessions = db.relationship('PracticeSession', backref='content', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content_source.id'), nullable=False)
    question_text = db.Column(Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # multiple_choice, fill_blank, etc.
    options = db.Column(JSON)  # For multiple choice options
    correct_answer = db.Column(Text, nullable=False)
    explanation = db.Column(Text)
    difficulty = db.Column(db.String(20))
    audio_timestamp = db.Column(db.Float)  # When in audio this question relates to
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True)

class PracticeSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('content_source.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer, default=0)
    score_percentage = db.Column(db.Float)
    time_spent = db.Column(db.Integer)  # in seconds
    
    # Relationships
    answers = db.relationship('Answer', backref='session', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('practice_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(Text)
    is_correct = db.Column(db.Boolean)
    time_taken = db.Column(db.Integer)  # in seconds
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_source = db.Column(db.String(50))
    topic = db.Column(db.String(100))
    score = db.Column(db.Float)
    max_score = db.Column(db.Float)
    strengths = db.Column(JSON)
    weaknesses = db.Column(JSON)
    recommendations = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

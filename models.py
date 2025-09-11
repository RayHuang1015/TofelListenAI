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
    name = db.Column(db.String(50), nullable=False)  # TPO, TED, CNN, BBC, ABC News, etc.
    type = db.Column(db.String(20), nullable=False)  # audio, video, podcast, news
    url = db.Column(db.String(500))
    description = db.Column(Text)
    difficulty_level = db.Column(db.String(20))  # beginner, intermediate, advanced
    duration = db.Column(db.Integer)  # in seconds
    topic = db.Column(db.String(100))
    category = db.Column(db.String(50))  # For news: politics, business, technology, etc.
    published_date = db.Column(db.DateTime)  # For news content
    content_metadata = db.Column(JSON)  # For storing additional metadata like TPO structure
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    practice_sessions = db.relationship('PracticeSession', backref='content', lazy=True)
    
    # Extended fields for international news system
    transcript_text = db.Column(Text)  # Full transcript
    language = db.Column(db.String(10), default='en')  # Language code
    region = db.Column(db.String(50))  # Geographic region 
    license_info = db.Column(db.String(200))  # License/attribution info
    source_ref = db.Column(db.Integer, db.ForeignKey('provider_source.id'))  # Reference to provider
    
    # Constraints to prevent duplicates
    __table_args__ = (
        # Unique constraint for URL to prevent duplicate content
        db.UniqueConstraint('url', name='unique_content_url'),
        # Add index for better query performance on content by date and name
        db.Index('idx_content_date_name', 'name', 'published_date'),
    )

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


# International News System Models

class ProviderSource(db.Model):
    """News providers (BBC, CNN, Reuters, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)  # 'bbc_world', 'cnn_international'
    name = db.Column(db.String(100), nullable=False)  # 'BBC World News'
    type = db.Column(db.String(20), nullable=False)  # 'rss', 'api', 'video'
    base_url = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True)
    provider_metadata = db.Column(JSON)  # API keys, feed URLs, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships will be established through EditionSegment


class DailyEdition(db.Model):
    """3-hour daily international news compilation"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # Edition date
    edition_number = db.Column(db.Integer, default=1)  # Multiple editions per day (1-8 for every 3 hours)
    
    # Unique constraint for one edition per date+slot
    __table_args__ = (
        db.UniqueConstraint('date', 'edition_number', name='unique_daily_edition'),
        db.Index('idx_edition_date', 'date'),
    )
    title = db.Column(db.String(200), nullable=False)
    total_duration_sec = db.Column(db.Integer, default=0)  # Target: 3 hours = 10800 seconds
    word_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='draft')  # 'draft', 'ready', 'failed'
    edition_metadata = db.Column(JSON)  # Statistics, sources used, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    segments = db.relationship('EditionSegment', backref='edition', lazy=True, cascade='all, delete-orphan')


class EditionSegment(db.Model):
    """Individual news segment within a daily edition"""
    id = db.Column(db.Integer, primary_key=True)
    edition_id = db.Column(db.Integer, db.ForeignKey('daily_edition.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider_source.id'), nullable=False)
    source_content_id = db.Column(db.Integer, db.ForeignKey('content_source.id'), nullable=True)
    
    seq = db.Column(db.Integer, nullable=False)  # Order within edition
    start_sec = db.Column(db.Integer, default=0)  # Start time in 3-hour compilation
    duration_sec = db.Column(db.Integer, nullable=False)
    
    headline = db.Column(db.String(300), nullable=False)
    region = db.Column(db.String(50))  # 'global', 'europe', 'asia', etc.
    category = db.Column(db.String(50))  # 'politics', 'business', 'technology'
    
    transcript_text = db.Column(Text)  # Full transcript for this segment
    summary = db.Column(JSON)  # AI-generated summary and key points
    segment_metadata = db.Column(JSON)  # Original source, timestamps, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints and indexes for EditionSegment
    __table_args__ = (
        db.UniqueConstraint('edition_id', 'seq', name='unique_segment_order'),
        db.Index('idx_segment_edition_seq', 'edition_id', 'seq'),
        db.Index('idx_segment_provider', 'provider_id'),
    )
    
    # Relationships
    provider = db.relationship('ProviderSource', backref=db.backref('segments', lazy=True))
    source_content = db.relationship('ContentSource', backref=db.backref('edition_segments', lazy=True))


class IngestionJob(db.Model):
    """Track data ingestion processes"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'running', 'completed', 'failed'
    attempts = db.Column(db.Integer, default=0)
    last_error = db.Column(Text)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    stats = db.Column(JSON)  # Sources processed, items found, etc.
    lock_token = db.Column(db.String(100))  # Prevent concurrent processing
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints and indexes for performance and data integrity
    __table_args__ = (
        db.UniqueConstraint('date', name='unique_ingestion_date'),
        db.Index('idx_ingestionjob_status_date', 'status', 'date'),
        db.Index('idx_ingestion_date_status', 'date', 'status'),
    )

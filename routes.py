from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app, db
from models import User, ContentSource, Question, PracticeSession, Answer, Score
from services.content_integration import ContentIntegrationService
from services.ai_question_generator import AIQuestionGenerator
from services.scoring_engine import ScoringEngine
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

@app.route('/')
def index():
    """Home page with overview and quick start options"""
    recent_content = ContentSource.query.order_by(ContentSource.created_at.desc()).limit(6).all()
    user_id = session.get('user_id')
    recent_scores = []
    
    if user_id:
        recent_scores = Score.query.filter_by(user_id=user_id).order_by(Score.created_at.desc()).limit(3).all()
    
    return render_template('index.html', recent_content=recent_content, recent_scores=recent_scores)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        password_hash = generate_password_hash(password)
        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        flash('Registration successful!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard with progress and analytics"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    recent_sessions = PracticeSession.query.filter_by(user_id=user_id).order_by(PracticeSession.started_at.desc()).limit(5).all()
    scores = Score.query.filter_by(user_id=user_id).all()
    
    # Calculate statistics
    total_sessions = len(user.practice_sessions)
    avg_score = sum(s.score for s in scores) / len(scores) if scores else 0
    
    return render_template('dashboard.html', 
                         user=user, 
                         recent_sessions=recent_sessions,
                         total_sessions=total_sessions,
                         avg_score=avg_score,
                         scores=scores)

@app.route('/content')
def content_library():
    """Browse available content sources"""
    source_type = request.args.get('type', '')
    difficulty = request.args.get('difficulty', '')
    topic = request.args.get('topic', '')
    
    query = ContentSource.query
    
    if source_type:
        query = query.filter(ContentSource.name.contains(source_type))
    if difficulty:
        query = query.filter_by(difficulty_level=difficulty)
    if topic:
        query = query.filter(ContentSource.topic.contains(topic))
    
    content_items = query.all()
    
    # Get unique values for filters
    sources = db.session.query(ContentSource.name).distinct().all()
    difficulties = db.session.query(ContentSource.difficulty_level).distinct().all()
    topics = db.session.query(ContentSource.topic).distinct().all()
    
    return render_template('content_library.html',
                         content_items=content_items,
                         sources=[s[0] for s in sources if s[0]],
                         difficulties=[d[0] for d in difficulties if d[0]],
                         topics=[t[0] for t in topics if t[0]])

@app.route('/practice/<int:content_id>')
def practice(content_id):
    """Start a practice session with specific content"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    content = ContentSource.query.get_or_404(content_id)
    
    # Create new practice session
    practice_session = PracticeSession(user_id=user_id, content_id=content_id)
    db.session.add(practice_session)
    db.session.commit()
    
    # Generate questions using AI
    try:
        ai_generator = AIQuestionGenerator()
        questions = ai_generator.generate_questions(content)
        
        # Save generated questions
        for q_data in questions:
            question = Question(
                content_id=content_id,
                question_text=q_data['question'],
                question_type=q_data['type'],
                options=q_data.get('options'),
                correct_answer=q_data['answer'],
                explanation=q_data.get('explanation'),
                difficulty=q_data.get('difficulty', 'intermediate'),
                audio_timestamp=q_data.get('timestamp')
            )
            db.session.add(question)
        
        db.session.commit()
        practice_session.total_questions = len(questions)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error generating questions: {e}")
        flash('Error generating questions. Please try again.', 'error')
        return redirect(url_for('content_library'))
    
    # Get questions for this content
    questions = Question.query.filter_by(content_id=content_id).all()
    
    # Convert questions to JSON-serializable format
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'options': q.options or [],
            'correct_answer': q.correct_answer,
            'explanation': q.explanation or '',
            'difficulty': q.difficulty or 'intermediate',
            'audio_timestamp': q.audio_timestamp or 0.0
        })
    
    return render_template('practice.html', 
                         content=content, 
                         questions=questions,
                         questions_data=questions_data,
                         session_id=practice_session.id)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Submit an answer during practice"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    session_id = request.form['session_id']
    question_id = request.form['question_id']
    user_answer = request.form['answer']
    time_taken = int(request.form.get('time_taken', 0))
    
    question = Question.query.get(question_id)
    is_correct = user_answer.strip().lower() == question.correct_answer.strip().lower()
    
    # Save answer
    answer = Answer(
        session_id=session_id,
        question_id=question_id,
        user_answer=user_answer,
        is_correct=is_correct,
        time_taken=time_taken
    )
    db.session.add(answer)
    
    # Update session score
    practice_session = PracticeSession.query.get(session_id)
    if is_correct:
        practice_session.correct_answers += 1
    
    db.session.commit()
    
    return jsonify({
        'correct': is_correct,
        'explanation': question.explanation,
        'correct_answer': question.correct_answer
    })

@app.route('/complete_session/<int:session_id>')
def complete_session(session_id):
    """Complete a practice session and show results"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    practice_session = PracticeSession.query.get_or_404(session_id)
    
    # Calculate final score
    if practice_session.total_questions > 0:
        practice_session.score_percentage = (practice_session.correct_answers / practice_session.total_questions) * 100
    
    practice_session.completed_at = datetime.utcnow()
    
    # Generate detailed feedback using scoring engine
    scoring_engine = ScoringEngine()
    feedback = scoring_engine.analyze_performance(practice_session)
    
    # Save score record
    score = Score(
        user_id=user_id,
        content_source=practice_session.content.name,
        topic=practice_session.content.topic,
        score=practice_session.score_percentage,
        max_score=100,
        strengths=feedback['strengths'],
        weaknesses=feedback['weaknesses'],
        recommendations=feedback['recommendations']
    )
    db.session.add(score)
    db.session.commit()
    
    return render_template('results.html', 
                         session=practice_session,
                         feedback=feedback)

@app.route('/sync_content')
def sync_content():
    """Sync content from various sources"""
    try:
        content_service = ContentIntegrationService()
        
        # Sync from different sources
        tpo_count = content_service.sync_tpo_content()
        ted_count = content_service.sync_ted_content()
        news_count = content_service.sync_news_content()
        podcast_count = content_service.sync_podcast_content()
        discovery_count = content_service.sync_discovery_content()
        natgeo_count = content_service.sync_national_geographic_content()
        
        flash(f'Content synced: TPO({tpo_count}), TED({ted_count}), News({news_count}), Podcasts({podcast_count}), Discovery({discovery_count}), NatGeo({natgeo_count})', 'success')
        
    except Exception as e:
        logging.error(f"Error syncing content: {e}")
        flash('Error syncing content. Please try again later.', 'error')
    
    return redirect(url_for('content_library'))

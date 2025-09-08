# TOEFL Listening Practice Platform

## Overview

This is a Flask-based web application for TOEFL listening practice that provides AI-generated questions from multiple content sources including TPO tests, TED talks, news broadcasts, and podcasts. The platform uses UTSM AI to automatically generate TOEFL-style questions and provides detailed performance analytics and personalized feedback to help users improve their listening skills.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Main web framework chosen for its simplicity and rapid development capabilities
- **SQLAlchemy**: ORM for database operations with declarative base model structure
- **Werkzeug**: WSGI utilities including ProxyFix for handling proxied requests

### Database Design
- **SQLite/PostgreSQL**: Primary database with configurable DATABASE_URL environment variable
- **User Management**: User authentication with password hashing using Werkzeug security
- **Content Models**: ContentSource, Question, PracticeSession, Answer, and Score entities
- **JSON Fields**: Used for storing flexible question options and metadata

### AI Integration Services
- **AIQuestionGenerator**: Integrates with UTSM AI API for automated question generation
- **Content Processing**: Handles multiple content types (audio, video, podcast) with metadata extraction
- **Scoring Engine**: Provides detailed performance analysis with question type breakdown and timing analysis

### Content Management
- **Multi-source Integration**: TPO tests, TED talks, news sources, and podcasts
- **ContentIntegrationService**: Handles syncing content from external sources including YouTube API
- **AudioProcessor**: Processes audio files and extracts duration and format metadata

### Frontend Architecture
- **Jinja2 Templates**: Server-side rendering with Bootstrap dark theme
- **JavaScript Controllers**: Separate controllers for audio playback and practice sessions
- **Responsive Design**: Mobile-friendly interface with Bootstrap components
- **Real-time Audio**: HTML5 audio player with custom controls and speed adjustment

### Authentication & Sessions
- **Flask Sessions**: Session-based authentication using secure cookies
- **Password Security**: Werkzeug password hashing for secure credential storage
- **User Registration/Login**: Standard form-based authentication flow

### Performance Analytics
- **ScoringEngine**: Comprehensive analysis including accuracy, timing patterns, strengths/weaknesses
- **Dashboard**: Visual progress tracking with Chart.js integration
- **Question Type Analysis**: Performance breakdown by different TOEFL question categories

## External Dependencies

### AI Services
- **UTSM AI API**: Primary service for generating TOEFL-style questions from content
- **API Configuration**: Configurable via UTSM_AI_API_KEY and UTSM_AI_API_URL environment variables

### Content Sources
- **YouTube API**: For fetching TED talks and educational content (YOUTUBE_API_KEY)
- **News API**: For current news content integration (NEWS_API_KEY)
- **TPO Content**: Official TOEFL Practice Online materials

### Frontend Libraries
- **Bootstrap**: UI framework with Replit dark theme
- **Font Awesome**: Icon library for consistent UI elements
- **Chart.js**: JavaScript charting library for analytics visualization

### Development Tools
- **Flask-Login**: User session management (imported in models but not fully implemented)
- **Requests**: HTTP client for external API calls
- **Feedparser**: RSS/Atom feed parsing for content syndication

### Database
- **SQLAlchemy**: ORM with support for both SQLite (development) and PostgreSQL (production)
- **Connection Pooling**: Configured with pool_recycle and pool_pre_ping for reliability

### Audio Processing
- **HTML5 Audio**: Browser-native audio playback
- **Planned Integration**: Librosa/PyDub for advanced audio analysis (referenced but not implemented)
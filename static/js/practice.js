/**
 * Practice Session Controller for TOEFL Listening Practice
 * Handles question navigation, answer submission, and session management
 */

class PracticeSessionController {
    constructor() {
        this.sessionId = null;
        this.currentQuestion = 1;
        this.totalQuestions = 0;
        this.answers = {};
        this.startTime = null;
        this.sessionTimer = null;
        this.correctCount = 0;
        this.incorrectCount = 0;
        this.questionStartTime = null;
    }

    /**
     * Initialize the practice session
     */
    init(sessionData) {
        this.sessionId = sessionData.sessionId;
        this.totalQuestions = sessionData.totalQuestions;
        this.currentQuestion = sessionData.currentQuestion || 1;
        this.startTime = new Date();
        this.questionStartTime = new Date();
        
        this.setupEventListeners();
        this.updateProgress();
        this.updateQuestionNavigation();
        
        console.log(`Practice session initialized: ${this.totalQuestions} questions`);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) return; // Ignore Ctrl/Cmd combinations
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousQuestion();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextQuestion();
                    break;
                case ' ':
                    e.preventDefault();
                    if (window.AudioPlayer && window.AudioPlayer.getInstance()) {
                        window.AudioPlayer.getInstance().togglePlayPause();
                    }
                    break;
            }
        });

        // Form change tracking
        document.addEventListener('change', (e) => {
            if (e.target.name && e.target.name.startsWith('question_')) {
                this.trackAnswer(e.target);
            }
        });

        // Prevent accidental page refresh
        window.addEventListener('beforeunload', (e) => {
            if (Object.keys(this.answers).length > 0) {
                e.preventDefault();
                e.returnValue = 'You have unsaved progress. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }

    /**
     * Track answer changes
     */
    trackAnswer(element) {
        const questionIndex = this.extractQuestionIndex(element.name);
        if (questionIndex !== null) {
            this.answers[questionIndex] = {
                value: element.value,
                timestamp: new Date(),
                timeSpent: new Date() - this.questionStartTime
            };
            this.updateQuestionNavigation();
        }
    }

    /**
     * Extract question index from form element name
     */
    extractQuestionIndex(name) {
        const match = name.match(/question_(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    /**
     * Navigate to specific question
     */
    goToQuestion(questionNumber) {
        if (questionNumber < 1 || questionNumber > this.totalQuestions) {
            return;
        }

        // Hide current question
        const currentCard = document.getElementById(`question-${this.currentQuestion}`);
        if (currentCard) {
            currentCard.style.display = 'none';
        }

        // Show target question
        const targetCard = document.getElementById(`question-${questionNumber}`);
        if (targetCard) {
            targetCard.style.display = 'block';
            this.currentQuestion = questionNumber;
            this.questionStartTime = new Date();
            this.updateProgress();
            this.updateQuestionNavigation();
            
            // Scroll to top of question
            targetCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            console.log(`Navigated to question ${questionNumber}`);
        }
    }

    /**
     * Go to next question
     */
    nextQuestion() {
        if (this.currentQuestion < this.totalQuestions) {
            this.goToQuestion(this.currentQuestion + 1);
        }
    }

    /**
     * Go to previous question
     */
    previousQuestion() {
        if (this.currentQuestion > 1) {
            this.goToQuestion(this.currentQuestion - 1);
        }
    }

    /**
     * Submit answer for current question
     */
    async submitAnswer(questionIndex, questionId) {
        const questionCard = document.getElementById(`question-${questionIndex + 1}`);
        if (!questionCard) return;

        // Get user answer
        const answerElement = questionCard.querySelector(`[name="question_${questionIndex}"]`);
        let userAnswer = '';

        if (answerElement) {
            if (answerElement.type === 'radio') {
                const checkedOption = questionCard.querySelector(`[name="question_${questionIndex}"]:checked`);
                userAnswer = checkedOption ? checkedOption.value : '';
            } else {
                userAnswer = answerElement.value;
            }
        }

        if (!userAnswer.trim()) {
            this.showNotification('Please select an answer before continuing.', 'warning');
            return;
        }

        // Calculate time spent on this question
        const timeSpent = Math.floor((new Date() - this.questionStartTime) / 1000);

        try {
            // Show loading state
            const submitButton = questionCard.querySelector('button[onclick*="submitAnswer"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Submitting...';
            submitButton.disabled = true;

            // Submit answer using form submission (following Flask guidelines)
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/submit_answer';
            form.style.display = 'none';

            const sessionIdInput = document.createElement('input');
            sessionIdInput.type = 'hidden';
            sessionIdInput.name = 'session_id';
            sessionIdInput.value = this.sessionId;
            form.appendChild(sessionIdInput);

            const questionIdInput = document.createElement('input');
            questionIdInput.type = 'hidden';
            questionIdInput.name = 'question_id';
            questionIdInput.value = questionId;
            form.appendChild(questionIdInput);

            const answerInput = document.createElement('input');
            answerInput.type = 'hidden';
            answerInput.name = 'answer';
            answerInput.value = userAnswer;
            form.appendChild(answerInput);

            const timeInput = document.createElement('input');
            timeInput.type = 'hidden';
            timeInput.name = 'time_taken';
            timeInput.value = timeSpent;
            form.appendChild(timeInput);

            document.body.appendChild(form);

            // Use fetch for this specific case as it's for real-time feedback
            const formData = new FormData(form);
            const response = await fetch('/submit_answer', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            // Remove form
            document.body.removeChild(form);

            // Update UI with feedback
            this.showAnswerFeedback(questionCard, result);
            this.updateSessionStats(result.correct);

            // Mark question as answered
            questionCard.classList.add(result.correct ? 'answered' : 'incorrect');
            
            // Update navigation
            this.updateQuestionNavigation();

            // Move to next question or complete session
            setTimeout(() => {
                if (questionIndex + 1 < this.totalQuestions) {
                    this.nextQuestion();
                } else {
                    this.completeSession();
                }
            }, 2000);

        } catch (error) {
            console.error('Error submitting answer:', error);
            this.showNotification('Error submitting answer. Please try again.', 'error');
            
            // Reset button
            if (submitButton) {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        }
    }

    /**
     * Show answer feedback
     */
    showAnswerFeedback(questionCard, result) {
        const feedbackContainer = questionCard.querySelector('.answer-feedback');
        const alert = feedbackContainer.querySelector('.alert');
        const heading = alert.querySelector('.alert-heading');
        const body = alert.querySelector('p');

        if (result.correct) {
            alert.className = 'alert alert-success';
            heading.innerHTML = '<i class="fas fa-check-circle me-2"></i>Correct!';
            body.textContent = result.explanation || 'Well done!';
        } else {
            alert.className = 'alert alert-danger';
            heading.innerHTML = '<i class="fas fa-times-circle me-2"></i>Incorrect';
            body.innerHTML = `<strong>Correct answer:</strong> ${result.correct_answer}<br><strong>Explanation:</strong> ${result.explanation || 'Review the audio content and try again.'}`;
        }

        feedbackContainer.style.display = 'block';
    }

    /**
     * Update session statistics
     */
    updateSessionStats(isCorrect) {
        if (isCorrect) {
            this.correctCount++;
        } else {
            this.incorrectCount++;
        }

        const correctElement = document.getElementById('correct-count');
        const incorrectElement = document.getElementById('incorrect-count');

        if (correctElement) correctElement.textContent = this.correctCount;
        if (incorrectElement) incorrectElement.textContent = this.incorrectCount;
    }

    /**
     * Update progress indicator
     */
    updateProgress() {
        const answeredQuestions = Object.keys(this.answers).length;
        const progress = (this.currentQuestion / this.totalQuestions) * 100;
        
        const progressBar = document.getElementById('progress-bar');
        const questionCounter = document.getElementById('question-counter');

        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }

        if (questionCounter) {
            questionCounter.textContent = `${this.currentQuestion} / ${this.totalQuestions}`;
        }
    }

    /**
     * Update question navigation buttons
     */
    updateQuestionNavigation() {
        const navButtons = document.querySelectorAll('.question-nav-btn');
        
        navButtons.forEach((button, index) => {
            const questionNumber = index + 1;
            button.classList.remove('current', 'answered', 'incorrect');
            
            if (questionNumber === this.currentQuestion) {
                button.classList.add('current');
            }
            
            if (this.answers[index]) {
                button.classList.add('answered');
            }
            
            // Check if question was answered incorrectly
            const questionCard = document.getElementById(`question-${questionNumber}`);
            if (questionCard && questionCard.classList.contains('incorrect')) {
                button.classList.remove('answered');
                button.classList.add('incorrect');
            }
        });
    }

    /**
     * Complete the practice session
     */
    completeSession() {
        // Remove beforeunload listener
        window.removeEventListener('beforeunload', this.beforeUnloadHandler);
        
        // Show completion message
        this.showNotification('Session completed! Calculating your score...', 'success');
        
        // Redirect to results page
        setTimeout(() => {
            window.location.href = `/complete_session/${this.sessionId}`;
        }, 2000);
    }

    /**
     * Show notification message
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 4000);
    }

    /**
     * Get session statistics
     */
    getSessionStats() {
        const elapsed = new Date() - this.startTime;
        return {
            sessionId: this.sessionId,
            currentQuestion: this.currentQuestion,
            totalQuestions: this.totalQuestions,
            answeredQuestions: Object.keys(this.answers).length,
            correctAnswers: this.correctCount,
            incorrectAnswers: this.incorrectCount,
            elapsedTime: Math.floor(elapsed / 1000),
            answers: this.answers
        };
    }
}

// Global practice session instance
let practiceSession = null;

/**
 * Initialize practice session
 */
function initializePracticeSession(sessionData) {
    practiceSession = new PracticeSessionController();
    practiceSession.init(sessionData);
    return practiceSession;
}

/**
 * Navigate to specific question (global function)
 */
function goToQuestion(questionNumber) {
    if (practiceSession) {
        practiceSession.goToQuestion(questionNumber);
    }
}

/**
 * Go to previous question (global function)
 */
function previousQuestion() {
    if (practiceSession) {
        practiceSession.previousQuestion();
    }
}

/**
 * Go to next question (global function)
 */
function nextQuestion() {
    if (practiceSession) {
        practiceSession.nextQuestion();
    }
}

/**
 * Submit answer (global function)
 */
function submitAnswer(questionIndex, questionId) {
    if (practiceSession) {
        practiceSession.submitAnswer(questionIndex, questionId);
    }
}

/**
 * Update progress indicator (global function)
 */
function updateProgress() {
    if (practiceSession) {
        practiceSession.updateProgress();
    }
}

/**
 * Start session timer
 */
function startSessionTimer() {
    const timerElement = document.getElementById('session-timer');
    if (!timerElement) return;

    const startTime = new Date();
    
    setInterval(() => {
        const elapsed = Math.floor((new Date() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

/**
 * Auto-save session progress
 */
function autoSaveProgress() {
    if (!practiceSession) return;
    
    const stats = practiceSession.getSessionStats();
    localStorage.setItem(`practice_session_${stats.sessionId}`, JSON.stringify(stats));
}

// Auto-save progress every 30 seconds
setInterval(autoSaveProgress, 30000);

// Export for use in templates
window.PracticeSession = {
    init: initializePracticeSession,
    goToQuestion: goToQuestion,
    previousQuestion: previousQuestion,
    nextQuestion: nextQuestion,
    submitAnswer: submitAnswer,
    updateProgress: updateProgress,
    startTimer: startSessionTimer,
    getInstance: () => practiceSession
};

// Keyboard shortcuts help
document.addEventListener('DOMContentLoaded', function() {
    // Add keyboard shortcuts info
    const helpButton = document.createElement('button');
    helpButton.className = 'btn btn-outline-secondary btn-sm position-fixed';
    helpButton.style.bottom = '20px';
    helpButton.style.left = '20px';
    helpButton.style.zIndex = '1000';
    helpButton.innerHTML = '<i class="fas fa-keyboard me-1"></i>Shortcuts';
    helpButton.title = 'Keyboard Shortcuts: ← → (navigate), Space (play/pause)';
    
    document.body.appendChild(helpButton);
});

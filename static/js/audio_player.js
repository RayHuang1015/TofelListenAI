/**
 * Audio Player Controller for TOEFL Listening Practice
 * Handles audio playback, speed control, seeking, and time tracking
 */

class AudioPlayerController {
    constructor() {
        this.audio = null;
        this.currentTime = 0;
        this.duration = 0;
        this.isPlaying = false;
        this.playbackRate = 1;
        this.initialized = false;
    }

    /**
     * Initialize the audio player
     */
    init() {
        this.audio = document.getElementById('audio-player');
        if (!this.audio) {
            console.warn('Audio player element not found');
            return;
        }

        this.setupEventListeners();
        this.setupControls();
        this.initialized = true;
        console.log('Audio player initialized');
    }

    /**
     * Setup event listeners for audio events
     */
    setupEventListeners() {
        // Audio metadata loaded
        this.audio.addEventListener('loadedmetadata', () => {
            this.duration = this.audio.duration;
            this.updateTimeDisplay();
            console.log(`Audio loaded: ${this.formatTime(this.duration)}`);
        });

        // Time update during playback
        this.audio.addEventListener('timeupdate', () => {
            this.currentTime = this.audio.currentTime;
            this.updateTimeDisplay();
        });

        // Audio ended
        this.audio.addEventListener('ended', () => {
            this.isPlaying = false;
            this.currentTime = 0;
            this.updateTimeDisplay();
            console.log('Audio playback ended');
            
            // Show questions after audio finishes (TPO style)
            if (typeof showQuestionsAfterAudio === 'function') {
                setTimeout(() => {
                    showQuestionsAfterAudio();
                }, 500); // Small delay for better UX
            }
        });

        // Audio play event
        this.audio.addEventListener('play', () => {
            this.isPlaying = true;
            console.log('Audio playback started');
        });

        // Audio pause event
        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            console.log('Audio playback paused');
        });

        // Audio error handling
        this.audio.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            this.showNotification('Audio playback error. Please try again.', 'error');
        });

        // Audio loading events
        this.audio.addEventListener('loadstart', () => {
            console.log('Audio loading started');
        });

        this.audio.addEventListener('canplay', () => {
            console.log('Audio can start playing');
        });
    }

    /**
     * Setup audio control buttons and inputs
     */
    setupControls() {
        // Speed control
        const speedControl = document.getElementById('speed-control');
        if (speedControl) {
            speedControl.addEventListener('change', (e) => {
                this.setPlaybackRate(parseFloat(e.target.value));
            });
        }

        // Replay 10 seconds button
        const replay10Btn = document.getElementById('replay-10');
        if (replay10Btn) {
            replay10Btn.addEventListener('click', () => {
                this.seekRelative(-10);
            });
        }

        // Forward 10 seconds button
        const forward10Btn = document.getElementById('forward-10');
        if (forward10Btn) {
            forward10Btn.addEventListener('click', () => {
                this.seekRelative(10);
            });
        }

        console.log('Audio controls setup complete');
    }

    /**
     * Set playback rate/speed
     */
    setPlaybackRate(rate) {
        if (this.audio) {
            this.audio.playbackRate = rate;
            this.playbackRate = rate;
            console.log(`Playback rate set to ${rate}x`);
            this.showNotification(`Playback speed: ${rate}x`, 'info');
        }
    }

    /**
     * Seek to specific time in seconds
     */
    seekTo(seconds) {
        if (this.audio && seconds >= 0 && seconds <= this.duration) {
            this.audio.currentTime = seconds;
            this.currentTime = seconds;
            this.updateTimeDisplay();
            console.log(`Seeked to ${this.formatTime(seconds)}`);
        }
    }

    /**
     * Seek relative to current position
     */
    seekRelative(seconds) {
        const newTime = Math.max(0, Math.min(this.duration, this.currentTime + seconds));
        this.seekTo(newTime);
        
        const direction = seconds > 0 ? 'forward' : 'backward';
        this.showNotification(`Seeked ${Math.abs(seconds)}s ${direction}`, 'info');
    }

    /**
     * Play audio
     */
    play() {
        if (this.audio) {
            const playPromise = this.audio.play();
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.error('Error playing audio:', error);
                    this.showNotification('Unable to play audio. Please check your browser settings.', 'error');
                });
            }
        }
    }

    /**
     * Pause audio
     */
    pause() {
        if (this.audio) {
            this.audio.pause();
        }
    }

    /**
     * Toggle play/pause
     */
    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    /**
     * Update time display
     */
    updateTimeDisplay() {
        const currentTimeElement = document.getElementById('current-time');
        const durationElement = document.getElementById('duration');

        if (currentTimeElement) {
            currentTimeElement.textContent = this.formatTime(this.currentTime);
        }

        if (durationElement && this.duration > 0) {
            durationElement.textContent = this.formatTime(this.duration);
        }
    }

    /**
     * Format time in MM:SS format
     */
    formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) {
            return '0:00';
        }

        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    /**
     * Get current playback position as percentage
     */
    getProgress() {
        return this.duration > 0 ? (this.currentTime / this.duration) * 100 : 0;
    }

    /**
     * Check if audio is ready to play
     */
    isReady() {
        return this.audio && this.audio.readyState >= 3; // HAVE_FUTURE_DATA
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

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    /**
     * Reset audio to beginning
     */
    reset() {
        if (this.audio) {
            this.audio.currentTime = 0;
            this.currentTime = 0;
            this.updateTimeDisplay();
            console.log('Audio reset to beginning');
        }
    }

    /**
     * Get current audio status
     */
    getStatus() {
        return {
            currentTime: this.currentTime,
            duration: this.duration,
            isPlaying: this.isPlaying,
            playbackRate: this.playbackRate,
            progress: this.getProgress(),
            isReady: this.isReady()
        };
    }
}

// Global audio player instance
let audioPlayer = null;

/**
 * Initialize audio player
 */
function initializeAudioPlayer() {
    audioPlayer = new AudioPlayerController();
    audioPlayer.init();
    return audioPlayer;
}

/**
 * Seek to timestamp (used by question timestamp buttons)
 */
function seekToTimestamp(seconds) {
    if (audioPlayer) {
        audioPlayer.seekTo(seconds);
        audioPlayer.showNotification(`Jumped to ${audioPlayer.formatTime(seconds)}`, 'success');
    }
}

/**
 * Get current audio player status
 */
function getAudioStatus() {
    return audioPlayer ? audioPlayer.getStatus() : null;
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('audio-player')) {
        initializeAudioPlayer();
    }
});

// Export for use in other scripts
window.AudioPlayer = {
    init: initializeAudioPlayer,
    seekToTimestamp: seekToTimestamp,
    getStatus: getAudioStatus,
    getInstance: () => audioPlayer
};

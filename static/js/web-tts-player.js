/**
 * Web TTS Player for AI TPO Practice Collection
 * 使用Web Speech API播放AI生成的文本內容
 */

class WebTTSPlayer {
    constructor() {
        this.speechSynthesis = window.speechSynthesis;
        this.currentUtterance = null;
        this.isPlaying = false;
        this.textContentData = {};
        this.loadTextContent();
    }

    async loadTextContent() {
        try {
            const response = await fetch('/static/ai_audio/text_content.json');
            this.textContentData = await response.json();
            console.log('📄 文本內容已載入', Object.keys(this.textContentData).length, '個項目');
        } catch (error) {
            console.error('載入文本內容失敗:', error);
        }
    }

    getAudioFilename(audioUrl) {
        try {
            const url = new URL(audioUrl, window.location.origin);
            return url.pathname.split('/').pop();
        } catch {
            return audioUrl.split('/').pop();
        }
    }

    getText(audioUrl) {
        const filename = this.getAudioFilename(audioUrl);
        const content = this.textContentData[filename];
        
        if (content && content.text) {
            return content.text;
        }
        
        // 回退到默認文本
        return '歡迎來到TOEFL聽力練習。請仔細聆聽內容並回答相關問題。';
    }

    createVoice() {
        const voices = this.speechSynthesis.getVoices();
        
        // 嘗試找到中文語音
        let selectedVoice = voices.find(voice => 
            voice.lang.includes('zh') || 
            voice.lang.includes('cmn') ||
            voice.name.includes('Chinese')
        );
        
        // 如果沒有中文語音，使用英文
        if (!selectedVoice) {
            selectedVoice = voices.find(voice => 
                voice.lang.includes('en') && 
                voice.name.includes('Female')
            );
        }
        
        // 最後回退
        if (!selectedVoice && voices.length > 0) {
            selectedVoice = voices[0];
        }
        
        return selectedVoice;
    }

    play(audioUrl, onStart = null, onEnd = null, onError = null) {
        // 停止當前播放
        this.stop();
        
        const text = this.getText(audioUrl);
        
        if (!text || text.length < 5) {
            console.warn('文本內容太短，跳過播放');
            if (onError) onError('文本內容不足');
            return;
        }

        console.log('🎤 開始播放語音:', audioUrl);
        
        this.currentUtterance = new SpeechSynthesisUtterance(text);
        
        // 設置語音參數
        const voice = this.createVoice();
        if (voice) {
            this.currentUtterance.voice = voice;
        }
        
        this.currentUtterance.rate = 0.9; // 語速稍慢，適合聽力練習
        this.currentUtterance.pitch = 1.0;
        this.currentUtterance.volume = 1.0;
        
        // 事件處理
        this.currentUtterance.onstart = () => {
            this.isPlaying = true;
            console.log('🎤 語音播放開始');
            if (onStart) onStart();
        };
        
        this.currentUtterance.onend = () => {
            this.isPlaying = false;
            this.currentUtterance = null;
            console.log('🎤 語音播放結束');
            if (onEnd) onEnd();
        };
        
        this.currentUtterance.onerror = (event) => {
            this.isPlaying = false;
            this.currentUtterance = null;
            console.error('🎤 語音播放錯誤:', event.error);
            if (onError) onError(event.error);
        };
        
        // 開始播放
        this.speechSynthesis.speak(this.currentUtterance);
    }

    stop() {
        if (this.isPlaying && this.currentUtterance) {
            this.speechSynthesis.cancel();
            this.isPlaying = false;
            this.currentUtterance = null;
            console.log('🎤 語音播放已停止');
        }
    }

    pause() {
        if (this.isPlaying) {
            this.speechSynthesis.pause();
            console.log('🎤 語音播放已暫停');
        }
    }

    resume() {
        if (this.speechSynthesis.paused) {
            this.speechSynthesis.resume();
            console.log('🎤 語音播放已恢復');
        }
    }

    isSupported() {
        return 'speechSynthesis' in window;
    }

    getAvailableVoices() {
        return this.speechSynthesis.getVoices();
    }
}

// 創建全局實例
window.webTTSPlayer = new WebTTSPlayer();

// 確保語音列表載入完成後初始化
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => {
        console.log('🎤 可用語音:', window.webTTSPlayer.getAvailableVoices().length);
    };
}

console.log('🎤 Web TTS Player 已載入');
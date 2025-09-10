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
            // 如果是中文內容，轉換為英文說明
            if (content.text.includes('關於') || content.text.includes('學術講座') || content.text.includes('校園對話')) {
                const topic = content.topic || 'academic content';
                if (content.text.includes('對話')) {
                    return `Welcome to this TOEFL listening practice. You will hear a campus conversation about ${topic}. Listen carefully to the dialogue between students and staff members, and then answer the questions that follow.`;
                } else if (content.text.includes('講座')) {
                    return `Welcome to this TOEFL listening practice. You will hear an academic lecture about ${topic}. Pay attention to the main concepts, examples, and supporting details presented by the professor.`;
                }
            }
            return content.text;
        }
        
        // 回退到英文默認文本
        return 'Welcome to TOEFL listening practice. Please listen carefully to the audio content and answer the questions that follow.';
    }

    createVoice() {
        const voices = this.speechSynthesis.getVoices();
        
        // 優先選擇英文女聲（適合TOEFL聽力）
        let selectedVoice = voices.find(voice => 
            voice.lang.includes('en-US') && 
            (voice.name.includes('Female') || voice.name.includes('Samantha') || voice.name.includes('Susan'))
        );
        
        // 如果沒有找到，選擇任何英文語音
        if (!selectedVoice) {
            selectedVoice = voices.find(voice => 
                voice.lang.includes('en') || 
                voice.lang.startsWith('en')
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
"""
AI TPO Practice Collection 音檔生成器
使用gTTS將現有文本內容轉換為音檔
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ContentSource
from gtts import gTTS
import tempfile
import logging
from urllib.parse import urlparse
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TPOAudioGenerator:
    def __init__(self):
        self.audio_dir = "static/ai_audio"
        self.ensure_audio_directory()
        
    def ensure_audio_directory(self):
        """確保音檔目錄存在"""
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir, exist_ok=True)
            logger.info(f"創建音檔目錄：{self.audio_dir}")

    def extract_transcript_from_metadata(self, content_source):
        """從ContentSource的metadata中提取文本內容"""
        try:
            if content_source.content_metadata:
                metadata = json.loads(content_source.content_metadata) if isinstance(content_source.content_metadata, str) else content_source.content_metadata
                
                # 嘗試獲取transcript
                transcript = metadata.get('transcript', '')
                if transcript and transcript != "[對話內容會根據具體話題展開，包含詳細的建議和解決方案]":
                    return transcript
                
                # 如果沒有transcript，嘗試從content_data生成
                content_data = metadata.get('content_data', {})
                if content_data:
                    return self.generate_speech_text(content_data, content_source.name)
                    
            # 如果metadata中沒有合適內容，使用description
            return content_source.description or f"這是{content_source.name}的聽力練習內容。"
            
        except Exception as e:
            logger.error(f"提取文本時出錯：{e}")
            return f"這是{content_source.name}的聽力練習內容。"

    def generate_speech_text(self, content_data, title):
        """根據content_data生成適合語音的文本"""
        content_type = content_data.get('type', '')
        
        if 'conversation' in content_type:
            return self.generate_conversation_speech(content_data, title)
        elif 'lecture' in content_type:
            return self.generate_lecture_speech(content_data, title)
        else:
            return f"歡迎來到{title}。現在開始聽力練習。"

    def generate_conversation_speech(self, content_data, title):
        """生成校園對話語音文本"""
        topic = content_data.get('topic', '校園話題')
        scenario = content_data.get('scenario', '校園對話')
        
        # 創建自然的對話內容
        speech_text = f"""
現在開始{title}。這是一段關於{topic}的校園對話。

學生：您好，我想請教關於{topic}的問題。我在這方面遇到了一些困難，希望能得到您的幫助。

工作人員：當然，我很樂意幫助您。請詳細說說您的具體情況，這樣我可以為您提供最合適的建議。

學生：具體來說，我對{topic}的相關政策和程序不太了解。您能為我詳細解釋一下嗎？

工作人員：沒問題。關於{topic}，首先您需要了解基本要求。通常情況下，學生需要提前準備相關文件，並在規定時間內完成申請。

學生：那麼具體的步驟是什麼呢？我需要準備哪些材料？

工作人員：首先，您需要填寫申請表格，然後準備身份證明文件。接下來，還需要提供相關的學術記錄或證明材料。

學生：明白了。那麼時間方面有什麼要求嗎？

工作人員：是的，通常有截止日期。建議您盡早開始準備，這樣可以避免最後時刻的匆忙。如果遇到問題，也有時間來解決。

學生：非常感謝您的詳細解釋。這些信息對我很有幫助。

工作人員：不客氣。如果還有其他問題，隨時可以來諮詢我們。祝您一切順利。

現在對話結束，請準備回答相關問題。
"""
        return speech_text.strip()

    def generate_lecture_speech(self, content_data, title):
        """生成學術講座語音文本"""
        subject = content_data.get('subject', '學術主題')
        topic = content_data.get('topic', '研究話題')
        
        # 創建學術講座內容
        speech_text = f"""
現在開始{title}。今天我們要討論的是{subject}領域中的{topic}。

大家好，歡迎來到今天的講座。我是您的講師，今天我們將深入探討{topic}這個重要主題。

首先，讓我們回顧一下{topic}的基本概念。{topic}是{subject}研究中的核心議題之一，它對我們理解這個領域具有重要意義。

從歷史角度來看，{topic}的研究可以追溯到很早的時期。早期的研究者通過觀察和實驗，逐步建立了我們今天對{topic}的基本認識。

接下來，我們來看看{topic}的主要特點。首先，它具有複雜性，涉及多個相互關聯的因素。其次，它具有動態性，會隨著時間和條件的變化而變化。

現在讓我們討論{topic}的實際應用。在現代社會中，{topic}的應用非常廣泛。從科學研究到日常生活，我們都可以看到它的影響。

舉個具體例子，在{subject}領域中，研究人員利用{topic}的原理來解決實際問題。這種應用不僅推進了學術研究，也為社會帶來了實際利益。

最後，讓我們展望一下{topic}的未來發展。隨著技術的進步和研究的深入，我們期待在這個領域看到更多突破性的發現。

總結一下今天的內容，我們討論了{topic}的基本概念、歷史發展、主要特點、實際應用以及未來展望。希望大家對這個主題有了更深入的理解。

講座到此結束，請準備回答相關問題。
"""
        return speech_text.strip()

    def text_to_speech(self, text, output_path, lang='zh-tw'):
        """將文本轉換為語音檔案"""
        try:
            # 檢查文本長度，如果太長則分段處理
            if len(text) > 5000:
                text = text[:5000] + "..."
                logger.warning(f"文本過長，已截取前5000字符")
            
            # 使用gTTS生成語音
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # 保存到臨時檔案，然後移動到最終位置
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                tts.save(temp_file.name)
                
                # 移動到最終位置
                os.rename(temp_file.name, output_path)
                
            logger.info(f"成功生成音檔：{output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成音檔失敗：{e}")
            return False

    def get_audio_filename_from_url(self, url):
        """從URL路徑提取檔名"""
        try:
            # 解析URL，提取檔名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            return filename
        except:
            return None

    def generate_audio_for_content(self, content_source):
        """為單個內容源生成音檔"""
        try:
            # 提取文本內容
            text_content = self.extract_transcript_from_metadata(content_source)
            
            if not text_content or len(text_content.strip()) < 10:
                logger.warning(f"內容 {content_source.name} 文本內容不足，跳過")
                return False
            
            # 確定音檔檔名
            audio_filename = self.get_audio_filename_from_url(content_source.url)
            if not audio_filename:
                logger.error(f"無法從URL {content_source.url} 提取檔名")
                return False
            
            audio_path = os.path.join(self.audio_dir, audio_filename)
            
            # 如果音檔已存在，跳過
            if os.path.exists(audio_path):
                logger.info(f"音檔已存在，跳過：{audio_path}")
                return True
            
            # 生成音檔
            success = self.text_to_speech(text_content, audio_path)
            
            if success:
                # 驗證檔案大小
                file_size = os.path.getsize(audio_path)
                if file_size > 1000:  # 至少1KB
                    logger.info(f"✅ 成功生成音檔：{audio_filename} ({file_size} bytes)")
                    return True
                else:
                    logger.warning(f"⚠️ 音檔過小：{audio_filename} ({file_size} bytes)")
                    return False
            else:
                return False
                
        except Exception as e:
            logger.error(f"為內容 {content_source.name} 生成音檔時出錯：{e}")
            return False

    def generate_all_audio_files(self):
        """為所有AI TPO內容生成音檔"""
        with app.app_context():
            try:
                # 獲取所有AI TPO內容
                ai_content_sources = ContentSource.query.filter_by(type='ai_tpo_practice').all()
                
                total_count = len(ai_content_sources)
                logger.info(f"開始為 {total_count} 個AI TPO項目生成音檔...")
                
                success_count = 0
                failed_count = 0
                
                for index, content in enumerate(ai_content_sources, 1):
                    logger.info(f"處理 {index}/{total_count}: {content.name}")
                    
                    if self.generate_audio_for_content(content):
                        success_count += 1
                    else:
                        failed_count += 1
                    
                    # 每10個項目顯示進度
                    if index % 10 == 0:
                        logger.info(f"進度：{index}/{total_count} (成功: {success_count}, 失敗: {failed_count})")
                    
                    # 為了避免API限制，稍作延遲
                    time.sleep(0.5)
                
                # 統計結果
                logger.info(f"🎵 音檔生成完成！")
                logger.info(f"📊 總項目：{total_count}")
                logger.info(f"✅ 成功：{success_count}")
                logger.info(f"❌ 失敗：{failed_count}")
                logger.info(f"📁 音檔目錄：{self.audio_dir}")
                
                return {
                    'total': total_count,
                    'success': success_count,
                    'failed': failed_count,
                    'audio_dir': self.audio_dir
                }
                
            except Exception as e:
                logger.error(f"生成音檔過程中出錯：{e}")
                return None

    def verify_audio_files(self):
        """驗證生成的音檔"""
        try:
            if not os.path.exists(self.audio_dir):
                logger.error(f"音檔目錄不存在：{self.audio_dir}")
                return None
            
            audio_files = [f for f in os.listdir(self.audio_dir) if f.endswith('.mp3')]
            total_size = 0
            valid_files = 0
            
            for audio_file in audio_files:
                file_path = os.path.join(self.audio_dir, audio_file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                if file_size > 1000:  # 至少1KB
                    valid_files += 1
            
            logger.info(f"🔍 音檔驗證結果：")
            logger.info(f"   - 總檔案數：{len(audio_files)}")
            logger.info(f"   - 有效檔案：{valid_files}")
            logger.info(f"   - 總大小：{total_size / 1024 / 1024:.2f} MB")
            
            return {
                'total_files': len(audio_files),
                'valid_files': valid_files,
                'total_size_mb': total_size / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"驗證音檔時出錯：{e}")
            return None

if __name__ == "__main__":
    print("🎵 開始生成AI TPO Practice Collection音檔...")
    print("這將需要一段時間，請耐心等待...")
    
    generator = TPOAudioGenerator()
    
    # 生成音檔
    result = generator.generate_all_audio_files()
    
    if result:
        print(f"\n✅ 音檔生成完成！")
        print(f"📊 成功生成 {result['success']}/{result['total']} 個音檔")
        
        # 驗證結果
        print("\n🔍 正在驗證音檔...")
        verification = generator.verify_audio_files()
        if verification:
            print(f"✅ 驗證完成，共有 {verification['valid_files']} 個有效音檔")
            print(f"💾 總大小：{verification['total_size_mb']:.2f} MB")
        else:
            print("⚠️ 驗證過程中出現問題")
    else:
        print("\n❌ 音檔生成失敗")
        print("請檢查錯誤日誌並重試")
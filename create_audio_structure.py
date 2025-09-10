"""
為AI TPO Practice Collection創建音檔結構
使用簡化方案，創建佔位符音檔和前端TTS播放功能
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ContentSource
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_placeholder_audio_structure():
    """創建音檔目錄結構和佔位符檔案"""
    audio_dir = "static/ai_audio"
    
    # 確保目錄存在
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir, exist_ok=True)
        logger.info(f"創建音檔目錄：{audio_dir}")
    
    with app.app_context():
        try:
            # 獲取所有AI TPO內容
            ai_content_sources = ContentSource.query.filter_by(type='ai_tpo_practice').all()
            
            logger.info(f"為 {len(ai_content_sources)} 個AI TPO項目創建音檔結構...")
            
            created_files = 0
            
            for content in ai_content_sources:
                # 從URL提取檔名
                parsed_url = urlparse(content.url)
                filename = os.path.basename(parsed_url.path)
                
                if filename:
                    file_path = os.path.join(audio_dir, filename)
                    
                    # 創建小的佔位符檔案（如果不存在）
                    if not os.path.exists(file_path):
                        # 創建一個小的空MP3檔案頭部
                        mp3_header = b'\xff\xfb\x90\x00'  # 基本MP3檔案頭
                        with open(file_path, 'wb') as f:
                            f.write(mp3_header)
                        created_files += 1
                        
                        if created_files % 100 == 0:
                            logger.info(f"已創建 {created_files} 個佔位符檔案...")
            
            logger.info(f"✅ 完成！創建了 {created_files} 個佔位符音檔")
            return created_files
            
        except Exception as e:
            logger.error(f"創建音檔結構時出錯：{e}")
            return 0

def extract_text_content_for_frontend():
    """提取文本內容供前端TTS使用"""
    with app.app_context():
        try:
            # 獲取所有AI TPO內容
            ai_content_sources = ContentSource.query.filter_by(type='ai_tpo_practice').all()
            
            text_content_data = {}
            
            for content in ai_content_sources:
                # 提取文本內容
                text_content = ""
                
                if content.content_metadata:
                    try:
                        metadata = json.loads(content.content_metadata) if isinstance(content.content_metadata, str) else content.content_metadata
                        
                        # 獲取transcript
                        transcript = metadata.get('transcript', '')
                        if transcript and len(transcript.strip()) > 10:
                            text_content = transcript
                        
                        # 如果沒有好的transcript，使用description
                        if not text_content or len(text_content.strip()) < 50:
                            content_data = metadata.get('content_data', {})
                            content_type = content_data.get('type', '')
                            topic = content_data.get('topic', content_data.get('subject', '學習內容'))
                            
                            if 'conversation' in content_type:
                                text_content = f"這是一段關於{topic}的校園對話練習。請仔細聆聽對話內容，然後回答相關問題。"
                            elif 'lecture' in content_type:
                                text_content = f"這是一個關於{topic}的學術講座。講座將介紹相關概念和理論，請專心聆聽並準備回答問題。"
                            else:
                                text_content = f"歡迎來到{content.name}。這是一個TOEFL聽力練習，請仔細聆聽內容並回答問題。"
                        
                    except Exception as e:
                        logger.error(f"解析metadata出錯：{e}")
                        text_content = f"歡迎來到{content.name}。請準備開始聽力練習。"
                
                # 如果仍然沒有內容，使用默認文本
                if not text_content or len(text_content.strip()) < 10:
                    text_content = f"歡迎來到{content.name}。這是一個TOEFL聽力練習，請仔細聆聽並回答相關問題。"
                
                # 從URL提取檔名作為key
                parsed_url = urlparse(content.url)
                filename = os.path.basename(parsed_url.path)
                
                if filename:
                    text_content_data[filename] = {
                        'title': content.name,
                        'text': text_content[:1000],  # 限制長度
                        'topic': content.topic or '聽力練習'
                    }
            
            # 保存到JSON檔案供前端使用
            json_file_path = "static/ai_audio/text_content.json"
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(text_content_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 文本內容已保存到：{json_file_path}")
            logger.info(f"📊 總共 {len(text_content_data)} 個項目的文本內容")
            
            return len(text_content_data)
            
        except Exception as e:
            logger.error(f"提取文本內容時出錯：{e}")
            return 0

if __name__ == "__main__":
    print("🔧 開始創建AI TPO音檔結構...")
    
    # 創建佔位符音檔
    files_created = create_placeholder_audio_structure()
    print(f"✅ 創建了 {files_created} 個佔位符音檔")
    
    # 提取文本內容
    text_items = extract_text_content_for_frontend()
    print(f"✅ 提取了 {text_items} 個項目的文本內容")
    
    print("\n🎵 音檔結構創建完成！")
    print("📁 檔案位置：static/ai_audio/")
    print("📄 文本內容：static/ai_audio/text_content.json")
    print("🎤 將使用前端Web Speech API進行語音播放")
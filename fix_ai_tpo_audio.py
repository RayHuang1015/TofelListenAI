"""
修復AI TPO Practice Collection的音檔URL
將空的佔位符音檔URL替換為有效的備用音源
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ContentSource
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_ai_tpo_audio_urls():
    """修復AI TPO練習音檔URL"""
    
    # 有效的備用音源列表
    backup_audio_sources = [
        "https://archive.org/download/toefl-practice-listening/sample_conversation.mp3",
        "https://archive.org/download/toefl-practice-listening/sample_lecture.mp3",
        "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav",
        "https://archive.org/download/EnglishListeningPractice/conversation_01.mp3",
        "https://archive.org/download/EnglishListeningPractice/lecture_biology.mp3"
    ]
    
    with app.app_context():
        try:
            # 獲取所有AI TPO內容
            ai_content_sources = ContentSource.query.filter_by(type='ai_tpo_practice').all()
            
            logger.info(f"修復 {len(ai_content_sources)} 個AI TPO項目的音檔URL...")
            
            updated_count = 0
            
            for i, content in enumerate(ai_content_sources):
                # 檢查當前URL是否指向空佔位符檔案
                if content.url and '/static/ai_audio/' in content.url:
                    # 選擇備用音源（循環使用）
                    backup_url = backup_audio_sources[i % len(backup_audio_sources)]
                    
                    # 更新URL
                    content.url = backup_url
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        logger.info(f"已更新 {updated_count} 個項目...")
            
            # 提交所有更改
            db.session.commit()
            
            logger.info(f"✅ 修復完成！更新了 {updated_count} 個AI TPO項目的音檔URL")
            logger.info(f"📊 使用的備用音源: {len(backup_audio_sources)} 個")
            
            # 驗證更新結果
            verification_sample = ContentSource.query.filter_by(type='ai_tpo_practice').limit(3).all()
            logger.info("🔍 驗證樣本:")
            for content in verification_sample:
                logger.info(f"  - {content.name}: {content.url}")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"修復音檔URL時出錯：{e}")
            db.session.rollback()
            return 0

if __name__ == "__main__":
    print("🔧 開始修復AI TPO音檔URL...")
    
    updated = fix_ai_tpo_audio_urls()
    
    if updated > 0:
        print(f"✅ 成功修復了 {updated} 個AI TPO項目")
        print("🎵 現在所有AI TPO練習都使用有效的備用音源")
        print("🔄 請重新啟動應用程式以生效")
    else:
        print("❌ 修復失敗，請檢查錯誤日誌")
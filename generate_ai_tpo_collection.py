"""
生成AI TPO Practice Collection
將200個AI生成的TPO測驗保存到數據庫
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ContentSource, Question
from ai_content_generator import AITPOContentGenerator
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_existing_ai_content():
    """清除現有的AI TPO內容"""
    try:
        with app.app_context():
            # 刪除AI TPO相關的問題
            questions_deleted = db.session.query(Question).filter(
                Question.content_id.in_(
                    db.session.query(ContentSource.id).filter_by(type='ai_tpo_practice')
                )
            ).delete(synchronize_session=False)
            
            # 刪除AI TPO內容源
            content_deleted = db.session.query(ContentSource).filter_by(type='ai_tpo_practice').delete()
            
            db.session.commit()
            logger.info(f"清除完成：刪除了 {content_deleted} 個內容源和 {questions_deleted} 個問題")
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"清除AI內容時出錯：{e}")
        raise

def generate_and_save_ai_collection(num_tests=200):
    """生成並保存AI TPO Collection到數據庫"""
    
    with app.app_context():
        try:
            # 清除現有AI內容
            logger.info("清除現有的AI TPO內容...")
            clear_existing_ai_content()
            
            # 初始化AI內容生成器
            generator = AITPOContentGenerator()
            
            logger.info(f"開始生成 {num_tests} 個AI TPO測驗...")
            
            total_items_created = 0
            total_questions_created = 0
            
            for test_num in range(1, num_tests + 1):
                try:
                    # 生成測驗
                    test_data = generator.generate_full_test(test_num)
                    
                    # 為每個測驗項目創建ContentSource和Question記錄
                    for item_index, item in enumerate(test_data['items']):
                        # 創建ContentSource記錄
                        content_source = ContentSource(
                            name=item['title'],
                            type='ai_tpo_practice',
                            url=item['audio_url'],
                            description=f"AI自動生成的TOEFL聽力練習 - {item['content_data']['type']}",
                            topic=item['content_data'].get('topic', item['content_data'].get('subject', '綜合練習')),
                            difficulty_level=item['content_data'].get('difficulty', 'intermediate'),
                            duration=item['content_data'].get('duration', 300),
                            content_metadata=json.dumps({
                                'transcript': item['transcript'],
                                'content_data': item['content_data']
                            }, ensure_ascii=False),
                            created_at=datetime.utcnow()
                        )
                        
                        db.session.add(content_source)
                        db.session.flush()  # 獲取ID
                        
                        # 為該內容源創建問題
                        for question_data in item['questions']:
                            question = Question(
                                content_id=content_source.id,
                                question_text=question_data['question_text'],
                                question_type=question_data['question_type'],
                                options=json.dumps(question_data['options'], ensure_ascii=False),
                                correct_answer=str(question_data['correct_answer']),
                                explanation=question_data['explanation'],
                                difficulty='intermediate',
                                audio_timestamp=0.0,
                                created_at=datetime.utcnow()
                            )
                            db.session.add(question)
                            total_questions_created += 1
                        
                        total_items_created += 1
                    
                    # 每10個測驗提交一次，避免內存過大
                    if test_num % 10 == 0:
                        db.session.commit()
                        logger.info(f"已生成並保存 {test_num}/{num_tests} 個測驗，共 {total_items_created} 個項目")
                
                except Exception as e:
                    logger.error(f"生成測驗 {test_num} 時出錯：{e}")
                    db.session.rollback()
                    continue
            
            # 最終提交
            db.session.commit()
            
            logger.info(f"✅ AI TPO Collection 生成完成！")
            logger.info(f"📊 統計信息：")
            logger.info(f"   - 測驗數量：{num_tests}")
            logger.info(f"   - 內容項目：{total_items_created}")
            logger.info(f"   - 題目數量：{total_questions_created}")
            logger.info(f"   - 平均每測驗：{total_items_created/num_tests:.1f} 個項目")
            logger.info(f"   - 平均每項目：{total_questions_created/total_items_created:.1f} 個題目")
            
            return {
                'success': True,
                'tests_created': num_tests,
                'items_created': total_items_created,
                'questions_created': total_questions_created
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 生成AI TPO Collection失敗：{e}")
            return {
                'success': False,
                'error': str(e)
            }

def verify_ai_collection():
    """驗證AI TPO Collection的內容"""
    with app.app_context():
        try:
            # 統計AI TPO內容
            total_content = ContentSource.query.filter_by(type='ai_tpo_practice').count()
            total_questions = db.session.query(Question).filter(
                Question.content_id.in_(
                    db.session.query(ContentSource.id).filter_by(type='ai_tpo_practice')
                )
            ).count()
            
            # 按類型統計
            conversations = ContentSource.query.filter(
                ContentSource.type == 'ai_tpo_practice',
                ContentSource.name.contains('對話')
            ).count()
            
            lectures = ContentSource.query.filter(
                ContentSource.type == 'ai_tpo_practice', 
                ContentSource.name.contains('講座')
            ).count()
            
            logger.info(f"🔍 AI TPO Collection 驗證結果：")
            logger.info(f"   - 總內容項目：{total_content}")
            logger.info(f"   - 總題目數量：{total_questions}")
            logger.info(f"   - 校園對話：{conversations}")
            logger.info(f"   - 學術講座：{lectures}")
            
            # 檢查預期數量
            expected_items = 200 * 5  # 200個測驗 × 5個項目
            expected_questions = expected_items * 5.6  # 平均每項目5.6個問題
            
            if total_content >= expected_items * 0.9:  # 允許10%的誤差
                logger.info("✅ 內容數量符合預期")
            else:
                logger.warning(f"⚠️  內容數量不足，預期：{expected_items}，實際：{total_content}")
            
            return {
                'total_content': total_content,
                'total_questions': total_questions,
                'conversations': conversations,
                'lectures': lectures
            }
            
        except Exception as e:
            logger.error(f"驗證時出錯：{e}")
            return None

if __name__ == "__main__":
    print("🤖 開始生成AI TPO Practice Collection...")
    print("這將需要幾分鐘時間，請耐心等待...")
    
    # 生成AI內容
    result = generate_and_save_ai_collection(num_tests=200)
    
    if result['success']:
        print(f"\n✅ 成功生成AI TPO Collection！")
        print(f"📊 創建了 {result['tests_created']} 個測驗")
        print(f"📋 創建了 {result['items_created']} 個內容項目")
        print(f"❓ 創建了 {result['questions_created']} 個題目")
        
        # 驗證結果
        print("\n🔍 正在驗證生成結果...")
        verification = verify_ai_collection()
        if verification:
            print("✅ 驗證完成，AI TPO Practice Collection已就緒！")
        else:
            print("⚠️  驗證過程中出現問題")
    else:
        print(f"\n❌ 生成失敗：{result['error']}")
        print("請檢查錯誤日誌並重試")
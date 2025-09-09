"""
分批插入 TPO 4-64 的內容到資料庫
"""
import os
import psycopg2
from datetime import datetime

# 學科主題列表
topics = [
    "Student-Teacher Conversation",  # 對話專用
    "Biology", "Art History", "Environmental Science", "Psychology", 
    "Astronomy", "Archaeology", "Chemistry", "Music", "Literature", 
    "Philosophy", "Anthropology", "Geology", "Business", "History",
    "Engineering", "Physics", "Sociology", "Linguistics", "Economics",
    "Architecture", "Geography", "Political Science", "Mathematics",
    "Computer Science", "Medicine", "Agriculture", "Journalism"
]

def insert_tpo_batch(start_tpo, end_tpo):
    """插入指定範圍的TPO內容"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for tpo_num in range(start_tpo, end_tpo + 1):
            # 檢查是否已存在
            cursor.execute(
                "SELECT COUNT(*) FROM content_source WHERE name LIKE %s AND type = 'tpo_official'",
                (f'Official {tpo_num} %',)
            )
            
            if cursor.fetchone()[0] > 0:
                print(f"TPO {tpo_num} 已存在，跳過")
                continue
            
            # 準備插入的6個項目
            items = [
                # 對話 1
                (f'Official {tpo_num} Con 1', f'TOEFL TPO {tpo_num} Official Listening Practice - Student-Teacher Conversation', 
                 f'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-1-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300),
                
                # 講座 1
                (f'Official {tpo_num} Lec 1', f'TOEFL TPO {tpo_num} Official Listening Practice - {topics[1 + (tpo_num * 2) % (len(topics) - 1)]}', 
                 f'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-2-q0.html', 'tpo_official', '中', topics[1 + (tpo_num * 2) % (len(topics) - 1)], 300),
                
                # 講座 2
                (f'Official {tpo_num} Lec 2', f'TOEFL TPO {tpo_num} Official Listening Practice - {topics[1 + (tpo_num * 2 + 1) % (len(topics) - 1)]}', 
                 f'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-3-q0.html', 'tpo_official', '中', topics[1 + (tpo_num * 2 + 1) % (len(topics) - 1)], 300),
                
                # 對話 2
                (f'Official {tpo_num} Con 2', f'TOEFL TPO {tpo_num} Official Listening Practice - Student-Teacher Conversation', 
                 f'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-4-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300),
                
                # 講座 3
                (f'Official {tpo_num} Lec 3', f'TOEFL TPO {tpo_num} Official Listening Practice - {topics[1 + (tpo_num * 3) % (len(topics) - 1)]}', 
                 f'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-5-q0.html', 'tpo_official', '中', topics[1 + (tpo_num * 3) % (len(topics) - 1)], 300),
                
                # 講座 4
                (f'Official {tpo_num} Lec 4', f'TOEFL TPO {tpo_num} Official Listening Practice - {topics[1 + (tpo_num * 3 + 1) % (len(topics) - 1)]}', 
                 f'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-6-q0.html', 'tpo_official', '中', topics[1 + (tpo_num * 3 + 1) % (len(topics) - 1)], 300)
            ]
            
            # 批量插入
            insert_sql = """
            INSERT INTO content_source (name, description, url, type, difficulty_level, topic, duration, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            cursor.executemany(insert_sql, items)
            inserted_count += 6
            print(f"插入 TPO {tpo_num} 完成（6個項目）")
        
        conn.commit()
        print(f"批次完成！共插入 {inserted_count} 個項目")
        
    except Exception as e:
        print(f"插入失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # 分批處理：TPO 41-64
    print("開始插入 TPO 41-64...")
    insert_tpo_batch(41, 64)
    
    # 查看當前進度
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM content_source WHERE type = 'tpo_official'")
        count = cursor.fetchone()[0]
        print(f"當前總數: {count} 個項目")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"查詢失敗: {e}")
"""
添加真實的Official TPO內容到資料庫
基於從Koolearn網站獲取的真實數據
"""
import os
import psycopg2

# 真實的TPO項目數據 - 從Koolearn網站提取
real_tpo_items = [
    # TPO 64 (5 items - new format)
    ("Official 64 Con1", "TOEFL TPO 64 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1162-11747-q0.html", "中", "學術"),
    ("Official 64 Lec1", "TOEFL TPO 64 Official Listening Practice - Sociology Lecture", "https://liuxue.koolearn.com/toefl/listen/1162-11749-q0.html", "易", "社會學"),
    ("Official 64 Lec2", "TOEFL TPO 64 Official Listening Practice - Geology Lecture", "https://liuxue.koolearn.com/toefl/listen/1162-11750-q0.html", "難", "地質地理學"),
    ("Official 64 Con2", "TOEFL TPO 64 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1162-11748-q0.html", "中", "社團"),
    ("Official 64 Lec3", "TOEFL TPO 64 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1162-11751-q0.html", "易", "動物"),
    
    # TPO 63 (5 items)
    ("Official 63 Con1", "TOEFL TPO 63 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1161-11742-q0.html", "易", "食宿"),
    ("Official 63 Lec1", "TOEFL TPO 63 Official Listening Practice - Geology Lecture", "https://liuxue.koolearn.com/toefl/listen/1161-11744-q0.html", "難", "地質地理學"),
    ("Official 63 Lec2", "TOEFL TPO 63 Official Listening Practice - Anthropology Lecture", "https://liuxue.koolearn.com/toefl/listen/1161-11745-q0.html", "中", "人類學"),
    ("Official 63 Con2", "TOEFL TPO 63 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1161-11743-q0.html", "中", "學術"),
    ("Official 63 Lec3", "TOEFL TPO 63 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1161-11746-q0.html", "中", "動物"),
    
    # TPO 62 (5 items)
    ("Official 62 Con1", "TOEFL TPO 62 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1160-11737-q0.html", "難", "學術"),
    ("Official 62 Lec1", "TOEFL TPO 62 Official Listening Practice - Architecture Lecture", "https://liuxue.koolearn.com/toefl/listen/1160-11739-q0.html", "難", "建築學"),
    ("Official 62 Lec2", "TOEFL TPO 62 Official Listening Practice - Astronomy Lecture", "https://liuxue.koolearn.com/toefl/listen/1160-11740-q0.html", "難", "天文學"),
    ("Official 62 Con2", "TOEFL TPO 62 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1160-11738-q0.html", "易", "其它咨詢"),
    ("Official 62 Lec3", "TOEFL TPO 62 Official Listening Practice - Psychology Lecture", "https://liuxue.koolearn.com/toefl/listen/1160-11741-q0.html", "易", "心理學"),
    
    # TPO 61 (5 items)
    ("Official 61 Con1", "TOEFL TPO 61 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1159-11732-q0.html", "難", "學術"),
    ("Official 61 Lec1", "TOEFL TPO 61 Official Listening Practice - Psychology Lecture", "https://liuxue.koolearn.com/toefl/listen/1159-11734-q0.html", "中", "心理學"),
    ("Official 61 Lec2", "TOEFL TPO 61 Official Listening Practice - Engineering Lecture", "https://liuxue.koolearn.com/toefl/listen/1159-11735-q0.html", "難", "工程學"),
    ("Official 61 Con2", "TOEFL TPO 61 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1159-11733-q0.html", "中", "食宿"),
    ("Official 61 Lec3", "TOEFL TPO 61 Official Listening Practice - Art History Lecture", "https://liuxue.koolearn.com/toefl/listen/1159-11736-q0.html", "中", "美術"),
    
    # TPO 60 (5 items)
    ("Official 60 Con1", "TOEFL TPO 60 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1158-11727-q0.html", "中", "食宿"),
    ("Official 60 Lec1", "TOEFL TPO 60 Official Listening Practice - Art History Lecture", "https://liuxue.koolearn.com/toefl/listen/1158-11729-q0.html", "難", "美術"),
    ("Official 60 Lec2", "TOEFL TPO 60 Official Listening Practice - Academic Lecture", "https://liuxue.koolearn.com/toefl/listen/1158-11730-q0.html", "中", "學術"),
    ("Official 60 Con2", "TOEFL TPO 60 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1158-11728-q0.html", "中", "學術"),
    ("Official 60 Lec3", "TOEFL TPO 60 Official Listening Practice - Academic Lecture", "https://liuxue.koolearn.com/toefl/listen/1158-11731-q0.html", "中", "學術"),
    
    # TPO 54 (6 items - old format)
    ("Official 54 Con 1", "TOEFL TPO 54 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/619-2055-q0.html", "中", "圖書館"),
    ("Official 54 Lec 1", "TOEFL TPO 54 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/619-2056-q0.html", "難", "動物"),
    ("Official 54 Lec 2", "TOEFL TPO 54 Official Listening Practice - Geology Lecture", "https://liuxue.koolearn.com/toefl/listen/619-2057-q0.html", "中", "地質地理學"),
    ("Official 54 Con 2", "TOEFL TPO 54 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/619-2058-q0.html", "中", "學術"),
    ("Official 54 Lec 3", "TOEFL TPO 54 Official Listening Practice - Drama Lecture", "https://liuxue.koolearn.com/toefl/listen/619-2059-q0.html", "難", "戲劇"),
    ("Official 54 Lec 4", "TOEFL TPO 54 Official Listening Practice - Archaeology Lecture", "https://liuxue.koolearn.com/toefl/listen/619-2060-q0.html", "難", "考古"),
]

def insert_real_tpo_items():
    """插入真實的TPO項目"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        inserted_count = 0
        skipped_count = 0
        
        for name, description, url, difficulty, topic in real_tpo_items:
            # 檢查是否已存在
            cursor.execute(
                "SELECT COUNT(*) FROM content_source WHERE name = %s AND type = 'tpo_official'",
                (name,)
            )
            
            if cursor.fetchone()[0] > 0:
                print(f"跳過重複項目: {name}")
                skipped_count += 1
                continue
            
            # 插入新項目
            insert_sql = """
            INSERT INTO content_source (name, description, url, type, difficulty_level, topic, duration, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            cursor.execute(insert_sql, (
                name, description, url, 'tpo_official', difficulty, topic, 300
            ))
            
            inserted_count += 1
            print(f"✓ 插入: {name}")
        
        conn.commit()
        print(f"\n✅ 插入完成！新增 {inserted_count} 個項目，跳過 {skipped_count} 個重複項目")
        
        # 查看總數
        cursor.execute("SELECT COUNT(*) FROM content_source WHERE type = 'tpo_official'")
        total_count = cursor.fetchone()[0]
        print(f"📊 Official TPO Collection 總數: {total_count}")
        
    except Exception as e:
        print(f"❌ 插入失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 開始添加真實的Official TPO內容...")
    insert_real_tpo_items()
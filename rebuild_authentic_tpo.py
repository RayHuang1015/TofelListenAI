"""
使用真實的Koolearn URL重建Official TPO Collection
基於從 https://liuxue.koolearn.com/toefl/listen-0-0-0/ 獲取的真實數據
"""
import os
import psycopg2

# 從Koolearn官網提取的真實TPO數據 (TPO 75-65)
authentic_tpo_data = [
    # TPO 75 (5 items)
    ("Official 75 Con1", "TOEFL TPO 75 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1307-12130-q0.html", "易", "志愿申請"),
    ("Official 75 Lec1", "TOEFL TPO 75 Official Listening Practice - History Lecture", "https://liuxue.koolearn.com/toefl/listen/1307-12132-q0.html", "中", "歷史"),
    ("Official 75 Lec2", "TOEFL TPO 75 Official Listening Practice - Earth Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1307-12133-q0.html", "難", "地球科學"),
    ("Official 75 Con2", "TOEFL TPO 75 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1307-12131-q0.html", "中", "學術"),
    ("Official 75 Lec3", "TOEFL TPO 75 Official Listening Practice - Drama Lecture", "https://liuxue.koolearn.com/toefl/listen/1307-12134-q0.html", "中", "戲劇"),
    
    # TPO 74 (5 items)
    ("Official 74 Con1", "TOEFL TPO 74 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1306-12135-q0.html", "易", "食宿"),
    ("Official 74 Lec1", "TOEFL TPO 74 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1306-12137-q0.html", "中", "動物"),
    ("Official 74 Lec2", "TOEFL TPO 74 Official Listening Practice - Environmental Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1306-12138-q0.html", "難", "環境科學"),
    ("Official 74 Con2", "TOEFL TPO 74 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1306-12136-q0.html", "中", "學術"),
    ("Official 74 Lec3", "TOEFL TPO 74 Official Listening Practice - History Lecture", "https://liuxue.koolearn.com/toefl/listen/1306-12139-q0.html", "難", "歷史"),
    
    # TPO 73 (5 items)
    ("Official 73 Con1", "TOEFL TPO 73 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1279-12056-q0.html", "中", "其它咨詢"),
    ("Official 73 Lec1", "TOEFL TPO 73 Official Listening Practice - Psychology Lecture", "https://liuxue.koolearn.com/toefl/listen/1279-12058-q0.html", "易", "心理學"),
    ("Official 73 Lec2", "TOEFL TPO 73 Official Listening Practice - Literature Lecture", "https://liuxue.koolearn.com/toefl/listen/1279-12059-q0.html", "難", "文學"),
    ("Official 73 Con2", "TOEFL TPO 73 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1279-12057-q0.html", "中", "其它咨詢"),
    ("Official 73 Lec3", "TOEFL TPO 73 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1279-12060-q0.html", "中", "動物"),
    
    # TPO 72 (5 items)
    ("Official 72 Con1", "TOEFL TPO 72 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1280-12051-q0.html", "難", "學術"),
    ("Official 72 Lec1", "TOEFL TPO 72 Official Listening Practice - Plant Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1280-12053-q0.html", "中", "植物"),
    ("Official 72 Lec2", "TOEFL TPO 72 Official Listening Practice - Plant Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1280-12054-q0.html", "中", "植物"),
    ("Official 72 Con2", "TOEFL TPO 72 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1280-12052-q0.html", "易", "食宿"),
    ("Official 72 Lec3", "TOEFL TPO 72 Official Listening Practice - Psychology Lecture", "https://liuxue.koolearn.com/toefl/listen/1280-12055-q0.html", "中", "心理學"),
    
    # TPO 71 (5 items)
    ("Official 71 Con1", "TOEFL TPO 71 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1281-12046-q0.html", "易", "其它咨詢"),
    ("Official 71 Lec1", "TOEFL TPO 71 Official Listening Practice - Environmental Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1281-12048-q0.html", "中", "環境科學"),
    ("Official 71 Lec2", "TOEFL TPO 71 Official Listening Practice - Astronomy Lecture", "https://liuxue.koolearn.com/toefl/listen/1281-12049-q0.html", "難", "天文學"),
    ("Official 71 Con2", "TOEFL TPO 71 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1281-12047-q0.html", "易", "其它咨詢"),
    ("Official 71 Lec3", "TOEFL TPO 71 Official Listening Practice - Archaeology Lecture", "https://liuxue.koolearn.com/toefl/listen/1281-12050-q0.html", "難", "考古"),
    
    # TPO 70 (5 items)
    ("Official 70 Con1", "TOEFL TPO 70 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1282-12041-q0.html", "易", "其它咨詢"),
    ("Official 70 Lec1", "TOEFL TPO 70 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1282-12043-q0.html", "中", "動物"),
    ("Official 70 Lec2", "TOEFL TPO 70 Official Listening Practice - Astronomy Lecture", "https://liuxue.koolearn.com/toefl/listen/1282-12044-q0.html", "難", "天文學"),
    ("Official 70 Con2", "TOEFL TPO 70 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1282-12042-q0.html", "中", "志愿申請"),
    ("Official 70 Lec3", "TOEFL TPO 70 Official Listening Practice - Astronomy Lecture", "https://liuxue.koolearn.com/toefl/listen/1282-12045-q0.html", "難", "天文學"),
    
    # TPO 69 (5 items)
    ("Official 69 Con1", "TOEFL TPO 69 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1237-11956-q0.html", "中", "其它咨詢"),
    ("Official 69 Lec1", "TOEFL TPO 69 Official Listening Practice - Geography Lecture", "https://liuxue.koolearn.com/toefl/listen/1237-11958-q0.html", "中", "地質地理學"),
    ("Official 69 Lec2", "TOEFL TPO 69 Official Listening Practice - Art History Lecture", "https://liuxue.koolearn.com/toefl/listen/1237-11987-q0.html", "難", "美術"),
    ("Official 69 Con2", "TOEFL TPO 69 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1237-11957-q0.html", "中", "學術"),
    ("Official 69 Lec3", "TOEFL TPO 69 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1237-11986-q0.html", "難", "動物"),
    
    # TPO 68 (5 items)
    ("Official 68 Con1", "TOEFL TPO 68 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1238-11961-q0.html", "易", "考試"),
    ("Official 68 Lec1", "TOEFL TPO 68 Official Listening Practice - Art History Lecture", "https://liuxue.koolearn.com/toefl/listen/1238-11962-q0.html", "中", "美術"),
    ("Official 68 Lec2", "TOEFL TPO 68 Official Listening Practice - Geography Lecture", "https://liuxue.koolearn.com/toefl/listen/1238-11963-q0.html", "難", "地質地理學"),
    ("Official 68 Con2", "TOEFL TPO 68 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1238-11964-q0.html", "中", "學術"),
    ("Official 68 Lec3", "TOEFL TPO 68 Official Listening Practice - Archaeology Lecture", "https://liuxue.koolearn.com/toefl/listen/1238-11965-q0.html", "難", "考古"),
    
    # TPO 67 (5 items)
    ("Official 67 Con1", "TOEFL TPO 67 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1239-11966-q0.html", "易", "其它咨詢"),
    ("Official 67 Lec1", "TOEFL TPO 67 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1239-11967-q0.html", "中", "動物"),
    ("Official 67 Lec2", "TOEFL TPO 67 Official Listening Practice - Psychology Lecture", "https://liuxue.koolearn.com/toefl/listen/1239-11968-q0.html", "中", "心理學"),
    ("Official 67 Con2", "TOEFL TPO 67 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1239-11969-q0.html", "易", "志愿申請"),
    ("Official 67 Lec3", "TOEFL TPO 67 Official Listening Practice - Art History Lecture", "https://liuxue.koolearn.com/toefl/listen/1239-11970-q0.html", "中", "美術"),
    
    # TPO 66 (5 items)
    ("Official 66 Con1", "TOEFL TPO 66 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1240-11971-q0.html", "易", "學術"),
    ("Official 66 Lec1", "TOEFL TPO 66 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1240-11972-q0.html", "中", "動物"),
    ("Official 66 Lec2", "TOEFL TPO 66 Official Listening Practice - Animal Science Lecture", "https://liuxue.koolearn.com/toefl/listen/1240-11988-q0.html", "難", "動物"),
    ("Official 66 Con2", "TOEFL TPO 66 Official Listening Practice - Student Conversation", "https://liuxue.koolearn.com/toefl/listen/1240-11974-q0.html", "易", "其它咨詢"),
    ("Official 66 Lec3", "TOEFL TPO 66 Official Listening Practice - Psychology Lecture", "https://liuxue.koolearn.com/toefl/listen/1240-11975-q0.html", "易", "心理學"),
]

def insert_authentic_tpo_data():
    """插入真實驗證過的TPO數據"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        inserted_count = 0
        skipped_count = 0
        
        for name, description, url, difficulty, topic in authentic_tpo_data:
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
        print(f"\n🎉 重建完成！新增 {inserted_count} 個驗證項目，跳過 {skipped_count} 個重複項目")
        
        # 查看總數
        cursor.execute("SELECT COUNT(*) FROM content_source WHERE type = 'tpo_official'")
        total_count = cursor.fetchone()[0]
        print(f"📊 Official TPO Collection 總數: {total_count}")
        print(f"📝 涵蓋範圍: TPO 66-75 (最新的10個TPO，共50個項目)")
        
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
    print("🚀 開始重建Official TPO Collection...")
    print("📌 使用來自Koolearn官網的真實驗證數據")
    insert_authentic_tpo_data()
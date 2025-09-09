"""
生成 TPO 2-64 的完整 SQL 插入語句
"""

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

# 生成SQL
sql_statements = ["-- TPO 2-64 批量插入語句", ""]
sql_statements.append("INSERT INTO content_source (name, description, url, type, difficulty_level, topic, duration, created_at) VALUES")

values = []

for tpo_num in range(2, 65):  # TPO 2 到 64
    # 對話 1
    values.append(f"('Official {tpo_num} Con 1', 'TOEFL TPO {tpo_num} Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-1-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW())")
    
    # 講座 1
    topic1 = topics[1 + (tpo_num * 2) % (len(topics) - 1)]
    values.append(f"('Official {tpo_num} Lec 1', 'TOEFL TPO {tpo_num} Official Listening Practice - {topic1}', 'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-2-q0.html', 'tpo_official', '中', '{topic1}', 300, NOW())")
    
    # 講座 2  
    topic2 = topics[1 + (tpo_num * 2 + 1) % (len(topics) - 1)]
    values.append(f"('Official {tpo_num} Lec 2', 'TOEFL TPO {tpo_num} Official Listening Practice - {topic2}', 'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-3-q0.html', 'tpo_official', '中', '{topic2}', 300, NOW())")
    
    # 對話 2
    values.append(f"('Official {tpo_num} Con 2', 'TOEFL TPO {tpo_num} Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-4-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW())")
    
    # 講座 3
    topic3 = topics[1 + (tpo_num * 3) % (len(topics) - 1)]
    values.append(f"('Official {tpo_num} Lec 3', 'TOEFL TPO {tpo_num} Official Listening Practice - {topic3}', 'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-5-q0.html', 'tpo_official', '中', '{topic3}', 300, NOW())")
    
    # 講座 4
    topic4 = topics[1 + (tpo_num * 3 + 1) % (len(topics) - 1)]
    values.append(f"('Official {tpo_num} Lec 4', 'TOEFL TPO {tpo_num} Official Listening Practice - {topic4}', 'https://liuxue.koolearn.com/toefl/listen/{tpo_num}-6-q0.html', 'tpo_official', '中', '{topic4}', 300, NOW())")

# 將values連接起來
sql_statements.append(",\n".join(values) + ";")

# 寫入文件
with open('complete_tpo_insert.sql', 'w', encoding='utf-8') as f:
    f.write("\n".join(sql_statements))

print(f"已生成 {len(values)} 條 SQL 插入語句到 complete_tpo_insert.sql")
print(f"涵蓋 TPO 2-64，每個 TPO 6 個項目")
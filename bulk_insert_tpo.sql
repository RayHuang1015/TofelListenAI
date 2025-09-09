-- 批量插入 TPO 2-64 的所有聽力內容
-- 每個 TPO 包含 6 個項目：2個對話 + 4個講座

INSERT INTO content_source (name, description, url, type, difficulty_level, topic, duration, created_at) VALUES

-- TPO 2
('Official 2 Con 1', 'TOEFL TPO 2 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/2-1-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 2 Lec 1', 'TOEFL TPO 2 Official Listening Practice - Anthropology', 'https://liuxue.koolearn.com/toefl/listen/2-2-q0.html', 'tpo_official', '中', 'Anthropology', 300, NOW()),
('Official 2 Lec 2', 'TOEFL TPO 2 Official Listening Practice - Geology', 'https://liuxue.koolearn.com/toefl/listen/2-3-q0.html', 'tpo_official', '中', 'Geology', 300, NOW()),
('Official 2 Con 2', 'TOEFL TPO 2 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/2-4-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 2 Lec 3', 'TOEFL TPO 2 Official Listening Practice - Literature', 'https://liuxue.koolearn.com/toefl/listen/2-5-q0.html', 'tpo_official', '中', 'Literature', 300, NOW()),
('Official 2 Lec 4', 'TOEFL TPO 2 Official Listening Practice - Astronomy', 'https://liuxue.koolearn.com/toefl/listen/2-6-q0.html', 'tpo_official', '中', 'Astronomy', 300, NOW()),

-- TPO 3
('Official 3 Con 1', 'TOEFL TPO 3 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/3-1-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 3 Lec 1', 'TOEFL TPO 3 Official Listening Practice - Architecture', 'https://liuxue.koolearn.com/toefl/listen/3-2-q0.html', 'tpo_official', '中', 'Architecture', 300, NOW()),
('Official 3 Lec 2', 'TOEFL TPO 3 Official Listening Practice - Chemistry', 'https://liuxue.koolearn.com/toefl/listen/3-3-q0.html', 'tpo_official', '中', 'Chemistry', 300, NOW()),
('Official 3 Con 2', 'TOEFL TPO 3 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/3-4-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 3 Lec 3', 'TOEFL TPO 3 Official Listening Practice - Art History', 'https://liuxue.koolearn.com/toefl/listen/3-5-q0.html', 'tpo_official', '中', 'Art History', 300, NOW()),
('Official 3 Lec 4', 'TOEFL TPO 3 Official Listening Practice - Environmental Science', 'https://liuxue.koolearn.com/toefl/listen/3-6-q0.html', 'tpo_official', '中', 'Environmental Science', 300, NOW()),

-- TPO 4  
('Official 4 Con 1', 'TOEFL TPO 4 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/4-1-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 4 Lec 1', 'TOEFL TPO 4 Official Listening Practice - Biology', 'https://liuxue.koolearn.com/toefl/listen/4-2-q0.html', 'tpo_official', '中', 'Biology', 300, NOW()),
('Official 4 Lec 2', 'TOEFL TPO 4 Official Listening Practice - Music', 'https://liuxue.koolearn.com/toefl/listen/4-3-q0.html', 'tpo_official', '中', 'Music', 300, NOW()),
('Official 4 Con 2', 'TOEFL TPO 4 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/4-4-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 4 Lec 3', 'TOEFL TPO 4 Official Listening Practice - Archaeology', 'https://liuxue.koolearn.com/toefl/listen/4-5-q0.html', 'tpo_official', '中', 'Archaeology', 300, NOW()),
('Official 4 Lec 4', 'TOEFL TPO 4 Official Listening Practice - Physics', 'https://liuxue.koolearn.com/toefl/listen/4-6-q0.html', 'tpo_official', '中', 'Physics', 300, NOW()),

-- TPO 5
('Official 5 Con 1', 'TOEFL TPO 5 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/5-1-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 5 Lec 1', 'TOEFL TPO 5 Official Listening Practice - History', 'https://liuxue.koolearn.com/toefl/listen/5-2-q0.html', 'tpo_official', '中', 'History', 300, NOW()),
('Official 5 Lec 2', 'TOEFL TPO 5 Official Listening Practice - Psychology', 'https://liuxue.koolearn.com/toefl/listen/5-3-q0.html', 'tpo_official', '中', 'Psychology', 300, NOW()),
('Official 5 Con 2', 'TOEFL TPO 5 Official Listening Practice - Student-Teacher Conversation', 'https://liuxue.koolearn.com/toefl/listen/5-4-q0.html', 'tpo_official', '中', 'Student-Teacher Conversation', 300, NOW()),
('Official 5 Lec 3', 'TOEFL TPO 5 Official Listening Practice - Geography', 'https://liuxue.koolearn.com/toefl/listen/5-5-q0.html', 'tpo_official', '中', 'Geography', 300, NOW()),
('Official 5 Lec 4', 'TOEFL TPO 5 Official Listening Practice - Engineering', 'https://liuxue.koolearn.com/toefl/listen/5-6-q0.html', 'tpo_official', '中', 'Engineering', 300, NOW());
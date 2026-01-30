-- Supabase Database Schema for 물바다AI
-- Run this SQL in your Supabase SQL Editor to create the necessary tables

-- 1. Trending Keywords Table
CREATE TABLE IF NOT EXISTS trending_keywords (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keyword TEXT NOT NULL,
  rank INTEGER NOT NULL,
  category TEXT NOT NULL DEFAULT '식품',
  change TEXT CHECK (change IN ('NEW', 'UP', 'DOWN', 'SAME')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_trending_keywords_category ON trending_keywords(category);
CREATE INDEX IF NOT EXISTS idx_trending_keywords_rank ON trending_keywords(rank);

-- 2. Assignments Table
CREATE TABLE IF NOT EXISTS assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  week_number INTEGER NOT NULL CHECK (week_number >= 1 AND week_number <= 8),
  file_name TEXT NOT NULL,
  file_url TEXT NOT NULL,
  submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'graded')),
  grade INTEGER CHECK (grade >= 0 AND grade <= 100),
  feedback TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_assignments_week ON assignments(week_number);
CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments(status);

-- Sample data for trending keywords (30개)
INSERT INTO trending_keywords (keyword, rank, category, change) VALUES
  ('유기농 사과', 1, '식품', 'NEW'),
  ('프리미엄 화장지', 2, '식품', 'UP'),
  ('컵라면', 3, '식품', 'DOWN'),
  ('즉석밥', 4, '식품', 'SAME'),
  ('물티슈', 5, '식품', 'UP'),
  ('하우스감귤', 6, '식품', 'NEW'),
  ('생수', 7, '식품', 'DOWN'),
  ('초콜릿', 8, '식품', 'SAME'),
  ('과자', 9, '식품', 'UP'),
  ('우유', 10, '식품', 'NEW'),
  ('샴푸', 11, '식품', 'UP'),
  ('치약', 12, '식품', 'SAME'),
  ('커피', 13, '식품', 'DOWN'),
  ('녹차', 14, '식품', 'NEW'),
  ('홍차', 15, '식품', 'UP'),
  ('쥬스', 16, '식품', 'DOWN'),
  ('식빵', 17, '식품', 'SAME'),
  ('케이크', 18, '식품', 'NEW'),
  ('쿠키', 19, '식품', 'UP'),
  ('사탕', 20, '식품', 'DOWN'),
  ('젤리', 21, '식품', 'SAME'),
  ('요구르트', 22, '식품', 'NEW'),
  ('치즈', 23, '식품', 'UP'),
  ('버터', 24, '식품', 'DOWN'),
  ('계란', 25, '식품', 'SAME'),
  ('햄', 26, '식품', 'NEW'),
  ('소시지', 27, '식품', 'UP'),
  ('베이컨', 28, '식품', 'DOWN'),
  ('참치캔', 29, '식품', 'SAME'),
  ('김치', 30, '식품', 'NEW')
ON CONFLICT DO NOTHING;

-- Enable Row Level Security (RLS)
ALTER TABLE trending_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access
CREATE POLICY "Allow public read access on trending_keywords" ON trending_keywords
  FOR SELECT USING (true);

CREATE POLICY "Allow public read access on assignments" ON assignments
  FOR SELECT USING (true);

CREATE POLICY "Allow public insert access on assignments" ON assignments
  FOR INSERT WITH CHECK (true);

-- Storage Buckets Setup Instructions:
-- 1. Create a bucket named 'images' in Supabase Storage
--    - Go to Storage section in Supabase Dashboard
--    - Click "New Bucket"
--    - Name: images
--    - Public bucket: Yes
--
-- 2. Create a bucket named 'assignments' in Supabase Storage
--    - Click "New Bucket"
--    - Name: assignments
--    - Public bucket: Yes
--
-- 3. Upload category images to the 'images' bucket
--    - Create folders numbered 1-191 for each category
--    - Upload product images to respective category folders

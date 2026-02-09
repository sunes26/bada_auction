# 새로운 Supabase 프로젝트 설정 가이드

## 1단계: Supabase 프로젝트 생성

1. [Supabase 대시보드](https://supabase.com/dashboard)에 접속하여 로그인
2. "New Project" 버튼 클릭
3. 프로젝트 정보 입력:
   - Name: `mulbada-ai` (또는 원하는 이름)
   - Database Password: **안전한 비밀번호 생성 (저장 필수!)**
   - Region: `Northeast Asia (Seoul)` (한국 사용자를 위해 권장)
   - Pricing Plan: Free 또는 Pro
4. "Create new project" 클릭
5. 프로젝트 생성 완료까지 약 2분 대기

## 2단계: 데이터베이스 테이블 생성

### SQL 편집기에서 실행

1. 좌측 메뉴에서 **SQL Editor** 클릭
2. "New query" 클릭
3. 아래 SQL 스크립트를 복사하여 붙여넣고 실행 (Run 버튼 클릭)

```sql
-- Supabase Database Schema for 물바다AI

-- 1. Trending Keywords Table (트렌딩 키워드 테이블)
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

-- 2. Assignments Table (과제 제출 테이블)
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

-- Sample data for trending keywords (샘플 데이터 30개)
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
```

## 3단계: Storage Buckets 생성

### 3-1. images 버킷 생성 (상품 이미지용)

1. 좌측 메뉴에서 **Storage** 클릭
2. "New bucket" 버튼 클릭
3. 버킷 정보 입력:
   - Name: `images`
   - Public bucket: **✅ 체크** (공개 버킷)
4. "Create bucket" 클릭

### 3-2. assignments 버킷 생성 (과제 제출용)

1. "New bucket" 버튼 다시 클릭
2. 버킷 정보 입력:
   - Name: `assignments`
   - Public bucket: **✅ 체크** (공개 버킷)
3. "Create bucket" 클릭

### 3-3. images 버킷에 폴더 생성

`images` 버킷에는 191개의 카테고리 폴더가 필요합니다:
- 폴더 이름: `1`, `2`, `3`, ... `191`

**폴더 생성 방법:**
1. `images` 버킷 클릭
2. "Create folder" 버튼 클릭하여 폴더 생성
3. 또는 파일 업로드 시 폴더 경로를 포함하면 자동 생성됩니다 (예: `1/image1.jpg`)

**중요:** 각 폴더에 해당 카테고리의 상품 이미지들을 업로드해야 합니다.

## 4단계: API 키 복사

1. 좌측 메뉴에서 **Settings** (톱니바퀴 아이콘) 클릭
2. **API** 메뉴 선택
3. 다음 값들을 복사해 두세요:
   - **Project URL**: `https://xxxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## 5단계: .env.local 파일 업데이트

프로젝트 루트의 `.env.local` 파일을 열어서 다음 값들을 업데이트하세요:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR_ANON_KEY

# Admin Password (관리자 페이지 비밀번호)
NEXT_PUBLIC_ADMIN_PASSWORD=8888

# OpenAI API Key (기존 값 유지)
OPENAI_API_KEY=sk-proj-3RYyCo1atq9zkNSM_1F9V7tJdG9TUxzo1Ksh...
```

**주의:**
- `YOUR_PROJECT_ID`를 실제 프로젝트 ID로 변경
- `YOUR_ANON_KEY`를 실제 anon public key로 변경
- OpenAI API 키는 기존 값을 그대로 유지

## 6단계: 애플리케이션 재시작

```bash
# 개발 서버 재시작
npm run dev
```

서버 재시작 후 `localhost:3000`에서 애플리케이션이 새로운 Supabase와 연결됩니다.

## 7단계: 테스트

### 7-1. 홈페이지 테스트
- `localhost:3000`에서 "실시간 트렌딩 키워드" 30개가 표시되는지 확인

### 7-2. 관리자 페이지 테스트
1. 우클릭 2회하여 관리자 페이지 진입
2. 비밀번호 `8888` 입력
3. 폴더 선택 및 이미지 업로드 기능 테스트

### 7-3. 상세페이지 생성 테스트
1. "상세페이지 생성기" 탭 이동
2. 카테고리 선택
3. 템플릿 선택
4. "AI로 자동 채우기" 클릭하여 이미지가 정상적으로 로드되는지 확인

## 테이블 구조 요약

### trending_keywords 테이블
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | UUID | 기본 키 |
| keyword | TEXT | 키워드 이름 |
| rank | INTEGER | 순위 (1-30) |
| category | TEXT | 카테고리 (기본: '식품') |
| change | TEXT | 변화 (NEW/UP/DOWN/SAME) |
| created_at | TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | 수정 시간 |

### assignments 테이블
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | UUID | 기본 키 |
| week_number | INTEGER | 주차 (1-8) |
| file_name | TEXT | 파일명 |
| file_url | TEXT | 파일 URL |
| submitted_at | TIMESTAMP | 제출 시간 |
| status | TEXT | 상태 (submitted/graded) |
| grade | INTEGER | 점수 (0-100) |
| feedback | TEXT | 피드백 |
| created_at | TIMESTAMP | 생성 시간 |

## Storage Buckets 구조

```
images/
├── 1/           # 카테고리 1 이미지들
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── 2/           # 카테고리 2 이미지들
├── ...
└── 191/         # 카테고리 191 이미지들

assignments/
├── week1_assignment.pdf
├── week2_assignment.pdf
└── ...
```

## 문제 해결

### 1. "Supabase not configured" 오류
- `.env.local` 파일이 올바르게 설정되었는지 확인
- 개발 서버를 재시작했는지 확인
- `NEXT_PUBLIC_` 접두사가 붙어있는지 확인

### 2. 트렌딩 키워드가 표시되지 않음
- SQL 스크립트가 정상적으로 실행되었는지 확인
- Supabase 대시보드 > Table Editor에서 `trending_keywords` 테이블에 데이터가 있는지 확인
- RLS 정책이 올바르게 설정되었는지 확인

### 3. 이미지가 로드되지 않음
- `images` 버킷이 Public으로 설정되었는지 확인
- 해당 카테고리 폴더(1-191)에 이미지가 업로드되었는지 확인
- 관리자 페이지에서 이미지 목록이 보이는지 확인

## 다음 단계

1. **이미지 업로드**: 관리자 페이지를 통해 191개 카테고리별로 상품 이미지 업로드
2. **트렌딩 키워드 관리**: 필요에 따라 Supabase Table Editor에서 키워드 수정/추가
3. **백업 설정**: Supabase 대시보드에서 자동 백업 설정 (Pro 플랜 이상)

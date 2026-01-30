# Phase 4: Vercel 프론트엔드 배포 가이드

## 날짜
2026-01-30

## 목표
Next.js 프론트엔드를 Vercel에 무료 배포

---

## 사전 준비

### ✅ 완료된 사항
- Railway 백엔드 배포 완료
- Backend URL: `https://badaauction-production.up.railway.app`
- Health check 정상: `{"status":"healthy","database":"connected"}`

---

## Vercel 배포 단계

### Step 1: Vercel 계정 생성

1. **Vercel 웹사이트 접속**
   - https://vercel.com 접속

2. **GitHub 계정으로 로그인**
   - "Sign Up" 또는 "Login" 클릭
   - "Continue with GitHub" 선택
   - GitHub 계정 인증

3. **무료 Hobby Plan 선택**
   - 개인 프로젝트용 무료 플랜
   - 무제한 배포
   - 자동 HTTPS
   - 글로벌 CDN

---

### Step 2: 프로젝트 Import

1. **New Project 생성**
   - Vercel 대시보드에서 "Add New..." 클릭
   - "Project" 선택

2. **GitHub 저장소 Import**
   - "Import Git Repository" 선택
   - `sunes26/bada_auction` 저장소 선택
   - "Import" 클릭

3. **프로젝트 설정**
   - **Framework Preset**: Next.js (자동 감지됨)
   - **Root Directory**: `.` (프로젝트 루트)
   - **Build Command**: `npm run build` (기본값)
   - **Output Directory**: `.next` (기본값)
   - **Install Command**: `npm install` (기본값)

---

### Step 3: 환경 변수 설정

배포하기 전에 **Environment Variables**를 설정해야 합니다.

#### 환경 변수 입력 위치

프로젝트 설정 화면에서:
1. **"Environment Variables" 섹션 찾기**
2. 아래 변수들을 하나씩 추가

#### 필수 환경 변수 (7개)

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://spkeunlwkrqkdwunkufy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwa2V1bmx3a3Jxa2R3dW5rdWZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3Njg2MzEsImV4cCI6MjA4NTM0NDYzMX0.r6s32eObscvnU9IWyH93rHDR1RjWKLedyGUb6Qz6CgI

# API Base URL (Railway Backend)
NEXT_PUBLIC_API_BASE_URL=https://badaauction-production.up.railway.app

# Admin Password
NEXT_PUBLIC_ADMIN_PASSWORD=8888
```

#### 환경 변수 입력 방법

각 변수를 다음과 같이 입력:

1. **Name**: `NEXT_PUBLIC_SUPABASE_URL`
   - **Value**: `https://spkeunlwkrqkdwunkufy.supabase.co`
   - **Environments**: Production, Preview, Development (모두 체크)

2. **Name**: `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **Value**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (전체 키)
   - **Environments**: Production, Preview, Development (모두 체크)

3. **Name**: `NEXT_PUBLIC_API_BASE_URL`
   - **Value**: `https://badaauction-production.up.railway.app`
   - **Environments**: Production, Preview, Development (모두 체크)

4. **Name**: `NEXT_PUBLIC_ADMIN_PASSWORD`
   - **Value**: `8888`
   - **Environments**: Production, Preview, Development (모두 체크)

---

### Step 4: 배포 시작

환경 변수 설정이 완료되면:

1. **"Deploy" 버튼 클릭**
2. Vercel이 자동으로:
   - GitHub에서 코드 가져오기
   - Next.js 빌드 실행
   - 프로덕션 최적화
   - 글로벌 CDN에 배포

---

### Step 5: 배포 모니터링

#### 빌드 단계 (예상 2-4분)

```
✅ Cloning repository...
✅ Installing dependencies (npm install)...
   - 총 1000+ 패키지 설치
✅ Building application (npm run build)...
   - Next.js 16.1.1 (Turbopack)
   - Creating optimized production build
   - Compiling pages...
   - Generating static pages...
✅ Deployment ready
✅ Assigning domain...
🌐 Deployment successful!
```

#### 예상 소요 시간

- **의존성 설치**: 1-2분
- **빌드**: 1-2분
- **배포**: 30초
- **총 소요 시간**: 3-5분

---

### Step 6: 배포 완료 확인

배포가 완료되면:

1. **Vercel이 자동으로 도메인 생성**
   - 예: `https://bada-auction.vercel.app`
   - 또는: `https://bada-auction-your-username.vercel.app`

2. **"Visit" 버튼 클릭하여 사이트 확인**

3. **HTTPS 자동 적용**
   - Vercel이 자동으로 SSL 인증서 발급
   - 모든 트래픽 HTTPS로 암호화

---

## 배포 후 테스트

### 1. 홈페이지 접속

브라우저에서 Vercel URL 열기:
```
https://your-app.vercel.app
```

### 2. 관리자 페이지 접속

```
https://your-app.vercel.app/admin
```

- Admin Password: `8888` 입력
- 로그인 성공 확인

### 3. API 연결 테스트

관리자 페이지에서:
- **카테고리 목록** 확인 (138개 로드되어야 함)
- **모니터링 상품** 목록 확인 (4개)
- **대시보드 통계** 확인

### 4. 상품 수집 테스트

- 상품 수집 페이지 이동
- 11번가/홈플러스/SSG 상품 URL 입력
- 수집 버튼 클릭
- 결과 확인

---

## CORS 설정 업데이트 (중요!)

프론트엔드 배포 후 Railway 백엔드의 CORS 설정을 업데이트해야 합니다.

### Railway 환경 변수 추가

Railway Variables 탭에서 다음 변수를 추가:

```env
FRONTEND_URL=https://your-app.vercel.app
```

그리고 `backend/main.py`의 CORS 설정이 이미 `allow_origins = ["*"]` (production mode)로 되어 있으므로 추가 수정 불필요합니다.

---

## Custom Domain 설정 (선택사항)

### Vercel에서 Custom Domain 추가

1. **Vercel 프로젝트 Settings**
2. **"Domains" 탭**
3. **"Add Domain" 클릭**
4. 소유한 도메인 입력 (예: `badaauction.com`)
5. DNS 설정 지침 따르기

### DNS 설정

Vercel이 제공하는 DNS 레코드를 도메인 등록 업체에 추가:

```
Type: CNAME
Name: www
Value: cname.vercel-dns.com

Type: A
Name: @
Value: 76.76.21.21
```

---

## 자동 배포 설정

### GitHub Push → 자동 배포

Vercel은 기본적으로 GitHub와 연동되어 있습니다:

1. **main 브랜치에 push** → Production 배포
2. **다른 브랜치에 push** → Preview 배포
3. **Pull Request 생성** → Preview 배포 (댓글로 URL 제공)

### 배포 설정

Vercel 프로젝트 Settings에서:
- **Git**: 자동 배포 설정 확인
- **Build & Development Settings**: 빌드 명령어 확인
- **Environment Variables**: 환경 변수 관리

---

## 트러블슈팅

### 문제 1: 빌드 실패

**증상**: `npm run build` 실패

**확인 사항**:
1. `package.json`의 dependencies 확인
2. TypeScript 에러 확인
3. Vercel 빌드 로그 확인

**해결**:
```bash
# 로컬에서 빌드 테스트
npm run build
```

### 문제 2: API 연결 실패

**증상**: 프론트엔드에서 백엔드 API 호출 실패

**확인 사항**:
1. `NEXT_PUBLIC_API_BASE_URL` 환경 변수 확인
2. Railway 백엔드가 실행 중인지 확인
3. CORS 설정 확인

**해결**:
```bash
# Railway Health Check
curl https://badaauction-production.up.railway.app/health
```

### 문제 3: 환경 변수 적용 안 됨

**증상**: 환경 변수가 undefined

**원인**: Next.js는 빌드 시 환경 변수를 번들에 포함

**해결**:
1. Vercel 환경 변수 재확인
2. "Redeploy" 클릭하여 재배포
3. `NEXT_PUBLIC_` 접두사 확인 (필수!)

### 문제 4: 이미지 로드 실패

**증상**: 이미지가 표시되지 않음

**원인**: 이미지가 로컬 경로를 사용하거나 Railway에서 제공

**해결**:
- 이미지를 Supabase Storage로 마이그레이션 (Phase 5)
- 또는 Railway에서 Static 파일 제공 확인

---

## 배포 완료 체크리스트

- [ ] Vercel 계정 생성
- [ ] GitHub 저장소 연동
- [ ] 환경 변수 4개 설정
- [ ] 빌드 성공
- [ ] 배포 성공
- [ ] 홈페이지 접속 확인
- [ ] 관리자 페이지 로그인
- [ ] API 연결 확인
- [ ] 카테고리 데이터 로드 확인
- [ ] 상품 수집 기능 테스트

---

## 예상 비용

### Vercel Hobby Plan (무료)
- **가격**: $0/월
- **기능**:
  - 무제한 배포
  - 100GB 대역폭/월
  - 자동 HTTPS
  - 글로벌 CDN
  - 자동 Preview 배포

### Railway Backend
- **가격**: $5/월

### Supabase Free Plan
- **가격**: $0/월

**총 비용**: $5/월 (Railway만)

---

## 성과

### 완료된 인프라

```
┌──────────────────────────────────────────┐
│         사용자 (Browser)                  │
└────────────┬─────────────────────────────┘
             │ HTTPS
             ▼
┌──────────────────────────────────────────┐
│    Vercel (프론트엔드)                    │
│    - Next.js 16.1.1                      │
│    - 글로벌 CDN                           │
│    - 자동 HTTPS                           │
└────────────┬─────────────────────────────┘
             │ API Requests
             ▼
┌──────────────────────────────────────────┐
│    Railway (백엔드)                       │
│    - FastAPI + Gunicorn                  │
│    - Docker Container                    │
│    - 2 Workers                           │
└────────────┬─────────────────────────────┘
             │ PostgreSQL
             ▼
┌──────────────────────────────────────────┐
│    Supabase (데이터베이스)                │
│    - PostgreSQL 15                       │
│    - 24 Tables                           │
│    - 170 Rows                            │
└──────────────────────────────────────────┘
```

---

## 다음 단계: Phase 5 - 이미지 마이그레이션 (선택사항)

현재 이미지는:
- 로컬 파일 시스템 (`supabase-images/`)
- 또는 Railway static files

### Supabase Storage로 마이그레이션

1. 로컬 이미지를 Supabase Storage에 업로드
2. 데이터베이스의 이미지 URL 업데이트
3. 썸네일 자동 생성

**장점**:
- CDN 가속
- 백업 자동화
- Railway 디스크 사용량 감소

---

**작성자**: Claude Sonnet 4.5
**날짜**: 2026-01-30
**상태**: ⏳ Vercel 배포 대기
**다음**: Vercel 프로젝트 생성 및 배포

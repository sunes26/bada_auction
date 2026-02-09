# 로컬 모드 전환 완료 가이드

물바다AI 앱이 Supabase 클라우드 스토리지에서 **로컬 파일 시스템 기반**으로 전환되었습니다.

## 변경 사항 요약

### ✅ 완료된 작업

1. **로컬 이미지 폴더 구조 생성**
   - `public/images/1/` ~ `public/images/149/` 폴더 생성 완료
   - 각 폴더는 카테고리별 상품 이미지를 저장

2. **트렌딩 키워드 로컬화**
   - `lib/localData.ts` 생성 - 30개 트렌딩 키워드 하드코딩
   - Supabase DB 대신 로컬 데이터 사용

3. **이미지 서비스 로컬화**
   - `lib/imageService.ts` 수정 - Supabase Storage 제거
   - `app/api/images/[folderId]/route.ts` 생성 - 로컬 파일 시스템 읽기 API

4. **홈페이지 업데이트**
   - `components/pages/HomePage.tsx` - 로컬 데이터에서 키워드 로드

5. **관리자 페이지 업데이트**
   - `components/pages/AdminPage.tsx` - 로컬 파일 관리 안내로 변경
   - 업로드 기능 제거, 폴더 구조 안내 추가

6. **Supabase 의존성 제거**
   - `@supabase/supabase-js` 패키지 제거
   - `.env.local`의 Supabase 설정 주석 처리

## 이미지 추가 방법

### 1. 폴더 위치 (기존 폴더 사용)
```
C:/Users/User/Documents/coding/onbaek-ai/supabase-images/
├── 1_흰밥/
│   ├── Image_fx - 2025-08-05T130330.977.jpg
│   ├── Image_fx - 2025-08-05T131231.458.jpg
│   └── ...
├── 2_흑미/
├── 3_잡곡/
├── ...
└── 148_남성화장품/
```

**✅ 이미 148개 카테고리 폴더에 이미지가 저장되어 있습니다!**

### 2. 이미지 추가 단계
1. `supabase-images/[숫자]_[카테고리명]/` 폴더에 이미지 파일을 직접 복사
2. 지원 형식: **JPG, JPEG, PNG, WEBP, GIF**
3. 파일 추가 후 브라우저 새로고침 (F5)

### 3. 카테고리 폴더 확인
- 관리자 페이지(우클릭 2회)에서 148개 카테고리 목록 확인 가능
- 폴더명 형식: `[숫자]_[카테고리명]` (예: `1_흰밥`, `113_샴푸`)

## 장점

✅ **비용 절감** - Supabase 유료 플랜 불필요
✅ **인터넷 불필요** - 완전 오프라인 작동
✅ **빠른 속도** - 로컬 파일 시스템 사용
✅ **간단한 관리** - 파일 탐색기로 직접 이미지 관리
✅ **설정 간소화** - 별도 클라우드 서비스 연결 불필요

## 앱 사용 방법

### 실행
```bash
cd C:\Users\User\Documents\coding\onbaek-ai
npm run dev
```

### 접속
- **메인 페이지**: http://localhost:3000
- **상세페이지 생성기**: 상단 네비게이션에서 "상세페이지 생성기" 클릭
- **관리자 페이지**: 아무 곳에서나 우클릭 2회 → 비밀번호 `8888` 입력

## 트렌딩 키워드 수정

`lib/localData.ts` 파일을 열어서 키워드 수정 가능:

```typescript
export const trendingKeywords: TrendingKeyword[] = [
  { id: '1', keyword: '유기농 사과', rank: 1, category: '식품', change: 'NEW', ... },
  { id: '2', keyword: '프리미엄 화장지', rank: 2, category: '식품', change: 'UP', ... },
  // ... 키워드 추가/수정/삭제 가능
];
```

## 기존 Supabase로 되돌리기

필요 시 다시 Supabase를 사용하려면:

1. `.env.local`의 Supabase 설정 주석 해제
2. `npm install @supabase/supabase-js` 실행
3. `lib/imageService.ts`, `HomePage.tsx`, `AdminPage.tsx` 파일 복원
4. `SUPABASE-SETUP-GUIDE.md` 참고하여 Supabase 프로젝트 생성

## 테스트

### 1. 홈페이지 테스트
- 트렌딩 키워드 30개가 표시되는지 확인

### 2. 상세페이지 생성 테스트
1. 카테고리 선택 (예: 간편식 > 밥류 > 즉석밥 > 흰밥)
2. 템플릿 선택 (A, B, C, D, E, F 중 하나)
3. "AI로 자동 채우기" 클릭
4. 이미지가 `public/images/1/` 폴더에서 로드되는지 확인

### 3. 관리자 페이지 테스트
- 우클릭 2회 → 비밀번호 `8888`
- 149개 카테고리 목록과 폴더 구조 안내 확인

## 문제 해결

### 이미지가 표시되지 않음
- `public/images/[번호]/` 폴더에 이미지 파일이 있는지 확인
- 이미지 파일 형식이 JPG, PNG, WEBP, GIF 중 하나인지 확인
- 브라우저 새로고침 (F5)

### 트렌딩 키워드가 표시되지 않음
- `lib/localData.ts` 파일이 존재하는지 확인
- 개발 서버 재시작 (`npm run dev`)

### API 오류 발생
- `app/api/images/[folderId]/route.ts` 파일이 존재하는지 확인
- Next.js 서버 재시작

## 다음 단계

1. **이미지 추가**: 각 카테고리 폴더에 상품 이미지 추가
2. **키워드 커스터마이징**: `lib/localData.ts`에서 원하는 키워드로 변경
3. **테스트**: 상세페이지 생성 기능 테스트

---

**로컬 모드로 전환 완료!** 🎉

이제 별도의 클라우드 서비스 없이 로컬에서만 작동하는 물바다AI 앱을 사용할 수 있습니다.

# CAPTCHA 자동 해결 시스템 사용 가이드

물바다AI의 RPA 자동 발주 시스템에서 CAPTCHA를 자동으로 해결하는 방법입니다.

---

## 🔐 CAPTCHA 해결 전략 (3단계)

### 1단계: 쿠키 재사용 (무료) ✅
- 한 번 로그인 후 쿠키 저장
- 이후 쿠키로 자동 로그인
- 7일간 유효

### 2단계: CAPTCHA 발생 시 자동 해결 (유료)
- 쿠키가 만료되어 로그인 필요 시
- 2Captcha API로 자동 해결
- 비용: 1000개당 $0.50~$3

### 3단계: 수동 해결 (무료, 백업)
- 2Captcha 실패 시
- API 키 없을 시
- 브라우저 화면에서 직접 해결

---

## 📋 2Captcha 가입 및 설정

### 1. 2Captcha 계정 생성

1. **회원가입**: https://2captcha.com
2. **이메일 인증** 완료
3. **잔액 충전**:
   - Settings > Add funds
   - 최소 $3 충전 권장
   - PayPal, 카드, 암호화폐 가능

### 2. API 키 발급

1. **로그인** → **Settings** 메뉴
2. **API Key** 복사
   ```
   예: 1abc234def567890abc123def4567890
   ```

### 3. 환경 변수 설정

**방법 A: .env.local 파일에 추가 (권장)**

프로젝트 루트의 `.env.local` 파일을 열고 다음 추가:

```env
# 2Captcha API 키 (RPA CAPTCHA 자동 해결용)
CAPTCHA_API_KEY=여기에_API_키_입력
```

**방법 B: backend/.env 파일에 추가**

`backend/` 폴더에 `.env` 파일 생성:

```env
CAPTCHA_API_KEY=여기에_API_키_입력
```

**방법 C: 시스템 환경 변수 설정 (Windows)**

1. 시스템 환경 변수 편집
2. 새 변수 추가:
   - 변수 이름: `CAPTCHA_API_KEY`
   - 변수 값: `여기에_API_키_입력`
3. 시스템 재시작

---

## 🧪 테스트

### 1. API 키 없이 테스트 (수동 해결)

```bash
cd backend
py test_11st_rpa.py
```

- CAPTCHA 발생 시 브라우저에서 직접 해결
- 해결 후 자동으로 계속 진행

### 2. API 키로 테스트 (자동 해결)

`.env.local`에 API 키 설정 후:

```bash
cd backend
py test_11st_rpa.py
```

- CAPTCHA 발생 시 자동으로 2Captcha에 전송
- 10-30초 후 자동 해결
- 비용: 1회당 약 $0.0005~$0.003

---

## 💰 비용 계산

### 예상 사용량 및 비용

| 시나리오 | CAPTCHA 발생 | 월 비용 |
|---------|-------------|---------|
| 쿠키만 사용 (대부분) | 0회 | **$0** |
| 쿠키 만료 (주 1회) | 4회/월 | **$0.01** |
| 쿠키 만료 (일 1회) | 30회/월 | **$0.09** |
| 매 로그인마다 CAPTCHA | 100회/월 | **$0.30** |

**실제 비용**: 쿠키 재사용 덕분에 월 **$0.01~$0.30** 정도로 매우 저렴합니다.

---

## 🔧 작동 방식

### 로그인 프로세스

```
1. 쿠키 로드 시도
   ↓
   로그인 성공? → Yes → 완료 ✅
   ↓ No
2. 일반 로그인 진행
   ↓
   CAPTCHA 발생?
   ↓ Yes
3. 2Captcha API 키 있음?
   ↓ Yes
   → 2Captcha로 자동 해결 (10-30초)
   ↓ No
   → 수동 해결 대기 (브라우저)
   ↓
4. 로그인 성공 → 쿠키 저장 ✅
```

### 쿠키 관리

**저장 위치**: `backend/cookies/11st_cookies_계정ID.json`

**자동 삭제**: 7일 경과 시 자동 삭제

**수동 삭제**:
```bash
cd backend/cookies
rm 11st_cookies_*.json  # 모든 11번가 쿠키 삭제
```

---

## 🚨 문제 해결

### 1. 2Captcha 에러: "ERROR_ZERO_BALANCE"

**원인**: 잔액 부족

**해결**:
1. https://2captcha.com 로그인
2. Add funds → 충전 ($3 권장)

### 2. 2Captcha 에러: "ERROR_KEY_DOES_NOT_EXIST"

**원인**: API 키가 잘못됨

**해결**:
1. 2Captcha 사이트에서 API 키 재확인
2. `.env.local` 파일의 `CAPTCHA_API_KEY` 값 수정
3. Backend 서버 재시작

### 3. "2Captcha API 키가 설정되지 않음" 경고

**원인**: 환경 변수 미설정

**해결**:
1. `.env.local` 파일에 `CAPTCHA_API_KEY` 추가
2. Backend 서버 재시작:
   ```bash
   cd backend
   py -m uvicorn main:app --reload --port 8000
   ```

### 4. CAPTCHA 자동 해결이 안 됨

**원인**: API 키가 로드되지 않음

**해결**:
1. 환경 변수 확인:
   ```python
   import os
   print(os.getenv('CAPTCHA_API_KEY'))  # None이 아니어야 함
   ```
2. `.env.local` 파일 위치 확인 (프로젝트 루트)
3. 서버 재시작

---

## 📖 API 참고

### 2Captcha 공식 문서

- 메인: https://2captcha.com
- API 문서: https://2captcha.com/2captcha-api
- reCAPTCHA v2: https://2captcha.com/2captcha-api#solving_recaptchav2_new

### 대체 서비스

만약 2Captcha가 마음에 들지 않으면:

1. **Anti-Captcha**: https://anti-captcha.com
   - 비용: 비슷함
   - 속도: 약간 빠름

2. **CapMonster Cloud**: https://capmonster.cloud
   - 비용: 약간 저렴
   - 속도: 보통

**참고**: 물바다AI는 2Captcha API와 호환됩니다. 다른 서비스를 사용하려면 코드 수정이 필요합니다.

---

## ✅ 권장 설정

### 운영 환경 (Production)

```env
# .env.local
CAPTCHA_API_KEY=실제_API_키
```

- 쿠키 + 2Captcha 조합
- 완전 자동화
- 월 비용: $0.01~$1

### 테스트 환경 (Development)

```env
# CAPTCHA_API_KEY 설정 안 함
```

- 쿠키 + 수동 해결
- CAPTCHA 발생 시 브라우저에서 직접 해결
- 비용: $0

---

## 🎯 요약

1. **대부분의 경우**: 쿠키 재사용으로 CAPTCHA 없이 로그인 (무료)
2. **쿠키 만료 시**: 2Captcha로 자동 해결 ($0.0005~$0.003/회)
3. **API 키 없을 시**: 수동 해결 (무료)

**결론**: 쿠키 덕분에 비용이 거의 들지 않으면서도, 필요할 때는 자동으로 CAPTCHA를 해결할 수 있습니다! 🎉

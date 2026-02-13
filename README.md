# 물바다AI - 통합 상품 관리 시스템

AI 기술로 상품 썸네일과 상세페이지를 전문가 수준으로 제작하고, 판매 상품을 체계적으로 관리하는 Next.js 애플리케이션입니다.

## 배포 현황

| 서비스 | URL | 비용 |
|--------|-----|------|
| 🎨 프론트엔드 | [Vercel](https://vercel.com/dashboard) | 무료 |
| 🔧 백엔드 API | `https://badaauction-production.up.railway.app` | $5/월 |
| 💾 데이터베이스 | Supabase PostgreSQL | 무료 |
| 📦 이미지 스토리지 | Supabase Storage | 무료 |

**총 운영 비용**: **$5/월**

---

## 주요 기능

### 🛍️ 상품 수집 & 관리
- **다채널 상품 수집**: G마켓, 옥션, 11번가, SSG, 홈플러스, 롯데ON, CJ더마켓, 도매꾹
- **수동/자동 입력 구분**: 사업자 전용 사이트는 가격 수동 입력 지원
- **Cloudflare 우회**: FlareSolverr 연동으로 자동 수집
- **동적 카테고리 시스템**: 138개 카테고리 실시간 동기화

### 💰 가격 모니터링
- **실시간 가격 추적**: 15분마다 자동 체크
- **역마진 알림**: 마진율 자동 계산 및 알림
- **Slack/Discord 알림**: 실시간 알림 시스템

### 📦 주문 관리
- **통합 주문 관리**: 다채널 주문 통합 대시보드
- **Playauto 자동 동기화**: 주문 자동 수집 및 동기화
- **송장 업로드 스케줄러**: 송장 번호 일괄 업로드

### 💰 회계 관리
- **자동 매출/매입 계산**: 주문 데이터 기반 자동 집계
- **손익계산서**: 기간별 P&L 리포트

### 🎨 상세페이지 제작
- **Figma 스타일 에디터**: 드래그 앤 드롭 편집
- **9개 템플릿**: Daily, Food, Fresh, Simple 등
- **이미지 편집**: 크기, 위치, 스타일 조정

### 🤖 자동화
- **재고 자동 관리**: 품절 시 자동 비활성화
- **자동 가격 조정**: 마진 기반 스마트 가격 계산

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | Next.js 16.1.1, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy 2.0, Gunicorn |
| Database | PostgreSQL (Supabase), SQLite (로컬) |
| Storage | Supabase Storage + Cloudflare CDN |
| Hosting | Vercel (FE), Railway (BE) |
| External | OpenAI GPT-4o-mini, Playauto API |

---

## 빠른 시작

```bash
# 프론트엔드
npm install && npm run dev

# 백엔드
cd backend
pip install -r requirements.txt
python main.py
```

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000/docs
- 관리자: http://localhost:3000/admin (비밀번호: 8888)

---

## 문서

| 문서 | 설명 |
|------|------|
| [로컬 개발 설정](./docs/SETUP.md) | 환경 변수, 설치 방법 |
| [배포 가이드](./docs/DEPLOYMENT.md) | 아키텍처, 배포 단계 |
| [API 문서](./docs/API.md) | 엔드포인트 목록 |
| [트러블슈팅](./docs/TROUBLESHOOTING.md) | 문제 해결 가이드 |
| [업데이트 히스토리](./docs/CHANGELOG.md) | 변경 내역 |
| [PlayAuto 가이드](./docs/PLAYAUTO.md) | 채널별 설정, 카테고리 |

### 추가 문서 (docs/md/)

- [FlareSolverr 설정](./docs/md/FLARESOLVERR_SETUP.md)
- [마켓플레이스 코드 가이드](./docs/md/MARKETPLACE_CODES_GUIDE.md)
- [PlayAuto API 문서](./docs/md/PLAYAUTO_API_DOCUMENTATION.md)

---

## 최근 업데이트 (2026-02-13)

### 🎯 조합형 옵션 자동 생성 시스템
- **스마트 옵션 조합**: 쉼표로 구분된 값 입력 시 모든 조합 자동 생성
  - 예: 색상=빨강,파랑 / 사이즈=L,M → 자동으로 4개 조합 생성
  - 실시간 조합 개수 미리보기
- **마켓별 최적화**:
  - 지마켓/옥션: 조합형 단일상품 (std_ol_yn=Y, opt_type=조합형)
  - 쿠팡: 조합형 일반상품 (std_ol_yn=N, opt_type=조합형)
  - 스마트스토어: 독립형 (기존 방식 유지)
- **카테시안 곱 자동 계산**: Backend에서 itertools.product로 모든 조합 생성
- **데이터 구조 개선**:
  - 조합형: `{"색상": ["빨강", "파랑"], "사이즈": ["L", "M"]}` 형태로 저장
  - 독립형: `[{opt_name, opt_value, stock_cnt}]` 배열 형태 유지
- **적용 범위**: 상품 추가 (DetailPage), 상품 수정 (EditProductModal)

### 🐛 UI/UX 버그 수정
- **옵션 입력 개선**:
  - 쉼표(,) 입력 시 값이 사라지는 문제 해결
  - Enter 키로 의도치 않은 상품 추가 방지
  - 모든 옵션 입력 필드에 키보드 이벤트 핸들링 추가
- **옵션 버튼 안정성**: type="button" 누락으로 인한 form submit 문제 해결

### 🔄 카테고리 동적 갱신 시스템
- **완전 동적 카테고리 관리**: 모든 카테고리 선택 UI가 실시간 동기화
- **자동 갱신**: 폴더 추가 후 탭 전환만으로 즉시 반영 (페이지 새로고침 불필요)
- **적용 범위**:
  - 상세페이지 생성기 (DetailPage)
  - 플레이오토 카테고리 매핑 관리
  - 상품 수정 모달 (EditProductModal)
  - 상품 목록 - 새 상품 추가 (ProductSourcingPage)
- **기술**: `visibilitychange` 이벤트 기반 자동 재로드

### 🏪 도매꾹(Domeggook) 소싱처 추가
- **사업자 전용 사이트 지원**: 로그인 필요 사이트 대응
- **수동 입력 모드**: 가격 정보 수동 입력 UI
- **자동/수동 구분**:
  - `input_type` 컬럼 추가 (auto/manual/semi-auto)
  - 상품명, 썸네일은 자동 추출
  - 소싱가, 판매가는 직접 입력
- **필터 및 배지**: 상품 목록에서 ⚡자동추출 / 🖊️수동입력 필터링 가능
- **통계 표시**: 자동/수동 상품 개수 실시간 표시

### 🖼️ 썸네일 핫링킹 방지 우회
- **동적 Referer 설정**: URL별 적절한 Referer 자동 선택
- **403 에러 처리**: 다운로드 실패 시 원본 URL 사용
- **지원 사이트**: 도매꾹, 네이버, SSG, 11번가, 쿠팡 등

### 2026-02-12

- **상품별 개별 마진율 저장 기능**:
  - 수동으로 가격 변경 시 해당 마진율을 상품에 저장
  - 소싱가 변동 시 저장된 마진율로 판매가 자동 계산
  - 마진율 미설정 상품은 기본값 30% 적용
- **PlayAuto adult_yn 설정**: 상품 등록 시 adult_yn을 True로 전송

### 2026-02-11

- **PlayAuto 주문 강제 재동기화**: `?force=true` 파라미터로 이미 동기화된 주문도 재동기화 가능
- **회계 시스템 버그 수정**:
  - datetime JSON 직렬화 오류 수정
  - 총 매출 기간 계산 오류 수정 (오늘 전체 주문 포함)
- **상세페이지 이미지 컨테이너**: + 버튼으로 추가 시 기본 너비 85%로 변경

### 2026-02-10

- **상세페이지 섹션 삭제 기능**: 6개 템플릿 모두에 섹션별 삭제 버튼 추가
- **PlayAuto 카테고리 번호 설정**: 상품 수정 화면에서 sol_cate_no 직접 입력 가능
- **에러 메시지 개선**: PlayAuto 카테고리 미설정 시 친절한 안내 메시지 표시

### 2026-02-09

- **쿠팡 기능 완성**: c_sale_cd_coupang, ol_shop_no_coupang 수집 기능 추가
- **상세페이지 이미지 개선**: + 버튼 이미지 가로 크기 조절, 세로 자동 조정
- **Selenium 완전 제거**: FlareSolverr 기반으로 전환, 서버 리소스 절감
- **품절 오감지 수정**: 구매 버튼 영역만 확인하도록 변경
- **CJ더마켓 소싱처 추가**: cjthemarket.com 지원

[전체 업데이트 내역 보기](./docs/CHANGELOG.md)

---

## 라이선스

MIT License

---

## 감사

[Next.js](https://nextjs.org/) · [FastAPI](https://fastapi.tiangolo.com/) · [Vercel](https://vercel.com/) · [Railway](https://railway.app/) · [Supabase](https://supabase.com/) · [OpenAI](https://openai.com/) · [Playauto](https://playauto.io/)

---

**물바다AI - 상품 관리의 미래** 🚀

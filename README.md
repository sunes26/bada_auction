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
- **다채널 상품 수집**: G마켓, 옥션, 11번가, SSG, 홈플러스, 롯데ON, CJ더마켓
- **Cloudflare 우회**: FlareSolverr 연동으로 자동 수집
- **카테고리 자동 매핑**: 138개 카테고리 계층 구조

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

## 최근 업데이트 (2026-02-11)

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

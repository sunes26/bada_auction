# 모바일 반응형 디자인 가이드

## 📱 개요

현재 데스크톱 위주 UI를 모바일 친화적으로 개선하는 가이드입니다.

**목표**: 768px 이하 모바일 환경에서 최적화된 사용자 경험 제공

## 🎯 Tailwind CSS Breakpoints

```
sm: 640px   # 스마트폰 가로 모드
md: 768px   # 태블릿
lg: 1024px  # 데스크톱
xl: 1280px  # 대형 데스크톱
```

**권장 사용법**:
- 모바일 퍼스트: 기본 스타일은 모바일용으로 작성
- `md:`, `lg:` prefix로 데스크톱 스타일 추가

## 📋 적용 필요 페이지 (7개)

1. ✅ **app/page.tsx** - 메인 레이아웃 및 네비게이션
2. ✅ **HomePage.tsx** - 대시보드
3. ✅ **ProductSourcingPage.tsx** - 상품 관리 (테이블 → 카드 UI)
4. ✅ **UnifiedOrderManagementPage.tsx** - 주문 관리
5. ✅ **DetailPage.tsx** - 상세페이지 생성기
6. ✅ **AccountingPage.tsx** - 회계 페이지
7. ✅ **AdminPage.tsx** - 관리자 페이지

---

## 1️⃣ 메인 네비게이션 (app/page.tsx)

### 현재 문제점
```tsx
// ❌ 데스크톱 전용 네비게이션
<div className="flex relative">
  <NavButton active={currentPage === 'home'} label="메인홈" />
  <NavButton active={currentPage === 'detail'} label="상세페이지 생성기" />
  <NavButton active={currentPage === 'sourcing'} label="상품" />
  <NavButton active={currentPage === 'orders'} label="주문 관리" />
  <NavButton active={currentPage === 'accounting'} label="회계" />
</div>
```

### 해결 방법: 햄버거 메뉴 + 슬라이드 네비게이션

```tsx
'use client';

import { useState } from 'react';
import { Menu, X } from 'lucide-react';

export default function Main() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* 모바일 헤더 (md 미만에서만 표시) */}
      <div className="md:hidden fixed top-0 left-0 right-0 bg-white/90 backdrop-blur-xl border-b border-gray-200 z-50 px-4 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            물바다AI
          </h1>

          {/* 햄버거 버튼 */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="메뉴 열기"
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6 text-gray-700" />
            ) : (
              <Menu className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
      </div>

      {/* 모바일 슬라이드 메뉴 */}
      {mobileMenuOpen && (
        <>
          {/* 배경 오버레이 */}
          <div
            className="md:hidden fixed inset-0 bg-black/50 z-40"
            onClick={() => setMobileMenuOpen(false)}
          />

          {/* 슬라이드 메뉴 */}
          <div className="md:hidden fixed top-0 left-0 bottom-0 w-80 bg-white z-50 shadow-2xl transform transition-transform duration-300">
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-6">메뉴</h2>

              <nav className="space-y-2">
                <MobileNavButton
                  active={currentPage === 'home'}
                  onClick={() => {
                    setCurrentPage('home');
                    setMobileMenuOpen(false);
                  }}
                  icon={<Home className="w-5 h-5" />}
                  label="메인홈"
                />
                <MobileNavButton
                  active={currentPage === 'detail'}
                  onClick={() => {
                    setCurrentPage('detail');
                    setMobileMenuOpen(false);
                  }}
                  icon={<FileText className="w-5 h-5" />}
                  label="상세페이지 생성기"
                />
                {/* ... 다른 메뉴 ... */}
              </nav>
            </div>
          </div>
        </>
      )}

      {/* 데스크톱 네비게이션 (md 이상에서만 표시) */}
      <div className="hidden md:flex justify-between items-center mb-8 px-6 pt-12">
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl p-2 shadow-2xl">
          <div className="flex relative">
            <NavButton active={currentPage === 'home'} label="메인홈" />
            {/* ... */}
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 (모바일: pt-20, 데스크톱: pt-0) */}
      <div className="container mx-auto px-4 md:px-6 pt-20 md:pt-0 pb-12">
        {/* 페이지 렌더링 */}
      </div>
    </div>
  );
}

// 모바일 전용 네비게이션 버튼
function MobileNavButton({ active, onClick, icon, label }: any) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
        active
          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
          : 'text-gray-700 hover:bg-gray-100'
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </button>
  );
}
```

---

## 2️⃣ 그리드 시스템 반응형 (HomePage.tsx)

### 현재 문제점
```tsx
// ❌ 모바일에서 4열이 깨짐
<div className="grid grid-cols-4 gap-6">
  <MetricCard title="총 주문 수" value="100건" />
  <MetricCard title="총 매출액" value="1,000만원" />
  <MetricCard title="평균 마진율" value="30%" />
  <MetricCard title="재고 알림" value="5건" />
</div>
```

### 해결 방법: 반응형 그리드

```tsx
// ✅ 모바일 1열, 태블릿 2열, 데스크톱 4열
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
  <MetricCard title="총 주문 수" value="100건" />
  <MetricCard title="총 매출액" value="1,000만원" />
  <MetricCard title="평균 마진율" value="30%" />
  <MetricCard title="재고 알림" value="5건" />
</div>
```

### 차트 반응형

```tsx
// ✅ 차트 높이 반응형
<div className="h-64 sm:h-80 lg:h-96">
  <Line
    data={chartData}
    options={{
      responsive: true,
      maintainAspectRatio: false,  // ⭐ 중요
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            font: {
              size: window.innerWidth < 640 ? 10 : 12,  // 모바일에서 작게
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            maxRotation: window.innerWidth < 640 ? 45 : 0,  // 모바일에서 회전
            font: {
              size: window.innerWidth < 640 ? 10 : 12,
            },
          },
        },
      },
    }}
  />
</div>
```

---

## 3️⃣ 테이블 → 카드 UI (ProductSourcingPage.tsx)

### 현재 문제점
```tsx
// ❌ 12개 컬럼이 모바일에서 가로 스크롤
<table className="w-full">
  <thead>
    <tr>
      <th>번호</th>
      <th>썸네일</th>
      <th>상품명</th>
      <th>카테고리</th>
      <th>판매가</th>
      <th>소싱가</th>
      <th>마진</th>
      <th>마진율</th>
      <th>소싱처</th>
      <th>상태</th>
      <th>등록일</th>
      <th>액션</th>
    </tr>
  </thead>
  <tbody>
    {/* 데이터 */}
  </tbody>
</table>
```

### 해결 방법: 조건부 렌더링 (테이블 vs 카드)

```tsx
{/* 데스크톱: 테이블 (md 이상) */}
<div className="hidden md:block overflow-x-auto">
  <table className="w-full">
    <thead>
      <tr>
        <th>번호</th>
        <th>썸네일</th>
        <th>상품명</th>
        {/* ... */}
      </tr>
    </thead>
    <tbody>
      {products.map((product) => (
        <tr key={product.id}>
          <td>{product.id}</td>
          <td><img src={product.thumbnail} /></td>
          {/* ... */}
        </tr>
      ))}
    </tbody>
  </table>
</div>

{/* 모바일: 카드 UI (md 미만) */}
<div className="block md:hidden space-y-4">
  {products.map((product) => (
    <div
      key={product.id}
      className="bg-white/80 backdrop-blur-xl rounded-xl shadow-lg border border-white/20 p-4"
    >
      {/* 상단: 썸네일 + 기본 정보 */}
      <div className="flex items-start gap-4 mb-4">
        <img
          src={product.thumbnail}
          alt={product.product_name}
          className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
        />
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm line-clamp-2 mb-1">
            {product.product_name}
          </h3>
          <p className="text-xs text-gray-500">{product.category}</p>
          <span className={`inline-block mt-2 px-2 py-1 text-xs rounded-full ${
            product.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
          }`}>
            {product.is_active ? '활성' : '비활성'}
          </span>
        </div>
      </div>

      {/* 가격 정보 그리드 */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-xs text-gray-500 mb-1">판매가</p>
          <p className="text-sm font-semibold text-blue-600">
            {product.selling_price?.toLocaleString()}원
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">소싱가</p>
          <p className="text-sm font-semibold">
            {product.sourcing_price?.toLocaleString()}원
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">마진</p>
          <p className="text-sm font-semibold text-green-600">
            {(product.selling_price - product.sourcing_price).toLocaleString()}원
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">마진율</p>
          <p className="text-sm font-semibold">
            {product.margin_percent?.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* 액션 버튼 */}
      <div className="flex gap-2">
        <button
          onClick={() => handleViewDetail(product)}
          className="flex-1 py-2 px-3 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors active:scale-95"
        >
          상세보기
        </button>
        <button
          onClick={() => handleEdit(product)}
          className="flex-1 py-2 px-3 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors active:scale-95"
        >
          수정
        </button>
        <button
          onClick={() => handleDelete(product.id)}
          className="py-2 px-4 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors active:scale-95"
        >
          삭제
        </button>
      </div>
    </div>
  ))}
</div>
```

---

## 4️⃣ 터치 친화적 버튼

### 현재 문제점
```tsx
// ❌ 터치 영역이 작음 (< 44px)
<button className="px-3 py-1 bg-blue-500 text-white rounded">
  클릭
</button>
```

### 해결 방법: 최소 44x44px 보장

```tsx
// ✅ 모바일 터치 최적화
<button className="px-4 py-3 sm:px-3 sm:py-2 bg-blue-500 text-white rounded-lg text-base sm:text-sm font-medium touch-manipulation active:scale-95 transition-transform">
  클릭
</button>

/* CSS 추가 권장 */
.touch-manipulation {
  touch-action: manipulation;  /* 더블 탭 줌 방지 */
}
```

---

## 5️⃣ 텍스트 크기 반응형

### 현재 문제점
```tsx
// ❌ 모든 화면에서 동일한 크기
<h1 className="text-4xl font-bold">제목</h1>
<p className="text-base">본문</p>
```

### 해결 방법: 반응형 텍스트

```tsx
// ✅ 모바일에서 작게, 데스크톱에서 크게
<h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold">제목</h1>
<p className="text-sm sm:text-base">본문</p>

/* 또는 clamp 사용 */
<h1 className="text-[clamp(1.5rem,4vw,2.5rem)] font-bold">제목</h1>
```

---

## 6️⃣ 모달 반응형

### 현재 문제점
```tsx
// ❌ 모바일에서 화면을 꽉 채워야 함
<div className="fixed inset-0 flex items-center justify-center">
  <div className="bg-white rounded-lg p-6 w-[500px]">
    {/* 모달 내용 */}
  </div>
</div>
```

### 해결 방법: 모바일 전체 화면, 데스크톱 고정 너비

```tsx
// ✅ 모바일 풀스크린, 데스크톱 센터 모달
<div className="fixed inset-0 flex items-center justify-center p-4 sm:p-0">
  <div className="bg-white rounded-lg w-full h-full sm:w-[500px] sm:h-auto sm:max-h-[90vh] overflow-auto p-6">
    {/* 모달 내용 */}
  </div>
</div>
```

---

## 7️⃣ 폼 입력 최적화

### 현재 문제점
```tsx
// ❌ 작은 입력 필드
<input
  type="text"
  className="px-3 py-2 border rounded"
/>
```

### 해결 방법: 큰 터치 영역, 적절한 input 타입

```tsx
// ✅ 모바일 최적화 입력
<input
  type="text"
  inputMode="text"  // 모바일 키보드 최적화
  className="w-full px-4 py-3 text-base border rounded-lg focus:ring-2 focus:ring-blue-500"
/>

<input
  type="number"
  inputMode="numeric"  // 숫자 키보드
  pattern="[0-9]*"
  className="w-full px-4 py-3 text-base border rounded-lg"
/>

<input
  type="tel"
  inputMode="tel"  // 전화번호 키보드
  className="w-full px-4 py-3 text-base border rounded-lg"
/>
```

---

## 8️⃣ 이미지 최적화

```tsx
// ✅ 반응형 이미지
<img
  src={product.thumbnail}
  alt={product.name}
  className="w-full sm:w-40 h-auto object-cover"
  loading="lazy"  // 지연 로딩
/>

// Next.js Image 컴포넌트 사용 권장
import Image from 'next/image';

<Image
  src={product.thumbnail}
  alt={product.name}
  width={160}
  height={160}
  className="w-full sm:w-40 h-auto"
  placeholder="blur"
/>
```

---

## 9️⃣ 스크롤 최적화

```tsx
// ✅ 모바일 스크롤 부드럽게
<div className="overflow-y-auto overscroll-contain scroll-smooth">
  {/* 콘텐츠 */}
</div>

/* CSS 추가 */
html {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;  /* iOS 관성 스크롤 */
}
```

---

## 🔟 성능 최적화 체크리스트

- [ ] 이미지 lazy loading 적용
- [ ] Chart.js `maintainAspectRatio: false` 설정
- [ ] 불필요한 리렌더링 방지 (React.memo, useMemo)
- [ ] 모바일에서 불필요한 애니메이션 제거
- [ ] 터치 이벤트 최적화 (`touch-action: manipulation`)
- [ ] 폰트 크기 clamp() 또는 반응형 클래스 사용
- [ ] 모달/드로어 열릴 때 body 스크롤 방지

---

## 📱 테스트 방법

### 1. Chrome DevTools
```
F12 → Device Toolbar (Ctrl+Shift+M)
→ iPhone 12 Pro (390x844)
→ iPad Air (820x1180)
```

### 2. 실제 기기 테스트
```bash
# 로컬 네트워크에서 접근 가능하도록 설정
npm run dev -- --host 0.0.0.0

# 모바일에서 접속
http://192.168.x.x:3000
```

### 3. Responsive Design Checker
- [responsivedesignchecker.com](https://responsivedesignchecker.com/)
- [screenfly.org](https://screenfly.org/)

---

## ✅ 우선순위별 작업 순서

### Phase 1: 핵심 네비게이션 (1시간)
1. `app/page.tsx` - 햄버거 메뉴 추가

### Phase 2: 주요 페이지 (3시간)
1. `HomePage.tsx` - 그리드 반응형
2. `ProductSourcingPage.tsx` - 테이블 → 카드 UI

### Phase 3: 나머지 페이지 (4시간)
1. `UnifiedOrderManagementPage.tsx`
2. `DetailPage.tsx`
3. `AccountingPage.tsx`
4. `AdminPage.tsx`

---

## 📚 참고 자료

- [Tailwind CSS Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [Touch Target Sizes (Google)](https://web.dev/accessible-tap-targets/)
- [Mobile UX Best Practices](https://material.io/design/layout/responsive-layout-grid.html)
- [Chart.js Responsive](https://www.chartjs.org/docs/latest/configuration/responsive.html)

---

## 💡 빠른 시작 예제

가장 빠르게 적용할 수 있는 패턴:

```tsx
// 1. 그리드 반응형
className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"

// 2. 조건부 렌더링
<div className="hidden md:block">{/* 데스크톱 전용 */}</div>
<div className="block md:hidden">{/* 모바일 전용 */}</div>

// 3. 반응형 텍스트
className="text-sm sm:text-base lg:text-lg"

// 4. 반응형 패딩/마진
className="px-4 sm:px-6 lg:px-8"

// 5. 터치 최적화 버튼
className="py-3 px-4 text-base active:scale-95 touch-manipulation"
```

이 패턴들을 적용하면 80%의 반응형 문제가 해결됩니다!

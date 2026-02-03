# PlayAuto ESM 채널 등록 제한

## ✅ 해결됨 (2026-02-03)

**A006 (옥션) ESM 템플릿을 default_templates에서 제거하여 해결**
- 현재 등록 채널: A001 (네이버), A077 (스마트스토어)
- 모든 카테고리 (식품 포함) 등록 가능

---

## 문제 (과거)

상품 등록 시 "ESM은 단일상품만 등록 가능합니다" 에러가 발생했습니다.

```
[플레이오토] 상품 등록 실패: ESM은 단일상품만 등록 가능합니다.
```

**원인**: A006 (옥션) 템플릿 2235971이 ESM 모드로 설정되어 있었음

## 원인

**ESM (eBay Smile Market)**은 G마켓/옥션의 간편 판매 방식으로, 다음과 같은 제약사항이 있습니다:

1. **특정 카테고리만 지원**
   - 도서, 음반, DVD 등 일부 카테고리만 ESM 등록 가능
   - 식품, 생활용품 등 대부분의 카테고리는 ESM 미지원

2. **단일 상품만 등록 가능**
   - 세트 구성 상품 불가
   - 옵션 상품 불가 (색상, 사이즈 등)

3. **계정 권한 필요**
   - ESM 판매 권한이 있는 계정만 사용 가능

## 자동 해결

시스템이 **자동으로 ESM 에러를 감지하고 ESM 채널을 제외한 나머지 채널로 재시도**합니다.

### 동작 방식

1. 상품 등록 시 ESM 에러 발생
2. 자동으로 ESM 채널을 제외
3. 나머지 채널(네이버 스마트스토어, 쿠팡 등)로 재등록 시도

```python
# 코드 예시
if "ESM" in error_msg and "단일상품" in error_msg:
    # site_list에서 ESM 제외
    filtered_site_list = [
        site for site in site_list
        if site.get("shop_cd") not in ["ESM", "esm"]
    ]
    # 재시도
    result = await register_product(product_data)
```

## 수동 해결 (권장)

PlayAuto 설정에서 **ESM 채널을 기본 템플릿에서 제거**하는 것을 권장합니다.

### 방법 1: 관리자 페이지에서 제거

1. 관리자 페이지 → PlayAuto 설정
2. 기본 템플릿 목록에서 ESM 채널 찾기
3. ESM 채널 삭제

### 방법 2: 데이터베이스에서 직접 제거

```sql
-- default_templates 조회
SELECT setting_value FROM playauto_settings
WHERE setting_key = 'default_templates';

-- ESM 채널 제거 후 업데이트
UPDATE playauto_settings
SET setting_value = '[{"shop_cd":"NSM","shop_id":"...","template_no":123}]'
WHERE setting_key = 'default_templates';
```

## ESM 채널 식별

다음 shop_cd 값이 ESM 채널입니다:
- `ESM`
- `esm`
- `Esm`

## 관련 코드

**backend/api/products.py**
```python
# ESM 채널 자동 제외
site_list = [
    {...}
    for t in default_templates
    if t.get("shop_cd") not in ["ESM", "esm"]
]

# ESM 에러 시 자동 재시도
if "ESM" in error_msg and "단일상품" in error_msg:
    filtered_site_list = [
        site for site in site_list
        if site.get("shop_cd") not in ["ESM", "esm", "Esm"]
    ]
    result = await register_product(filtered_site_list)
```

## 대체 채널

ESM 대신 다음 채널을 사용하세요:

| 채널 | shop_cd | 지원 카테고리 | 비고 |
|------|---------|--------------|------|
| 네이버 스마트스토어 | NSM | 전 카테고리 | 권장 |
| 쿠팡 | CPM | 전 카테고리 | 승인 필요 |
| 11번가 | STM | 전 카테고리 | |
| G마켓 (일반) | GMK | 전 카테고리 | ESM 아님 |
| 옥션 (일반) | AUC | 전 카테고리 | ESM 아님 |

## 적용된 수정사항

### 1. A006 템플릿 제거 (2026-02-03)
```bash
# backend/fix_remove_esm_template.py 실행
# default_templates에서 A006 (옥션 ESM 템플릿) 제거
# 결과: A001 (네이버), A077 (스마트스토어)만 사용
```

### 2. ESM 에러 자동 감지 및 재시도 강화
**backend/api/products.py:693-711**
```python
# ESM 에러 감지 시 A006도 함께 필터링
if "ESM" in error_msg and "단일상품" in error_msg:
    filtered_site_list = [
        site for site in product_data.get("site_list", [])
        if site.get("shop_cd") not in ["ESM", "esm", "Esm", "A006"]
    ]
    # 나머지 채널로 재시도
```

## 참고

- ESM은 eBay Korea의 간편 판매 모드입니다
- 일반 G마켓/옥션 등록(`GMK`, `AUC`)은 모든 카테고리 지원
- ESM보다 일반 등록을 권장합니다
- **현재 시스템은 네이버(A001)와 스마트스토어(A077)를 사용하여 모든 카테고리 등록 가능**

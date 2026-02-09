# 플레이오토(Playauto) API 상세 명세서 (v1.1 Legacy)

본 문서는 플레이오토 레거시(v1.1) API 환경의 모든 엔드포인트와 파라미터를 상세히 기술한 통합 명세서입니다. 모든 용어는 문맥에 맞게 교정되었습니다.

**Base URL**: `https://openapi.playauto.io/api`

---

## 인증 (Authentication)

모든 API 요청에는 다음 헤더가 필수적으로 포함되어야 합니다.

| 헤더 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `x-api-key` | String | O | 승인 시 발급받은 API KEY |
| `Authorization` | String | O | 인증 토큰 (Token {Access_Token} 형식) |

---

## API 엔드포인트 리스트

### 1. 배송처 조회

사용 중인 플레이오토 배송처 목록을 조회합니다.

**Endpoint**: `GET /api/depots`

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `masking_yn` | Boolean | O | `true` | 개인정보 마스킹 처리 여부 |

#### Response Fields

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `no` | Number | O | 배송처 번호 |
| `sol_no` | Number | O | 솔루션 번호 |
| `default_yn` | Boolean | O | 기본 설정 여부 |
| `name` | String | O | 배송처명 |
| `address` | String | O | 배송처 주소 |
| `zip` | String | O | 우편번호 |
| `use_yn` | Boolean | O | 사용 여부 |
| `charge_name` | String | O | 담당자명 |

---

### 2. HS코드 조회

수출입 품목 분류를 위한 HS코드 목록을 조회합니다.

**Endpoint**: `GET /api/hscds`

#### Response Fields

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `hscd` | String | O | HS코드 |
| `item_kor` | String | O | 상세 정보(품명) |
| `hz` | String | O | 기초 세율 |

---

### 3. 로그 조회

주문 및 상품 정보의 작업 로그를 조회합니다.

**Endpoint**: `GET /api/logs/v1.1`

#### Query Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `unliq` | String | | 주문 고유번호 (주문으로 검색 시 필수 입력) |
| `inq_unliq` | String | | 문의 고유번호 (문의로 검색 시 필수 입력) |
| `prod_no` | String | | SKU상품 고유번호 (SKU상품으로 검색 시 필수 입력) |
| `ol_shop_no` | String | | 상품 고유번호 (상품으로 검색 시 필수 입력) |
| `sddate` | String | | 검색 시작일 (YYYY-MM-DD) |
| `eddate` | String | | 검색 종료일 (YYYY-MM-DD) |

#### Response Fields

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `results` | Object | O | 조회된 로그 리스트 |
| `wdate` | String | O | 등록일 |
| `name` | String | O | 작업자 이름 |
| `content` | String | O | 작업 내역 |
| `result` | String | O | 작업 결과 |

---

### 4. 매입처 조회

사용 중인 플레이오토 매입처 목록을 조회합니다.

**Endpoint**: `GET /api/suppliers`

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `masking_yn` | Boolean | | `false` | 개인정보 마스킹 처리 여부 |

#### Response Fields

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `no` | Number | O | 매입처 번호 |
| `name` | String | O | 매입처 명칭 |
| `business_number` | String | O | 사업자 등록번호 |
| `address` | String | O | 매입처 주소 |
| `charge_name` | String | O | 담당자 이름 |

---

### 5. 원산지 조회

플레이오토 시스템에 등록된 원산지 목록을 조회합니다.

**Endpoint**: `GET /api/origins`

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 허용값 | 설명 |
|---------|------|------|--------|--------|------|
| `group` | String | | `partial` | `exact`, `partial` | 국내/외 및 지역 분류 |
| `name` | String | | | | 검색어 |
| `combine` | String | | | `or`, `and` | 검색 조건 조합 |

---

### 6. 택배사 코드 조회

플레이오토 표준 
 코드 리스트를 조회합니다.

**Endpoint**: `GET /api/carriers`

#### Response Fields

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `carrier_code` | Number | O | 택배사 코드 |
| `carrier_name` | String | O | 택배사 명칭 |

---

### 7. 공지사항 조회

플레이오토 시스템 공지사항을 조회합니다.

**Endpoint**: `GET /api/announcements`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `start` | Number | | 페이징 시작 번호 (0부터) |
| `length` | Number | | 조회 개수 |
| `search_key` | String | | 검색 타입 (title, content, all) |
| `search_word` | String | | 검색어 |
| `noti_type` | String | | 공지 타입 (일반, 부분 등) |
| `sdatr` / `edatr` | String | | 등록일 시작/종료 (YYYY-MM-DD) |

---

### 8. 쇼핑몰 코드 조회

지원하는 쇼핑몰 코드 리스트를 조회합니다.

**Endpoint**: `GET /api/shops`

#### Query Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `used` | String | | 사용 중인 쇼핑몰 조회 여부 (true/false) |
| `etc_detail` | String | | 쇼핑몰별 기능/옵션 상세 포함 여부 |
| `usable_shop` | String | | 사용 가능 여부 (기능 지원 여부) |

---

### 9. 쇼핑몰 계정 등록

쇼핑몰 판매 채널의 계정을 등록합니다.

**Endpoint**: `POST /api/shop/add`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `id` | String | O | 쇼핑몰 아이디 |
| `pwd` | String | O | 쇼핑몰 비밀번호 |
| `shop_cd` | String | O | 쇼핑몰 코드 |
| `etc` | Array | O | 쇼핑몰별 추가 인증 정보 (API Key 등) |

---

### 10. 쇼핑몰 계정 수정

등록된 쇼핑몰 계정 정보를 수정합니다.

**Endpoint**: `PATCH /api/shop/edit`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `id` / `pwd` | String | O | 계정 및 비밀번호 |
| `shop_cd` | String | O | 쇼핑몰 코드 |
| `etc` | Array | O | 수정할 추가 정보 |

---

### 11. 쇼핑몰 계정 삭제

등록된 쇼핑몰 계정을 삭제합니다.

**Endpoint**: `DELETE /api/shop/delete`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `id` | String | O | 쇼핑몰 아이디 |
| `shop_cd` | String | O | 쇼핑몰 코드 |

---

### 12. 주문 상세 조회

주문의 상세 정보를 조회합니다.

**Endpoint**: `GET /api/order`

참고: 다수의 파라미터를 지원하며 상세 목록은 원본 문서에 명시되지 않은 매우 광범위한 목록을 포함합니다.

---

### 13. 배송정보 업데이트 (송장 등록)

주문건의 송장 번호를 입력하고 배송 상태를 수정합니다.

**Endpoint**: `PUT /api/order/setnotice`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `orders` | Array | O | 주문 정보 리스트 (bundle_no, carr_no, invoice_no 포함) |
| `overwrite` | Boolean | | 송장 번호 덮어쓰기 여부 |
| `change_complete` | Boolean | | 배송 완료 상태로 즉시 변경 여부 |

---

### 14. 보류 처리

주문건을 보류 또는 출고대기 상태로 변경합니다.

**Endpoint**: `PUT /api/order/hold`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `bundle_codes` | Array | O | 보류 처리할 묶음 번호 리스트 |
| `holdReason` | String | O | 보류 사유 |
| `status` | String | | 처리할 상태 (출고대기, 주문보류 등) |

---

### 15. 주문 삭제

주문 정보를 삭제합니다.

**Endpoint**: `DELETE /api/order/delete`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `unliqList` | Array | O | 삭제할 주문 고유번호 리스트 |

---

### 16. 주문 등록

수동으로 주문 정보를 등록합니다.

**Endpoint**: `POST /api/order/add`

#### Body Parameters (주요 항목)

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `ord_date` / `ord_time` | String | | 주문 일시 |
| `shop_cd` / `seller_id` | String | | 판매처 코드 및 아이디 |
| `order_no` | String | | 쇼핑몰 주문번호 |
| `to_name` / `to_tel` | String | | 수령자 명칭 및 연락처 |
| `to_addr1` / `to_addr2` | String | | 수령자 주소 |
| `cart_info` | Object | | 배송 품목 리스트 |

---

### 17. 주문 분할

한 주문 내의 여러 상품을 개별 주문으로 분리합니다.

**Endpoint**: `PUT /api/order/divide`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `unliqList` | Array | O | 분할할 상품의 주문 고유번호 리스트 |
| `type` | String | | 분할 방식 (divide, bundle) |

---

### 18. 주문 수정

등록된 주문 정보를 수정합니다.

**Endpoint**: `PATCH /api/order/edit`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `unliq` | String | O | 주문 고유번호 |
| 수령인/주문 정보 필드 | | | 변경하고자 하는 정보 전송 |

---

### 19. 주문 합포장

여러 주문건을 하나의 묶음으로 합칩니다.

**Endpoint**: `PUT /api/order/combine`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `unliqList` | Array | O | 합칠 주문 고유번호 리스트 |

---

### 20. 출고 지시

주문건을 출고 지시 상태로 변경합니다.

**Endpoint**: `PUT /api/order/instruction`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `bundle_codes` | Array | O | 묶음 번호 리스트 |
| `auto_bundle` | Boolean | O | 주문 묶음 여부 |

---

### 21. 주문상태변경

주문의 처리 단계를 변경합니다.

**Endpoint**: `PATCH /api/orders/status`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `bundle_codes` / `unlqs` | Array | | 대상 리스트 |
| `status` | String | O | 변경할 상태 (신규주문, 배송중, 배송완료, 고취소 등) |

---

### 22. 규칙 사은품 분배

설정된 규칙에 따라 주문에 사은품을 추가합니다.

**Endpoint**: `PATCH /api/order/gift/distribution`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `bundle_codes` | Array | | 대상 묶음 번호 리스트 |

---

### 23. 상태별 주문수량 조회

주문 처리 단계별 건수를 조회합니다.

**Endpoint**: `GET /api/orders/count`

#### Query Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `ord_status` | String | O | 조회할 주문 상태 |
| `sddate` / `eddate` | Date | | 조회 기간 |

---

### 24. 중복의심 해제

중복 주문으로 분류된 건의 의심을 해제합니다.

**Endpoint**: `PATCH /api/orders/suspicious/release`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `unliqs` | Array | O | 대상 주문 고유번호 리스트 |

---

### 25. 머리말 꼬리말 조회

상세페이지 등에 노출될 머리말/꼬리말 문구를 조회합니다.

**Endpoint**: `POST /api/adornments`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `search_key` / `search_word` | String | | 검색 필터 |
| `adornmentTarget` | String | | 타겟 (상품등록, 송장등록) |
| `adornmentType` | String | | 타입 (공지사항, 배송안내 등) |
| `viewPosition` | String | | 위치 (머리말, 꼬리말) |

---

### 26. 송장번호 조회

등록된 송장 번호 내역을 조회합니다.

**Endpoint**: `GET /api/invoices`

---

### 27. 송장번호 등록

송장 번호를 시스템에 등록합니다.

**Endpoint**: `POST /api/invoice`

---

### 28. 송장번호 수정

등록된 송장 번호를 수정합니다.

**Endpoint**: `PATCH /api/invoice`

---

### 29. 온라인상품 판매수량 수정

쇼핑몰에 판매 중인 상품의 재고 수량을 실시간 수정합니다.

**Endpoint**: `PATCH /api/products/take-cnt`

#### Body Parameters (주요)

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `products` | Array | O | 대상 목록 |
| `sku_cd` | String | O | SKU 코드 |
| `stock_cnt` | Number | O | 반영할 재고 개수 |
| `status` | String | O | 상태 (판매, 품절) |

---

### 30. 온라인상품 연동 수정/해제

쇼핑몰과 플레이오토 간의 연동 상태를 수정하거나 해제합니다.

**Endpoint**: `PATCH /api/products/setShopLinkInfo`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `type` | String | O | 작업 타입 (edit: 수정, stop: 해제) |
| `sale_data` | Array | O | 연동 상품 데이터 리스트 |

---

### 31. 카테고리 조회

플레이오토 카테고리 목록과 쇼핑몰 카테고리 매핑 정보를 조회합니다.

**Endpoint**: `GET /api/categorys`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `start` / `length` | Number | | 페이징 및 조회 개수 (최대 1000) |

---

### 32. 템플릿 조회

등록 시 사용하는 템플릿 리스트를 조회합니다.

**Endpoint**: `GET /api/templates`

---

### 33. 수집 상품 삭제

쇼핑몰에서 수집된 임시 상품 목록을 삭제합니다.

**Endpoint**: `DELETE /api/product/online/listOfScrap`

---

### 34. 고객문의 조회

쇼핑몰에서 수집된 고객 문의 목록을 조회합니다.

**Endpoint**: `GET /api/inquiries/merchant`

---

### 35. 문의답변 등록

수집된 고객 문의에 답변을 등록합니다.

**Endpoint**: `PUT /api/inquiry/answer`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `inquirys` | Array | O | 문의 고유번호(inq_unliq) 및 답변 내용(content) 리스트 |

---

### 36. SKU상품 목록 조회

등록된 SKU 상품 목록을 조회합니다.

**Endpoint**: `GET /api/product/sku/list`

---

### 37. SKU상품 상세 조회

특정 SKU 상품의 상세 정보를 조회합니다.

**Endpoint**: `GET /api/product/sku/info`

---

### 38. SKU상품 등록

새로운 SKU 상품을 등록합니다.

**Endpoint**: `POST /api/product/sku/add`

#### Body Parameters (주요 항목)

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `prod_name` | String | O | 상품명 |
| `barcodes` | Array | | 바코드 리스트 |
| `supplier_no` | Number | | 매입처 번호 |

---

### 39. SKU상품 수정

등록된 SKU 상품의 정보를 수정합니다.

**Endpoint**: `PATCH /api/product/sku/edit`

---

### 40. 세트상품 조회

등록된 세트 상품 목록을 조회합니다.

**Endpoint**: `GET /api/product/sets`

---

### 41. 세트상품 등록

여러 SKU를 조합하여 세트 상품을 등록합니다.

**Endpoint**: `POST /api/stock/set-add`

#### Body Parameters (주요 항목)

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `set_cd` / `set_name` | String | O | 세트 코드 및 명칭 |
| `setProductList` | Array | O | 구성 SKU 리스트 및 각 구성 수량 |

---

### 42. 세트상품 수정

세트 상품 구성을 수정합니다.

**Endpoint**: `PUT /api/stock/set-edit`

---

### 43. 재고수정

특정 배송처의 SKU 재고를 입고 또는 출고 처리합니다.

**Endpoint**: `PUT /api/stock/manage/v1.1`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stocks` | Array | O | 리스트 (sku_cd, depot_no, set[입고/출고], count 포함) |

---

### 44. 재고변동조회

재고의 입출고 변동 내역을 조회합니다.

**Endpoint**: `GET /api/stocks/v1`

---

### 45. 정산내역 조회

쇼핑몰 정산 내역을 조회합니다.

**Endpoint**: `GET /api/settlements/v1`

---

### 46. 주문관리 정산 조회

주문관리 차원에서의 정산 데이터를 조회합니다.

**Endpoint**: `GET /api/settlements/order`

---

### 47. 메모 등록

주문, 상품, 문의에 메모를 등록합니다.

**Endpoint**: `POST /api/memo`

#### Body Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `memo_type` | String | O | 대상 타입 (ord, ol_shop, prod) |
| `content` | String | O | 메모 내용 |
| `unliq` 등 | String | | 대상의 고유번호 |

---

### 48. 메모 삭제

등록된 메모를 삭제합니다.

**Endpoint**: `DELETE /api/memo`

---

### 49. 메모 수정

등록된 메모의 내용을 수정합니다.

**Endpoint**: `PUT /api/memo`

---

## 에러 코드 가이드 (Full List)

### 공통 에러

| 코드 | 설명 |
|------|------|
| 400 | 필수 파라미터 누락 |
| e1001~e1005 | 사용자 정보 조회 실패 및 인증 실패 |
| e1006 | OPEN-API 미승인 사용자 |
| e1012 | 조회되는 쇼핑몰 정보가 없음 |
| e1013 | 이미 등록된 쇼핑몰 계정 |
| e1017 | 데이터 용량 초과(10MB) |

### 주문 에러

| 코드 | 설명 |
|------|------|
| o2001 | 존재하지 않는 주문 정보 |
| o2003 | 유효하지 않은 택배사 번호 |
| o2007 | 배송 정보 중복 입력 |
| o2009 | 이미 등록된 주문 번호 |
| o2032 | 분할/합포장 타입 오류 |
| o2044 | 조회 건수 제한 초과 (최대 3000건) |

### 문의 에러

| 코드 | 설명 |
|------|------|
| e5001 | 답변 처리 완료된 문의 |
| e5002 | 존재하지 않는 문의 |

### 재고 및 상품 에러

| 코드 | 설명 |
|------|------|
| e3001 | SKU 코드 길이 초과 (40자) |
| e3008 | 중복된 SKU 코드 |
| e3015 | 존재하지 않는 배송처 번호 |
| e4033 | 존재하지 않는 상품 번호 |

### 정산 에러

| 코드 | 설명 |
|------|------|
| e7003/e7004 | 날짜 형식 오류 |
| e7012 | 조회 개수 오류 |

### 메모 에러

| 코드 | 설명 |
|------|------|
| e8001 | 존재하지 않는 주문 고유번호 |
| e8004 | 잘못된 메모 유형 |

---

## 참고사항

- 모든 API는 HTTPS 프로토콜을 사용합니다.
- API 키는 플레이오토 개발자 센터에서 발급받을 수 있습니다.
- 응답 형식은 JSON입니다.
- 날짜 형식은 `YYYY-MM-DD` 또는 `YYYY-MM-DD HH:mm:ss` 형식을 사용합니다.

---

**문서 버전**: v1.1.2 (Full No-Omission Specification)
**최종 업데이트**: 2026-01-27
**출처**: 플레이오토 API 상세 명세서 (교정본) PDF

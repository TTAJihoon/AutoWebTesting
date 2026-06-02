# 08 — 기능 리스트 정제 & 확정 게이트 (로그인 편중 해소)

> **목적**: "특정 도메인(로그인/인증)이 TC를 과대표집하는" 분포 왜곡을 *입력(기능 리스트) 단계*에서 차단한다.
> **상태**: 설계 (구현 전, 사용자 검토 대기)
> **관련 결정**: D51 / D52 / D53 (본 문서에서 신규 정의 → [06-decisions.md](06-decisions.md)에 등재)
> **연관 단계**: Stage 0(DOM 스캔) · Stage 1(ingest) · Stage 1b(consolidate) · Stage 2(TC 설계)

---

## 1. 문제 정의 (실측 근거)

run `89f3ba56` (TC 484건) 실측:

| 측정 기준 | 값 |
|---|---|
| 분류(대/중/소)가 로그인·인증·계정인 TC | **30.0%** (145/484) |
| 시나리오·입력·예상값에 "로그인" 언급(전제조건 포함) | **33.5%** (162/484) |
| 로그인 폼이 감지된 페이지 | **44/89** (49.4%) |

대분류 분포 상위 — **같은 인증 도메인이 3개 이름으로 파편화**:

```
64 (13.2%)  User Management     ┐
57 (11.8%)  Authentication      ├─ 동일 인증/계정 도메인 = 141건 (29%)
20 ( 4.1%)  Account Management  ┘
54 (11.2%)  Navigation
...
```

> **결론**: "로그인이 절반"은 체감 과장이나, **인증·계정 도메인이 단일 최대 비중(~30%)**이고 **3개 카테고리로 분열**되어 실사용 신뢰를 떨어뜨린다. 원인은 데이터(입력) 단계에 있다.

---

## 2. 근본 원인 (코드 근거)

| # | 원인 | 코드 위치 | 메커니즘 |
|---|---|---|---|
| **C1** | **전역 컴포넌트 페이지별 중복 추출** | `stage0_dom_scan.py:26` `_extract_elements()` — 페이지마다 독립 추출 | GnuBoard5 헤더 로그인 박스(`#ol_id`/`#ol_pw`/`#ol_submit`)가 44개 페이지에서 44회 추출 → raw feature 다수가 로그인 |
| **C2** | **카테고리 어휘 통제 부재** | `prompts/tc_design.md`·`feature_consolidate.md` — `category_major` 자유 서술 | LLM이 배치마다 `User Management`/`Authentication`/`Account Management`를 임의 부여 → 같은 도메인이 분열, 통합 패스가 "다른 대분류=다른 기능"으로 오판 |
| **C3** | **leaf 정규화의 얕은 수준** | `stage1_ingest.py:142` dedup 키 `(major, mid, normalized_leaf)` | `_normalize_leaf_name`은 공백·숫자·기호만 제거. major/mid가 다르면(C2) 동일 로그인이 합쳐지지 않음 |
| **C4** | **확정 게이트 부재 + 선형 증폭** | `orchestrator.py:187` `run_stage1` → `:209` `run_stage2` 직결 / `prompts/tc_design.md` "TC 3~8개" | Stage1↔2 사이 사람 확정 없음. 과대표집 leaf가 leaf당 3~8 TC로 선형 증폭 |

**개선 순서의 논리**: C1·C2를 먼저 고쳐 *입력을 정화*해야, C4 게이트에 올라오는 노이즈가 줄어 사람이 매번 같은 중복을 손으로 지우지 않는다. (4인 토론 합의)

---

## 3. 개선안 (3개 결정)

### D51 — 전역 컴포넌트 dedup (C1 해소) · 1순위

**아이디어**: 헤더·푸터·네비처럼 **여러 페이지에 동일 셀렉터로 반복 등장하는 요소**를 "전역 컴포넌트"로 식별해, DOM_SPEC LLM 호출 *전에* **1회만** 명세화한다.

**탐지 기준 (결정적·규칙 기반, LLM 불필요)**:
- 요소 지문(signature) = `(tag, id, name, type, normalized_text)` — `href`의 쿼리/도메인은 제외, text는 정규화.
- 전역 판정 = 동일 지문이 **스캔 페이지의 ≥ `GLOBAL_RATIO`(기본 0.5)** 에서 등장.
- 단, 페이지 모수가 작을 때 오탐 방지: 전체 페이지 `< MIN_PAGES_FOR_GLOBAL`(기본 5)이면 비활성.

**처리 흐름** (Stage 0 내부, `_extract_elements` 결과 취합 직후):
```
모든 페이지 요소 수집
  → 지문별 등장 페이지 수 카운트
  → 전역 지문 집합 G 산출
  → 페이지별 요소에서 G 제거 + "__global__" 가상 페이지에 G를 1벌만 적재
  → DOM_SPEC는 각 페이지(전역 제거됨) + __global__ 1회 = 총 (페이지수 + 1)회 호출
```

**산출물 변화**:
- feature에 `scope: "global" | "page"` 필드 추가 (전역 컴포넌트 출신 여부).
- `source_url` = 전역이면 `"__global__"`, 아니면 기존 URL.
- DOM_SPEC 호출 횟수 **감소**(중복 페이지의 헤더·푸터 재명세 제거) → 토큰·시간 절감 부수효과.

**meta.json 기록**: `global_component_report = {total_pages, global_signatures, removed_per_page_avg, sample_signatures[]}`.

**검증 지표**: 재실행 후 "인증 도메인 TC 비율 30% → ?%" 및 "raw feature 중 로그인 비율" 직접 비교.

**안전장치**: `GLOBAL_RATIO`·`MIN_PAGES_FOR_GLOBAL`는 `RunConfig`로 노출. 전역 dedup 끄기 옵션 제공(`dedup_global_components: bool = True`). **손실 0 원칙**: 전역 요소는 삭제가 아니라 `__global__`로 *이동*이므로 기능 누락 없음.

---

### D52 — 카테고리 통제 어휘(taxonomy) (C2·C3 보조 해소) · 2순위 (quick win)

**아이디어**: `category_major`를 **고정 목록 중 선택**으로 강제해 도메인 분열을 제거한다.

**통제 어휘 (초안, 웹 일반 + ISO 25023 친화)** — `app/core/taxonomy.py`(신규)에 단일 정의:
```
인증·계정 / 회원관리 / 게시판·콘텐츠 / 검색 / 네비게이션 / 파일·미디어 /
폼·입력검증 / 결제·주문 / 알림·메시지 / 관리자 / 정보표시 / 설정·환경 / 기타
```
- 영/한 혼용 금지(한글 고정) → 분열 차단.
- "분류 불가"는 `기타`로만 흡수(임의 신조어 금지).

**적용 지점**:
1. `prompts/dom_spec.md`·`tc_design.md`·`feature_consolidate.md` [System]에 목록 주입 + "이 목록 외 대분류 생성 금지" 규칙.
2. `stage1_ingest.py`에 `_coerce_major(name) -> str` 후처리 — LLM이 목록 밖 값을 내면 동의어 매핑표로 강제 보정(`"authentication"/"user management"/"account" → "인증·계정"`).
3. C3 dedup 키가 통제된 major 위에서 동작 → 동일 로그인이 실제로 병합됨.

**meta.json 기록**: `taxonomy_version`, `coerced_major_count`(보정 건수), `unknown_major_samples[]`.

**검증 지표**: 대분류 distinct 개수(현재 다수 → 13 이하), 인증 도메인 단일 카테고리화 여부.

**안전장치**: 매핑표는 보수적으로(확실한 동의어만). 매칭 실패 시 `기타`로 보내고 샘플을 로깅해 어휘 보강 근거로 사용.

---

### D53 — 기능 확정 게이트 + 도메인 TC 예산 (C4 해소) · 3순위

**아이디어**: Stage 1b(통합) 완료 후 **Stage 2 진입 전**, 도메인별 집계를 보여주고 사용자가 **선택적으로** 조절·확정한다.

**UI (신규 다이얼로그 `app/ui/feature_gate.py`)**:
- 대분류(D52 통제 어휘)별 집계 테이블: `도메인 | leaf 수 | 예상 TC 수 | 전체 대비 %`.
- 비대 도메인 1클릭 펼침 → 개별 leaf 체크 해제(제외)·병합.
- **도메인 TC 예산** (정 박사 안): 도메인별 "최대 비중 %" 또는 "최대 TC 수" 상한 슬라이더. Stage 2는 예산 내에서 대표 leaf 우선 설계.
- 기본값은 무조작 통과(자동 파이프라인 유지) — **필수 아님, 의심 시 확인용**.

**오케스트레이션 변화** (`orchestrator.py`):
- `run_stage1` 반환 후 `run_stage2` 직결 대신, UI가 게이트를 띄울 수 있도록 **leaves 확정 hook** 추가.
- `run_stage2(leaf_overrides=None, domain_budget=None)` — 제외 leaf 반영 + 예산 기반 TC 수 조정.

**meta.json 기록**: `feature_gate = {shown, excluded_leaf_ids[], domain_budget{}, leaves_before, leaves_after}` (재현성·추적성).

**검증 지표**: 게이트 사용 시 도메인 분포가 사용자 의도대로 수렴하는지, 미사용 시 기존과 동일하게 동작하는지(회귀 없음).

**안전장치**: 게이트 스킵 = 현행 동작 그대로. 예산 기능은 후속(D53b)으로 분리 가능 — 1차는 "집계 표시 + leaf 제외"만으로도 가치.

---

## 4. 구현 순서 & 의존성

```
D51 (전역 dedup)  ──┐  입력 정화
D52 (taxonomy)    ──┴─→  D53 (게이트)  ─→  깨끗한 집계/예산
   ↑ 독립 가능        ↑ D52의 통제 어휘에 의존(집계 축)
```

1. **D51 먼저** — 근본 원인 직격, 효과 즉시 정량 검증, 후속 전제.
2. **D52** — 난이도 최저, 분열 즉시 완화, D53 집계 축 제공.
3. **D53** — D52 위에서 도메인 집계가 의미 있어짐.

각 단계는 **독립 커밋 + 재실행 검증**(인증 도메인 비율 추이) 후 다음 단계 착수.

---

## 5. 회귀·안전 원칙 (전 결정 공통)

- **손실 0**: dedup·통합은 *이동/병합*이지 *삭제*가 아니다(전역→`__global__`, 동의어→canonical). 게이트 제외만 명시적 삭제이며 meta에 기록.
- **옵트아웃 가능**: `dedup_global_components`, 게이트 스킵, 예산 미설정 시 모두 현행 동작 보존.
- **결정성 우선**: D51 전역 탐지·D52 보정은 규칙 기반(LLM 불필요) → 재현 가능.
- **추적성**: 모든 변경은 meta.json에 리포트 필드로 남겨 재현/감사 가능(D38 stateless 유지).

---

## 6. 미해결 질문 (구현 전 확인 필요)

- **Q1** `GLOBAL_RATIO` 기본 0.5가 적정한가? (헤더는 거의 100%, 일부 섹션 네비는 30~50%) — 1차는 0.5로 두고 실측 후 튜닝.
- **Q2** taxonomy 13종으로 충분한가, 시험 대상 제품군별 확장 필요한가? — `taxonomy.py` 버전 관리로 대응.
- **Q3** 도메인 예산(D53)을 1차 범위에 포함할지, "집계+제외"만 먼저 낼지 — 사용자 결정 사항.

---

## 7. MANUAL 동기화

D53 게이트 UI는 사용자 진입점 변경이므로, 구현 시 `MANUAL.md`에 "Stage 1 후 기능 확정 단계" 사용법·결과 해석을 함께 갱신한다(메모리 규칙 manual_sync).

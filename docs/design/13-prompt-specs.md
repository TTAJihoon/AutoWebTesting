---
status: stable
lastUpdated: 2026-05-15
related:
  - 12-gpt-web-workflow.md
  - 06-risk-policy.md
---

# 프롬프트 명세

`prompts/` 폴더의 프롬프트 파일은 GPT Web Import Mode와 API Mode에서 공통으로 사용한다. API Mode도 내부적으로 동일한 task 정의와 출력 스키마를 사용한다.

## 1. 공통 규칙

모든 프롬프트는 다음을 요구해야 한다.

- 유효한 JSON만 출력
- Markdown 코드 블록 사용 금지
- JSON 외 설명 텍스트 금지
- 임의 계정/비밀번호 생성 금지
- 임의 Playwright 코드 생성 금지
- 리스크 플래그 없이 위험 행동 제안 금지

## 2. Prompt 1 — Testcase Generation

파일: `prompts/testcase-generation.prompt.md`

**입력**

- 고정 양식 기능목록 (대분류/중분류/소분류/기능설명)
- 제품 매뉴얼 텍스트
- 생성 수준 (`STANDARD` 또는 `DETAILED`)

**출력**

- `schemas/testcase.schema.json` 형식의 JSON

**주요 task**

- 기능 행을 대분류/중분류/소분류로 분류
- TC_ID 부여 (`TC_{소분류번호}-{순번}`)
- 시나리오, 사전조건, 기대결과 작성
- 자동화 대상 여부 표시
- 리스크 수준과 플래그 표시
- 불확실한 항목은 `reviewStatus = DRAFT`로 표시

---

## 3. Prompt 2 — DOM Mapping (실행계획 생성)

파일: `prompts/dom-mapping.prompt.md`

**입력**

- 승인된 테스트케이스 JSON (`reviewStatus = APPROVED`만)
- DOM Summary JSON (여러 PageState)
- 테스트 데이터 변수 목록 (이름과 타입만, `secret` 값은 제외)
- 리스크 정책 요약

**출력**

- `schemas/execution-plan.schema.json` 형식의 JSON

**주요 task**

- 각 step에 사용할 elementId 선택
- 허용 action 이름만 사용
- 실제 값 대신 `valueSource`(변수명) 참조
- 불확실한 매핑은 `planStatus = NEEDS_MAPPING_REVIEW`
- 자동화 불가 케이스는 `planStatus = NOT_AUTOMATABLE`
- 위험 행동은 적절한 리스크 플래그 첨부
- assertion step 최소 1개 포함

---

## 4. Prompt 3 — Failure Analysis

파일: `prompts/failure-analysis.prompt.md`

**입력**

- failure-package.json (실패 패키지)

**출력**

- `schemas/failure-analysis.schema.json` 형식의 JSON

**주요 task**

- 실패를 사람이 이해할 수 있는 한국어로 요약
- 실패 원인을 enum (`likelyCauseCategory`)으로 분류
- 사용자가 검토해야 할 항목 제안
- raw P/F 데이터를 변경하지 않음
- `finalResult`로 `F`, `MANUAL_REVIEW`, `NOT_A_PRODUCT_FAILURE` 중 하나 지정

---

## 5. 프롬프트 작성 가이드

### 5.1 한글 vs 영어

프롬프트 본문은 **한글**로 작성한다. 단, 스키마 필드명, enum 값, 식별자 형식은 **영어**를 유지한다.

```text
좋은 예:
- "각 테스트케이스에는 reviewStatus 필드를 반드시 포함하세요."
- "허용 액션은 click, fill, selectOption 등입니다."

피해야 할 예:
- "각 testcase needs a review_status field."
- "허용 액션은 클릭, 채우기, 선택옵션 등입니다."
```

### 5.2 출력 형식 강조

프롬프트 마지막에 출력 형식을 다시 강조한다.

```text
출력은 반드시 다음 형식의 JSON만 출력합니다.
- 코드 펜스(```) 사용 금지
- 설명 텍스트 추가 금지
- 첫 글자는 { 또는 [

스키마: { schemaVersion: "...", ... }
```

### 5.3 예시 포함

프롬프트에 짧은 입력/출력 예시를 1~2개 포함하면 출력 안정성이 높아진다.

### 5.4 리스크 지침

리스크 관련 프롬프트 섹션은 다음을 포함한다.

```text
다음 행동은 PROHIBITED로 분류하고 실행 step에 포함하지 마세요.
- 실제 결제 확정
- 운영 데이터 영구 삭제
- 외부 SMS/이메일/푸시 실제 발송
- 권한/보안 설정 변경

다음 행동은 HIGH로 분류하고 적절한 riskFlags를 첨부하세요.
- 삭제 (자동 생성 데이터만 허용)
- 외부 시스템 제출
- 권한 변경
```

## 6. 버전 관리

프롬프트 파일 상단에 버전을 표시한다.

```markdown
# Testcase Generation Prompt

version: 0.3
schemaVersion: 0.3
lastUpdated: 2026-05-15
```

프롬프트 버전과 스키마 버전이 호환되지 않으면 앱은 경고를 표시한다.

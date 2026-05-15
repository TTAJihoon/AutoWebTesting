---
status: stable
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 09-run-result-failure.md
---

# Assertion 정책

## 1. 기본 원칙

자연어 기대결과만으로 P/F를 판단하지 않는다.

자동 P/F 판정은 **구조화된 assertion**을 기준으로 한다.

## 2. Assertion 분류

| 대분류 | Assertion Type | 설명 |
|---|---|---|
| 텍스트 검증 | `assertTextVisible` | 특정 텍스트가 보이는지 확인 |
| 텍스트 검증 | `assertTextNotVisible` | 특정 텍스트가 보이지 않는지 확인 |
| 요소 검증 | `assertElementVisible` | 특정 요소가 보이는지 확인 |
| 요소 검증 | `assertElementNotVisible` | 특정 요소가 보이지 않는지 확인 |
| 값 검증 | `assertValueEquals` | 입력값 또는 표시값이 기대값과 같은지 확인 |
| 값 검증 | `assertValueContains` | 값이 특정 문자열을 포함하는지 확인 |
| URL 검증 | `assertUrlContains` | URL에 특정 경로/문자열 포함 여부 확인 |
| 페이지 검증 | `assertPageTitleContains` | 페이지 제목 확인 |
| 테이블 검증 | `assertRowContains` | 목록/테이블 행에 특정 값이 포함되는지 확인 |
| 테이블 검증 | `assertRowNotContains` | 목록/테이블 행에 특정 값이 사라졌는지 확인 |
| 테이블 검증 | `assertCellEquals` | 특정 행/열 값이 기대값과 같은지 확인 |
| 메시지 검증 | `assertToastVisible` | 저장/수정/삭제 성공 메시지 확인 |
| 메시지 검증 | `assertAlertText` | alert/dialog 문구 확인 |
| 상태 검증 | `assertEnabled` | 버튼/입력 요소 활성화 여부 확인 |
| 상태 검증 | `assertDisabled` | 버튼/입력 요소 비활성화 여부 확인 |
| 개수 검증 | `assertCountEquals` | 검색 결과나 목록 개수 확인 |
| 개수 검증 | `assertCountGreaterThan` | 행 개수가 특정 수보다 큰지 확인 |
| 파일 검증 | `assertDownloadStarted` | 다운로드 발생 여부 확인 |

## 3. Assertion 필수 여부

실행 가능한 테스트케이스는 **최소 1개 이상의 assertion**을 가져야 한다.

단, 로그인, 메뉴 이동, 사전 준비 단계 같은 보조 흐름은 assertion 없이도 step으로 포함될 수 있다.

assertion이 하나도 없는 TC는 자동 P/F 판정을 할 수 없으므로 `executionStatus = COMPLETED`가 되어도 `testResult = N/A`로 처리한다.

## 4. Assertion 예시

### 4.1 텍스트 검증

```json
{
  "stepId": "ASSERT_001",
  "stepType": "ASSERTION",
  "pageStateId": "PAGE_001",
  "assertion": "assertTextVisible",
  "expectedText": "저장되었습니다",
  "description": "저장 성공 메시지 표시 확인"
}
```

### 4.2 테이블 행 검증

```json
{
  "stepId": "ASSERT_002",
  "stepType": "ASSERTION",
  "pageStateId": "PAGE_001",
  "assertion": "assertRowContains",
  "tableId": "TABLE_USERS",
  "expectedValueSource": "USER_NAME",
  "description": "사용자 목록 테이블에 등록한 사용자명이 표시되는지 확인"
}
```

### 4.3 값 검증

```json
{
  "stepId": "ASSERT_003",
  "stepType": "ASSERTION",
  "pageStateId": "PAGE_004",
  "assertion": "assertValueEquals",
  "elementId": "PAGE_004.el_0010",
  "expectedValueSource": "USER_NAME",
  "description": "수정 화면 사용자명 입력값이 등록값과 일치하는지 확인"
}
```

### 4.4 URL 검증

```json
{
  "stepId": "ASSERT_004",
  "stepType": "ASSERTION",
  "assertion": "assertUrlContains",
  "expectedSubstring": "/users/",
  "description": "URL이 사용자 상세 경로로 이동했는지 확인"
}
```

## 5. Assertion 실패와 실행 실패 구분

| 상황 | executionStatus | testResult | 의미 |
|---|---|---|---|
| 모든 step과 assertion 성공 | `COMPLETED` | `P` | 테스트 통과 |
| step은 성공했지만 assertion 실패 | `COMPLETED` | `F` | 제품 기능 실패 가능성 |
| 요소를 찾지 못함 | `MAPPING_FAILED` | 없음 | 자동화 매핑 실패 |
| Playwright 명령 실패 | `SCRIPT_FAILED` | 없음 | 스크립트 실행 실패 |
| 사전조건 미충족 | `BLOCKED` | 없음 | 테스트 수행 불가 |
| 위험 정책 차단 | `SKIPPED_RISK` | 없음 | 안전상 실행 제외 |

자세한 ExecutionStatus 목록은 [`09-run-result-failure.md`](09-run-result-failure.md) 참고.

## 6. Assertion 결과와 testResult

| Assertion 결과 | executionStatus | testResult |
|---|---|---|
| 모든 assertion 성공 | `COMPLETED` | `P` |
| 하나 이상의 assertion 실패 | `COMPLETED` | `F` |
| assertion 수행 전 실행 실패 | 실패 유형에 따름 | 없음 |

`testResult`는 `executionStatus = COMPLETED`일 때만 `P` 또는 `F`가 될 수 있다.

## 7. Assertion 작성 가이드

- 기대 텍스트는 가능한 한 짧고 유일한 표현을 선택한다.
- 다국어/번역 변경 가능성이 있는 텍스트는 피하거나 부분 매칭을 사용한다.
- 표시 값과 비교할 때는 `expectedValueSource`로 변수 참조를 우선 사용한다.
- 동적 값(타임스탬프, 자동생성 ID)은 정확 일치(`assertValueEquals`)보다 포함(`assertValueContains`)을 권장한다.
- 토스트 메시지처럼 빠르게 사라지는 요소는 `assertToastVisible`를 사용하고 timeout을 짧게 설정한다.

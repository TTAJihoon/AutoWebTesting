---
status: stable
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 09-run-result-failure.md
---

# 08. Assertion 정책

## 목적

Assertion은 자동 P/F 판단의 기준이다.

자연어 기대결과는 사람이 이해하기 위한 설명이고, 실제 자동 판정은 구조화된 assertion으로 수행한다.

## Assertion을 사용하는 이유

1. LLM에게 더 명확한 실행 목표를 제공한다.
2. 앱이 자동으로 P/F를 판단할 수 있다.
3. 실패 보고서에 명확한 근거를 남길 수 있다.

## Assertion 목록

| assertion | 설명 |
|---|---|
| `assertTextVisible` | 특정 텍스트가 보이는지 확인 |
| `assertTextNotVisible` | 특정 텍스트가 보이지 않는지 확인 |
| `assertElementVisible` | 특정 요소가 보이는지 확인 |
| `assertElementNotVisible` | 특정 요소가 보이지 않는지 확인 |
| `assertValueEquals` | 입력값 또는 표시값이 기대값과 같은지 확인 |
| `assertValueContains` | 값이 특정 문자열을 포함하는지 확인 |
| `assertUrlContains` | 현재 URL에 특정 문자열 포함 여부 확인 |
| `assertPageTitleContains` | 페이지 제목 확인 |
| `assertToastVisible` | 토스트 메시지 표시 확인 |
| `assertAlertText` | alert/dialog 문구 확인 |
| `assertRowContains` | 테이블에 특정 값을 포함한 행이 있는지 확인 |
| `assertRowNotContains` | 테이블에 특정 값을 포함한 행이 없는지 확인 |
| `assertCellEquals` | 특정 행/열의 셀 값이 기대값과 같은지 확인 |
| `assertCountEquals` | 행 개수 또는 요소 개수 확인 |
| `assertDownloadStarted` | 다운로드 발생 여부 확인 |

## Assertion 결과와 testResult

| Assertion 결과 | executionStatus | testResult |
|---|---|---|
| 모든 assertion 성공 | `COMPLETED` | `P` |
| 하나 이상의 assertion 실패 | `COMPLETED` | `F` |
| assertion 수행 전 실행 실패 | 실패 유형에 따름 | 없음 |

## 핵심 원칙

`testResult`는 `executionStatus = COMPLETED`인 경우에만 `P` 또는 `F`를 가진다.

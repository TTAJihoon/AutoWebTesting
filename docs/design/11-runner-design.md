---
status: draft
lastUpdated: 2026-05-15
related:
  - 04-page-state-dom.md
  - 05-execution-plan.md
  - 06-risk-policy.md
---

# 11. Playwright Runner 설계

## 목적

Runner는 승인된 ExecutionPlan을 Playwright 명령으로 실행하고, 결과와 증적을 생성한다.

Runner는 AI가 만든 임의 코드를 실행하지 않는다.  
오직 허용된 action과 검증된 elementId만 실행한다.

## 실행 흐름

```text
1. ExecutionPlan 로드
2. 스키마 검증
3. planStatus 확인
4. testDataSnapshot 생성
5. startPageState 확인
6. step 순차 실행
7. 각 step 실행 전 riskCheck
8. elementId resolve
9. Playwright action 실행
10. expectedTransition 확인
11. assertion 수행
12. 실패 시 screenshot/log 저장
13. RunResult 생성
14. 필요 시 FailurePackage 생성
15. cleanupPlan 처리
```

## element resolve

```text
1. 현재 PageState 확인
2. ElementRegistry에서 elementId 조회
3. selectorCandidates를 priority 순서로 시도
4. visible/enabled 조건 확인
5. stableHints로 후보 재필터링
6. 확정 실패 시 MAPPING_FAILED
```

## step 실행 전 검사

- 현재 화면이 `step.pageStateId`와 일치하는지 확인
- step action이 허용 목록에 있는지 확인
- riskCheck 결과가 실행 가능한지 확인
- valueSource가 TestDataProfile에 존재하는지 확인
- elementId가 ElementRegistry에 존재하는지 확인

## 실패 처리

| 실패 상황 | executionStatus |
|---|---|
| elementId resolve 실패 | `MAPPING_FAILED` |
| 현재 화면이 다름 | `PAGE_STATE_MISMATCH` |
| 기대 전환 실패 | `NAVIGATION_FAILED` |
| dialog 처리 실패 | `DIALOG_UNHANDLED` |
| Playwright 예외 | `SCRIPT_FAILED` |
| 리스크 차단 | `SKIPPED_RISK` |
| 사전조건 미충족 | `BLOCKED` |

## 증적

Runner는 다음 증적을 저장한다.

- 실패 스크린샷
- 선택적 step 스크린샷
- console error
- network error
- current URL
- visible text summary
- step log
- selector resolve attempts

## 원칙

실행은 가능한 한 selectorCandidates 기반으로 수행한다.  
이미지 기반 좌표 클릭은 최후 수단으로만 허용한다.

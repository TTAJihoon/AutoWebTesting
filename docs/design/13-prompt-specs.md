---
status: stable
lastUpdated: 2026-05-15
related:
  - 02-ai-exploration.md
  - 05-execution-plan.md
  - 12-gpt-web-workflow.md
---

# 13. 프롬프트 명세

## 공통 규칙

모든 프롬프트는 다음을 요구해야 한다.

- 유효한 JSON만 출력
- Markdown code block 금지
- JSON 외 설명 금지
- 임의 Playwright 코드 생성 금지
- secret 값 추측 금지
- 위험 행동은 riskFlag 표시
- 불확실한 경우 review 필요 상태로 표시

## 제품 형상 기반 TC 생성

테스트케이스 생성은 기능목록/매뉴얼만 사용하지 않는다.

입력에는 다음이 포함될 수 있다.

- 기능목록 Excel
- 제품 매뉴얼
- 대상 URL
- PageState 목록
- DOM Summary
- Form 구조
- Table 구조
- Button/Link 후보
- PageFlow 후보
- CandidateFeature
- CandidateCrudFlow
- Risk Policy
- TestDataProfile 변수 목록

## 탐색 판단 프롬프트

AI는 Observation을 보고 다음을 판단한다.

- 현재 화면의 의미
- 기능 후보
- CRUD 흐름 후보
- 다음 탐색 action
- 예상 화면 전환
- 리스크 수준
- 사람 검토 필요 여부

## 실행계획 생성 프롬프트

AI는 승인된 TestCase와 탐색 결과를 바탕으로 ExecutionPlan을 생성한다.

조건:

- 허용된 action만 사용
- elementId만 참조
- 실제 secret 값 사용 금지
- valueSource 사용
- assertion 포함
- riskCheck 포함
- 불확실하면 `NEEDS_MAPPING_REVIEW` 또는 `MANUAL_REQUIRED`

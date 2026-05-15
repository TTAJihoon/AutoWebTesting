# ADR-003: 리스크 정책은 3단계로 적용한다

## 상태

- status: accepted
- date: 2026-05-15

## 결정

리스크 정책은 다음 세 단계에서 적용한다.

1. 생성 전 지침
2. 생성 후 검증
3. 실행 직전 차단

## 이유

LLM이 위험 TC 생성을 줄이도록 유도하는 것만으로는 부족하다. 생성 결과에서 riskFlag 누락이 있을 수 있고, 실제 화면에서는 예상하지 못한 위험 버튼이나 confirm dialog가 나타날 수 있다.

## 영향

- `design/06-risk-policy.md`
- `design/05-execution-plan.md`
- `design/11-runner-design.md`

# ADR-004: 자동 생성 데이터만 cleanup 대상으로 삼는다

## 상태

- status: accepted
- date: 2026-05-15

## 결정

AutoWebTesting이 생성하고 추적한 데이터만 자동 cleanup 대상으로 삼는다. 기존 데이터 삭제는 기본적으로 차단한다.

## 이유

CRUD 자동화에서 Delete를 검증하려면 데이터 삭제가 필요할 수 있다. 그러나 기존 데이터를 삭제하면 업무 피해가 발생할 수 있다. Create 단계에서 생성한 데이터를 추적하고 해당 데이터만 cleanup 대상으로 삼는 것이 가장 안전하다.

## 영향

- `design/07-test-data.md`
- `design/06-risk-policy.md`
- `design/05-execution-plan.md`

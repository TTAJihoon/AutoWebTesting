# ADR-004: 자동 생성한 테스트 데이터만 cleanup 대상으로 삼는다

## 상태

- status: accepted
- date: 2026-05-15

## 배경

자동화 테스트는 데이터를 반복 생성하므로 정리 전략이 필요하다. 그러나 기존 운영 데이터를 잘못 삭제하면 사고로 이어진다.

## 선택지

### 선택지 A — Cleanup 없음

테스트 데이터를 그대로 남긴다. 데이터 누적 문제가 발생한다.

### 선택지 B — 모든 매칭 데이터 삭제

이름이나 검색 조건이 일치하는 모든 데이터를 삭제한다. 운영 데이터 손상 위험이 매우 크다.

### 선택지 C — 자동 생성 데이터만 cleanup

`CreatedDataRegistry`에 등록된 데이터, 즉 AutoWebTesting이 직접 생성하고 추적한 데이터만 cleanup 대상으로 한다.

## 결정

선택지 C를 채택한다.

## 이유

기존 운영 데이터 손상은 가장 큰 사고 유형이다. cleanup은 안전한 범위에서만 수행해야 한다.

기본 정책은 `AUTO_CLEANUP_APPROVAL_REQUIRED`로 한다. 즉, 자동 생성 데이터에 한해 cleanup 후보로 등록하고 사용자 승인 후 삭제한다.

테스트 데이터는 다음 변수 유형으로 구분한다.

- `secret`: ID/비밀번호/토큰 등 민감정보. LLM 전달 금지.
- `testData`: 일반 입력값. LLM 전달 가능.
- `generated`: 실행 시점에 생성하는 고유값(`AUTO_USER_${timestamp}` 등). cleanup의 기준 키가 된다.
- `file`: 업로드용 파일 경로.

`generated` 변수로 만든 데이터는 `CreatedDataRegistry`에 등록되어 cleanup 식별 키로 활용된다.

## 영향

- `design/07-test-data.md`
- `design/05-execution-plan.md`

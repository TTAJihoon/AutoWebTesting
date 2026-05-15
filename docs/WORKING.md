# AutoWebTesting 현재 작업 범위

이 문서는 현재 대화 또는 현재 개발 작업에서 참조해야 할 문서와 수정 범위를 정의한다.

## 현재 작업 목표

AI 탐색 기반 AutoWebTesting 설계를 실제 구현 가능한 JSON Schema, TypeScript 타입, IPC 계약, Runner 구조로 구체화한다.

## 현재 작업 대상 문서

- `design/03-data-schema-overview.md`
- `design/05-execution-plan.md`
- `design/10-ipc-contract.md`
- `design/11-runner-design.md`
- `design/15-phase-roadmap.md`

## 참조할 수 있는 문서

- `design/02-ai-exploration.md`
- `design/04-page-state-dom.md`
- `design/06-risk-policy.md`
- `design/07-test-data.md`
- `design/08-assertion-policy.md`
- `design/09-run-result-failure.md`

## 이번 작업에서 수정하지 않을 문서

- `design/00-product-overview.md`
- `design/01-mvp-scope.md`
- `design/12-gpt-web-workflow.md`
- `design/13-prompt-specs.md`
- `design/14-storage-structure.md`

## 현재 확정된 방향

1. MVP는 URL 기반 AI 탐색형 CRUD 테스트 자동화 도구를 목표로 한다.
2. GPT Web Import Mode는 비용 절감을 위한 초기 운용 방식이다.
3. 궁극적 방향은 API Mode 또는 내부 AI 서버 기반 탐색 루프다.
4. 테스트케이스 생성에는 기능목록/매뉴얼뿐 아니라 실제 웹 형상 정보가 포함된다.
5. Observation은 DOM Summary를 우선 사용하고, 필요한 경우 masked screenshot을 보강한다.
6. 실행은 이미지 좌표가 아니라 ElementRegistry와 selectorCandidates 기반으로 수행한다.
7. 위험 행동은 생성 전 지침, 생성 후 검증, 실행 직전 차단의 3단계로 통제한다.
8. Delete는 AutoWebTesting이 생성한 데이터에 대해서만 제한적으로 허용한다.
9. SMS/메일/푸시 등 외부 발송은 HIGH로 보고 명시 승인 후 실행한다.
10. P/F는 `executionStatus = COMPLETED`인 경우에만 부여한다.

## 다음 작업

1. JSON Schema 파일 목록과 필수 필드 확정
2. TypeScript 타입 구조 작성
3. IPC 계약 재정리
4. Runner 실행 흐름 작성
5. 샘플 JSON 세트 작성

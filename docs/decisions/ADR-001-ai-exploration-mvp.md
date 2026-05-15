# ADR-001: MVP를 AI 탐색 기반 CRUD 테스트 자동화로 정의한다

## 상태

- status: accepted
- date: 2026-05-15

## 배경

초기 설계에서는 사용자가 주요 화면을 수동으로 캡처하고, GPT가 실행계획을 생성하는 방식이 검토되었다. 그러나 이 방식은 기존 자동화 시험 도구에 GPT 보조를 붙인 수준에 머물 가능성이 있다.

AutoWebTesting의 목표는 URL과 시험 의도만 입력하면 AI가 웹 제품을 탐색하고, 주요 기능과 CRUD 흐름을 발견하며, 테스트케이스와 실행계획 후보를 생성하는 것이다.

## 선택지

### 선택지 A — 수동 PageState 캡처 기반 MVP

사용자가 각 화면으로 이동하고 캡처 버튼을 눌러 PageState를 만든다.

### 선택지 B — AI 탐색 기반 MVP

AI가 URL을 기준으로 화면을 관찰하고, PageState/PageFlow/TestCase/ExecutionPlan 후보를 생성한다.

## 결정

선택지 B를 채택한다.

## 이유

AutoWebTesting의 차별점은 기존 자동화 도구보다 높은 수준의 AI 탐색과 자동 테스트 설계에 있다. 구현 난이도는 높아지지만, 제품 가치와 목표에 더 부합한다.

## 영향

- `design/01-mvp-scope.md`
- `design/02-ai-exploration.md`
- `design/04-page-state-dom.md`
- `design/05-execution-plan.md`

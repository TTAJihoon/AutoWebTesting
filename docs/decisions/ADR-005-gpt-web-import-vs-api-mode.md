# ADR-005: GPT Web Import는 초기 운용 방식, API Mode는 궁극 방향이다

## 상태

- status: accepted
- date: 2026-05-15

## 배경

AutoWebTesting은 LLM을 활용해 테스트케이스, 실행계획, 실패분석을 생성한다. LLM 연동 방식은 두 가지로 정리된다.

- GPT Web Import Mode: 사용자가 GPT 웹페이지에서 직접 JSON을 만들어 앱에 업로드
- API Mode: 앱이 LLM API를 직접 호출

## 선택지

### 선택지 A — GPT Web Import만 사용

비용과 보안 부담이 적지만 AI 탐색 루프 자동화가 어렵다.

### 선택지 B — API Mode를 처음부터 기본으로 사용

탐색 루프 자동화에 유리하지만 API 키 관리, 비용, 보안 도입 부담이 크다.

### 선택지 C — GPT Web Import를 초기, API Mode를 후속

초기에는 GPT Web Import로 운용을 시작하고, AI 탐색 루프가 본격화되는 시점에 API Mode를 도입한다.

## 결정

선택지 C를 채택한다.

## 이유

조직마다 외부 API 도입 부담은 다르고, 초기에는 GPT Web Import로도 충분히 가치를 검증할 수 있다.

다만 제품의 궁극 방향은 AI 탐색 루프 자동화이며, 이는 GPT Web Import만으로는 사용자 조작 부담이 너무 크다. 따라서 API Mode는 단순 부가기능이 아니라 핵심 구현 수단으로 본다.

GPT Web Import Mode와 API Mode는 입력 방식만 다르고, 다음은 동일하게 유지한다.

- JSON 스키마 계약
- 사람 검토 절차
- 리스크 정책
- 실행 엔진

API 어댑터는 GPT Web Import와 같은 출력을 만들도록 설계하여 둘 사이 전환 비용을 최소화한다.

## 영향

- `design/01-mvp-scope.md`
- `design/02-ai-exploration.md`
- `design/12-gpt-web-workflow.md`
- `design/13-prompt-specs.md`

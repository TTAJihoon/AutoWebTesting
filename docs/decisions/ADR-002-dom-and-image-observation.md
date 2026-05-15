# ADR-002: Observation은 DOM 우선 + 선택적 이미지 보강으로 한다

## 상태

- status: accepted
- date: 2026-05-15

## 배경

AI 에이전트가 웹 화면을 이해할 때 스크린샷은 유용하다. 그러나 모든 화면에서 이미지를 LLM에 전달하면 비용, 속도, 보안, 재현성 문제가 발생한다.

## 결정

기본 판단은 DOM Summary로 수행하고, 필요한 경우 masked screenshot을 추가한다.

## 이유

텍스트 DOM은 구조화와 재현성에 강하고, 이미지는 화면 이해 보조에 강하다. 두 방식을 역할에 따라 나누는 것이 가장 안정적이다.

## 영향

- `design/02-ai-exploration.md`
- `design/04-page-state-dom.md`
- `design/11-runner-design.md`

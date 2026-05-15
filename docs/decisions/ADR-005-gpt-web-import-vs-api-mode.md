# ADR-005: GPT Web Import는 비용 절감형 초기 방식, API Mode는 궁극 방향이다

## 상태

- status: accepted
- date: 2026-05-15

## 배경

AI 탐색 루프는 화면 관찰과 AI 판단이 반복되어야 한다. GPT Web Import Mode만으로는 사용자가 매번 복사/붙여넣기를 해야 하므로 완전한 탐색 자동화 경험을 만들기 어렵다.

## 결정

GPT Web Import Mode는 초기 개발과 비용 절감을 위한 운용 방식으로 사용한다. 궁극적인 제품 방향은 API Mode 또는 내부 AI 서버 기반 탐색 루프다.

## 이유

구독형 LLM을 활용하면 초기 비용을 줄일 수 있다. 그러나 URL 기반 자동 탐색을 제품 핵심 경험으로 만들려면 LLM Adapter 기반 자동 호출 구조가 필요하다.

## 영향

- `design/02-ai-exploration.md`
- `design/12-gpt-web-workflow.md`
- `design/13-prompt-specs.md`

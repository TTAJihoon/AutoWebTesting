---
status: stable
lastUpdated: 2026-05-15
related:
  - 13-prompt-specs.md
  - ADR-005-gpt-web-import-vs-api-mode.md
---

# 12. GPT Web Import Workflow

## 목적

GPT Web Import Mode는 초기 개발 및 검증 단계에서 LLM API 비용을 줄이고, 구독형 LLM 웹페이지를 활용하기 위한 운용 방식이다.

궁극적 목표는 API Mode 또는 내부 AI 서버 기반 탐색 루프지만, GPT Web Import Mode는 스키마와 프롬프트를 검증하는 전환 단계로 사용한다.

## 기본 흐름

```text
앱이 입력 JSON 패키지를 생성
→ 사용자가 GPT 웹에 붙여넣음
→ GPT가 JSON 출력
→ 사용자가 JSON 저장
→ 앱에 업로드
→ 앱이 스키마 검증
→ 검토/실행 단계로 진행
```

## 사용 가능한 작업

- 테스트케이스 후보 생성
- 탐색 후보 action 생성
- 실행계획 후보 생성
- 실패분석 생성

## JSON 출력 규칙

GPT 출력은 유효한 JSON만 포함해야 한다.

금지:

- Markdown code fence
- JSON 외 설명
- 예시 뒤 추가 문장
- 임의 Playwright code

## 안전한 보정

앱은 다음 보정을 허용한다.

- Markdown 코드펜스 제거
- 첫 번째 `{` 또는 `[` 앞의 텍스트 제거
- 마지막 `}` 또는 `]` 뒤의 텍스트 제거
- UTF-8 BOM 제거

단, 필드 값 자체를 조용히 변경해서는 안 된다.

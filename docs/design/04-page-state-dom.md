---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 02-ai-exploration.md
  - 05-execution-plan.md
---

# 04. PageState / DOM Summary / ElementRegistry 설계

## PageState

`PageState`는 테스트 자동화에서 구분해야 하는 하나의 화면 상태다.

URL이 같아도 다음 상태는 서로 다른 PageState가 될 수 있다.

- 검색 전 목록
- 검색 후 목록
- 등록 모달이 열린 상태
- 삭제 확인 모달이 열린 상태
- 권한 없음 메시지가 표시된 상태

## PageState 예시

```json
{
  "pageStateId": "PAGE_001",
  "name": "사용자 목록 화면",
  "description": "사용자 검색, 등록 버튼, 사용자 목록 테이블이 표시되는 화면",
  "url": "https://example.com/users",
  "urlPattern": "/users",
  "title": "사용자 관리",
  "stateType": "PAGE",
  "identityHints": {
    "requiredTexts": ["사용자 목록", "검색", "등록"],
    "requiredElementIds": ["PAGE_001.el_0001", "PAGE_001.el_0002"],
    "optionalTexts": ["전체", "사용자명"]
  },
  "domSummaryId": "DOM_001",
  "elementRegistryId": "REG_001"
}
```

## stateType

| 값 | 설명 |
|---|---|
| `PAGE` | 일반 페이지 화면 |
| `MODAL` | HTML 기반 모달 |
| `POPUP` | 새 브라우저 창 또는 탭 |
| `DIALOG` | alert, confirm, prompt |
| `PARTIAL` | 페이지 일부 영역만 변경된 상태 |

## DOM Summary

DOM Summary는 GPT/LLM에게 전달할 화면 요소 요약본이다.

실제 Playwright selector는 포함하지 않는다.

```json
{
  "schemaVersion": "0.3",
  "domSummaryId": "DOM_001",
  "pageStateId": "PAGE_001",
  "url": "https://example.com/users",
  "title": "사용자 관리",
  "elements": [
    {
      "elementId": "PAGE_001.el_0001",
      "role": "button",
      "tag": "button",
      "label": "등록",
      "text": "등록",
      "visible": true,
      "enabled": true,
      "nearbyText": "사용자 목록",
      "region": "toolbar"
    }
  ],
  "visibleTexts": ["사용자 목록", "검색", "등록"],
  "tables": [
    {
      "tableId": "TABLE_USERS",
      "label": "사용자 목록 테이블",
      "elementId": "PAGE_001.el_0020",
      "columns": ["사용자명", "아이디", "상태", "관리"]
    }
  ]
}
```

## elementId 형식

다중 화면을 지원하기 위해 elementId는 PageState를 포함한다.

```text
PAGE_001.el_0001
PAGE_002.el_0001
```

## ElementRegistry

ElementRegistry는 앱 내부에서만 사용하는 실행용 요소 매핑 정보다.

```json
{
  "schemaVersion": "0.3",
  "elementRegistryId": "REG_001",
  "pageStateId": "PAGE_001",
  "items": [
    {
      "elementId": "PAGE_001.el_0001",
      "selectorCandidates": [
        {
          "type": "role",
          "value": "button[name='등록']",
          "priority": 1,
          "confidence": 0.95
        },
        {
          "type": "text",
          "value": "button:has-text('등록')",
          "priority": 2,
          "confidence": 0.85
        }
      ],
      "stableHints": {
        "role": "button",
        "label": "등록",
        "text": "등록",
        "nearbyText": "사용자 목록",
        "region": "toolbar"
      }
    }
  ]
}
```

## selector 후보 우선순위

| 우선순위 | selector 유형 |
|---:|---|
| 1 | `testId` |
| 2 | `role` |
| 3 | `label` |
| 4 | `placeholder` |
| 5 | `text` |
| 6 | `css` |
| 7 | `xpath` |

## 실행 시 element resolve 방식

```text
1. 현재 PageState 확인
2. elementId에 해당하는 registry item 조회
3. selectorCandidates를 priority 순서로 시도
4. visible/enabled 조건 확인
5. 후보가 여러 개면 stableHints로 재필터링
6. 하나로 확정되면 실행
7. 실패하면 MAPPING_FAILED 처리
```

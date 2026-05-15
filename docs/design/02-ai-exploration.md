---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 04-page-state-dom.md
  - 06-risk-policy.md
  - ADR-001-ai-exploration-mvp.md
  - ADR-002-dom-and-image-observation.md
---

# 02. AI 탐색 세션 설계

## 목적

AI 탐색 세션은 사용자가 URL, 계정 정보, 시험 방법 설명을 입력했을 때 AI가 웹 제품을 탐색하고, 실제 제품 형상에 기반하여 테스트케이스와 실행계획 후보를 생성하기 위한 구조다.

## 핵심 개념

| 개념 | 설명 |
|---|---|
| `ExplorationSession` | 한 번의 AI 탐색 작업 전체 |
| `Observation` | 현재 화면을 AI가 판단할 수 있도록 정리한 관찰 데이터 |
| `AiDecision` | AI가 현재 화면을 보고 다음 행동 또는 판단을 제안한 결과 |
| `ExplorationAction` | AI 결정에 따라 실제로 수행할 탐색 행동 |
| `ExplorationMemory` | 이미 방문한 화면, 시도한 행동, 발견한 기능 후보 저장 |
| `CandidateFeature` | AI가 발견한 기능 후보 |
| `CandidateCrudFlow` | AI가 발견한 CRUD 흐름 후보 |
| `HumanReviewGate` | 사람 검토 또는 승인이 필요한 지점 |

## 탐색 루프

```text
현재 화면 관찰
→ Observation 생성
→ AI 판단
→ AiDecision 생성
→ Risk Policy 검사
→ ExplorationAction 실행
→ 새 화면 관찰
→ PageState / PageFlow 후보 생성
→ CandidateFeature / CandidateCrudFlow 갱신
→ 반복
```

## ExplorationSession 예시

```json
{
  "explorationSessionId": "EXP_20260515_001",
  "projectId": "PROJECT_USER_MANAGEMENT",
  "targetUrl": "https://example.com/admin",
  "goal": "사용자 관리 기능의 CRUD 흐름을 탐색하고 테스트케이스 후보를 생성한다.",
  "inputSources": {
    "featureList": true,
    "manual": true,
    "webShape": true
  },
  "mode": "AI_ASSISTED_EXPLORATION",
  "llmMode": "GPT_WEB_IMPORT_OR_API_ADAPTER",
  "environmentType": "staging",
  "riskPolicyId": "RISK_DEFAULT",
  "testDataProfileId": "PROFILE_DEFAULT",
  "status": "IN_PROGRESS"
}
```

## Observation

Observation은 특정 시점의 화면을 AI가 판단할 수 있도록 정리한 관찰 데이터다.

Observation은 다음을 포함한다.

- 현재 URL
- title
- visibleTexts
- DOM Summary
- form 정보
- table 정보
- ElementRegistry 참조
- 이전 action 결과
- 필요 시 masked screenshot

## Observation 유형

| 유형 | 설명 |
|---|---|
| `TEXT_DOM_PRIMARY` | DOM Summary와 텍스트 정보 중심 관찰 |
| `TEXT_DOM_WITH_IMAGE` | DOM Summary와 스크린샷을 함께 사용하는 관찰 |
| `IMAGE_ASSISTED_ONLY` | DOM 정보가 부족해 이미지 판단을 보조로 사용하는 관찰 |
| `ERROR_STATE` | 오류 화면 또는 예외 상태 관찰 |
| `UNKNOWN_STATE` | 기존 PageState와 매칭되지 않는 화면 관찰 |

## AiDecision

AiDecision은 AI가 Observation을 보고 내린 구조화된 판단이다.

```json
{
  "aiDecisionId": "DEC_001",
  "observationId": "OBS_001",
  "decisionType": "NEXT_ACTION",
  "intent": "DISCOVER_CREATE_FLOW",
  "proposedAction": {
    "action": "click",
    "elementId": "PAGE_001.el_0001",
    "description": "등록 버튼을 클릭하여 사용자 등록 화면을 탐색한다."
  },
  "expectedOutcome": {
    "transitionType": "URL_CHANGE_OR_DOM_CHANGE",
    "expectedTexts": ["사용자 등록", "저장"],
    "expectedPageStateName": "사용자 등록 화면"
  },
  "riskAssessment": {
    "riskLevel": "LOW",
    "riskFlags": [],
    "reason": "등록 화면으로 이동하는 버튼으로 판단되며 실제 데이터 변경은 아직 발생하지 않음"
  },
  "confidence": 0.86,
  "requiresHumanReview": false
}
```

## 이미지/스크린샷 관찰 전략

기본 전략은 다음이다.

```text
텍스트 DOM 우선 + 선택적 이미지 보강
```

이미지는 다음 상황에서만 LLM 판단에 보강한다.

- 아이콘 버튼이 많아 DOM 텍스트만으로 의미 파악이 어려운 경우
- label 없는 입력칸이 많은 경우
- 모달/팝업 구조가 DOM만으로 불명확한 경우
- div 기반 테이블이라 구조 추출이 어려운 경우
- 대시보드/그래프처럼 시각 정보가 핵심인 경우
- 화면 깨짐, 겹침, 가려짐 같은 시각 결함을 봐야 하는 경우

이미지를 LLM에 전달하기 전 masked screenshot을 생성한다.

## 탐색 중단 조건

| 항목 | 기본값 |
|---|---:|
| 최대 탐색 step | 50 |
| 최대 PageState | 20 |
| 동일 URL 반복 허용 | 3회 |
| 동일 action 반복 허용 | 2회 |
| HIGH 행동 자동 실행 | 금지 |

## HumanReviewGate

사람 검토가 필요한 경우:

- HIGH 리스크 행동
- PROHIBITED 후보
- 삭제/발송/결제/권한변경
- AI confidence 낮음
- 동일 후보가 여러 개
- 화면 의미 불명확
- 자동 생성 TC 과다

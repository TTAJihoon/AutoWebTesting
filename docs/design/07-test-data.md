---
status: stable
lastUpdated: 2026-05-15
related:
  - 06-risk-policy.md
  - 05-execution-plan.md
---

# 07. 테스트 데이터 관리

## 기본 원칙

테스트 데이터는 계정 정보, 일반 입력값, 실행 시 생성값, 파일 입력값을 구분한다.

LLM에는 비밀번호, 토큰, 실제 계정정보 등 민감정보를 전달하지 않는다.

## 변수 유형

| 유형 | 설명 | LLM 전달 |
|---|---|---:|
| `secret` | ID, 비밀번호, 토큰 등 민감정보 | 금지 |
| `testData` | 이름, 검색어, 일반 입력값 | 가능 |
| `generated` | 실행 시점에 생성되는 고유값 | 가능 |
| `file` | 업로드 테스트용 파일 경로 | 파일명 정도만 가능 |

## TestDataProfile 예시

```json
{
  "testDataProfileId": "PROFILE_DEFAULT",
  "name": "기본 테스트 데이터",
  "variables": [
    {
      "name": "LOGIN_ID",
      "type": "secret",
      "valueSource": "localCredentialStore",
      "sendToLlm": false
    },
    {
      "name": "LOGIN_PASSWORD",
      "type": "secret",
      "valueSource": "localCredentialStore",
      "sendToLlm": false
    },
    {
      "name": "UNIQUE_USER_ID",
      "type": "generated",
      "pattern": "autotest_${yyyyMMddHHmmss}",
      "sendToLlm": true
    },
    {
      "name": "USER_NAME",
      "type": "testData",
      "value": "자동테스트사용자",
      "sendToLlm": true
    }
  ]
}
```

## 로그인 정보 처리

LLM에는 실제 로그인 정보를 전달하지 않는다.

LLM은 변수명만 사용한다.

```json
{
  "action": "fill",
  "elementId": "PAGE_LOGIN.el_0001",
  "valueSource": "LOGIN_ID"
}
```

실행 시점에 앱이 로컬 저장소에서 실제 값을 꺼내 Playwright에 입력한다.

## CreatedDataRegistry

AutoWebTesting이 생성한 데이터를 추적한다.

```json
{
  "createdDataRegistryId": "CDR_001",
  "runId": "RUN_20260515_001",
  "items": [
    {
      "createdDataId": "DATA_001",
      "entityType": "USER",
      "displayName": "자동테스트사용자",
      "uniqueKey": "AUTO_USER_20260515103000",
      "createdByTcId": "TC_001-001",
      "cleanupStatus": "PENDING"
    }
  ]
}
```

## Cleanup 정책

| 정책 | 설명 |
|---|---|
| `NO_CLEANUP` | 정리하지 않음 |
| `MANUAL_CLEANUP` | 보고서에 정리 대상 표시 |
| `AUTO_CLEANUP_APPROVAL_REQUIRED` | 사용자 승인 후 자동 삭제 |
| `AUTO_CLEANUP_SAFE_ONLY` | 자동 생성 데이터에 한해 자동 삭제 |

MVP 기본값은 `AUTO_CLEANUP_APPROVAL_REQUIRED`다.

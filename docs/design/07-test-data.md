---
status: stable
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 06-risk-policy.md
---

# 테스트 데이터 관리

자세한 결정 근거는 [`ADR-004-test-data-cleanup.md`](../decisions/ADR-004-test-data-cleanup.md) 참고.

## 1. 기본 원칙

테스트 데이터는 계정 정보, 일반 입력값, 실행 시 생성값, 파일 입력값을 구분한다.

LLM에는 비밀번호, 토큰, 실제 계정정보 등 민감정보를 전달하지 않는다.

## 2. 변수 유형

| 유형 | 설명 | LLM 전달 |
|---|---|---:|
| `secret` | ID, 비밀번호, 토큰 등 민감정보 | 금지 |
| `testData` | 이름, 검색어, 일반 입력값 | 가능 |
| `generated` | 실행 시점에 생성되는 고유값 | 가능 |
| `file` | 업로드 테스트용 파일 경로 | 파일명 정도만 가능 |

## 3. TestDataProfile

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

## 4. 실행계획에서 변수 사용

실행계획은 실제 값을 직접 담지 않고 `valueSource`를 사용한다.

```json
{
  "stepId": "STEP_001",
  "action": "fill",
  "elementId": "PAGE_002.el_0010",
  "valueSource": "USER_NAME"
}
```

직접 값 입력은 민감정보가 아니고 재현성에 문제가 없는 경우에만 허용한다.

## 5. 고유값 생성

등록 테스트는 반복 실행 가능해야 한다. 따라서 ID, 제목, 코드 등 중복 위험이 있는 값은 `generated` 변수를 사용한다.

```text
AUTO_USER_${yyyyMMddHHmmss}
AUTO_TITLE_${timestamp}
AUTO_CODE_${random6}
```

### 5.1 지원 패턴

| 패턴 | 설명 |
|---|---|
| `${yyyyMMddHHmmss}` | 실행 시점 타임스탬프 |
| `${timestamp}` | Unix epoch (밀리초) |
| `${random6}` | 6자리 랜덤 영숫자 |
| `${random10}` | 10자리 랜덤 영숫자 |
| `${uuid}` | UUID v4 |

## 6. Secret 처리

`secret` 변수는 다음 원칙을 따른다.

- LLM 프롬프트에 절대 포함하지 않는다.
- DOM Summary, 실행계획 JSON에도 실제 값을 넣지 않고 변수명만 표시한다.
- 로컬 저장 시 Electron `safeStorage` 또는 OS 키체인을 사용한다.
- 실행 시점에 Runner가 변수명을 실제 값으로 치환한다.
- 실패 패키지와 보고서에도 실제 값은 마스킹한다.

## 7. 테스트 데이터 정리 (Cleanup)

### 7.1 기본 원칙

```text
AutoWebTesting이 생성한 데이터만 자동 정리 대상으로 삼는다.
기존 데이터 삭제는 기본적으로 차단한다.
```

### 7.2 CreatedDataRegistry

자동 생성한 데이터를 추적하는 레지스트리.

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
      "createdAt": "2026-05-15T10:30:00+09:00",
      "cleanupStatus": "PENDING"
    }
  ]
}
```

### 7.3 Cleanup 정책

| 정책 | 설명 |
|---|---|
| `NO_CLEANUP` | 정리하지 않음 |
| `MANUAL_CLEANUP` | 보고서에 정리 대상 표시 |
| `AUTO_CLEANUP_APPROVAL_REQUIRED` | 사용자 승인 후 자동 삭제 |
| `AUTO_CLEANUP_SAFE_ONLY` | 자동 생성 데이터에 한해 자동 삭제 |

**MVP 기본값**: `AUTO_CLEANUP_APPROVAL_REQUIRED`

### 7.4 cleanup strategy

| strategy | 설명 |
|---|---|
| `DELETE_CREATED_ROW` | 생성한 데이터 행 삭제 |
| `DEACTIVATE_CREATED_ITEM` | 삭제 대신 비활성화 |
| `ROLLBACK_BY_UI` | UI를 통해 원복 |
| `MANUAL_CLEANUP` | 수동 정리 필요 |
| `NO_CLEANUP` | 정리하지 않음 |

### 7.5 CleanupPlan 예시

```json
{
  "policy": "AUTO_CLEANUP_APPROVAL_REQUIRED",
  "items": [
    {
      "cleanupId": "CLEANUP_001",
      "entityType": "USER",
      "matchValueSource": "UNIQUE_USER_ID",
      "strategy": "DELETE_CREATED_ROW",
      "requiresApproval": true,
      "riskCheck": {
        "riskLevel": "HIGH",
        "riskFlags": ["DELETE_DATA"],
        "requiresApproval": true,
        "approvalScope": "PER_RUN"
      }
    }
  ]
}
```

## 8. 테스트 데이터 snapshot

실패 재현을 위해 실행 당시의 테스트 데이터 snapshot을 저장한다. 단, `secret`은 마스킹한다.

```json
{
  "snapshotId": "SNAP_001",
  "runId": "RUN_20260515_001",
  "capturedAt": "2026-05-15T10:30:00+09:00",
  "variables": [
    { "name": "LOGIN_ID", "value": "***MASKED***" },
    { "name": "UNIQUE_USER_ID", "value": "autotest_20260515103000" },
    { "name": "USER_NAME", "value": "자동테스트사용자" }
  ]
}
```

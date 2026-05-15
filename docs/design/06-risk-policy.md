---
status: stable
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 11-runner-design.md
  - 13-prompt-specs.md
---

# 리스크 정책

자세한 결정 근거는 [`ADR-003-risk-policy.md`](../decisions/ADR-003-risk-policy.md) 참고.

## 1. 리스크 수준

| 수준 | 의미 | 기본 처리 |
|---|---|---|
| `LOW` | 읽기 또는 되돌리기 쉬운 동작 | 승인된 TC는 자동 실행 가능 |
| `MEDIUM` | 제한적 상태 변경 | 실행 전 경고 권장 |
| `HIGH` | 민감하거나 영향이 큰 동작 | 실행마다 명시 승인 필요 |
| `PROHIBITED` | 자동화 금지 | 자동 실행 차단 |

## 2. 리스크 플래그

| 플래그 | 의미 |
|---|---|
| `PAYMENT` | 실제 결제, 카드 승인, 유료 주문 확정 |
| `DELETE_DATA` | 운영 또는 중요 데이터 삭제 |
| `SEND_EXTERNAL_MESSAGE` | SMS, 이메일, 푸시, 메신저 발송 |
| `SUBMIT_TO_EXTERNAL_SYSTEM` | 외부기관 또는 외부 API 제출 |
| `DOWNLOAD_SENSITIVE_DATA` | 개인정보, 고객정보, 대량 민감정보 다운로드 |
| `CHANGE_PERMISSION` | 사용자, 역할, 관리자 권한 변경 |
| `CHANGE_SECURITY_SETTING` | 비밀번호 정책, MFA, 접근제어 변경 |
| `PUBLIC_PUBLISH` | 외부 공개 게시 |
| `IRREVERSIBLE_ACTION` | 되돌리기 어려운 작업 |
| `LEGAL_OR_FINANCIAL_ACTION` | 계약, 청구, 정산, 세금계산서, 법적 약정 |

## 3. 위험 키워드 탐지

GPT가 리스크 플래그를 누락하더라도 앱은 위험 키워드를 탐지해야 한다.

```json
{
  "DELETE_DATA": ["삭제", "영구삭제", "제거", "탈퇴", "초기화", "폐기"],
  "PAYMENT": ["결제", "주문확정", "카드승인", "청구", "입금", "정산"],
  "SEND_EXTERNAL_MESSAGE": ["발송", "문자", "SMS", "메일", "이메일", "알림톡", "푸시"],
  "CHANGE_PERMISSION": ["권한", "관리자", "역할 변경", "승인자 변경"],
  "CHANGE_SECURITY_SETTING": ["비밀번호 정책", "MFA", "2단계 인증", "접근제어", "보안설정"],
  "PUBLIC_PUBLISH": ["게시", "공개", "배포", "발행"]
}
```

### 3.1 키워드 탐지 대상

- 테스트 시나리오
- 사전조건
- 기대결과
- 실행 step 설명
- action
- element text
- button label
- nearbyText

## 4. 리스크 보정 규칙

```text
LOW + 위험 키워드 → MEDIUM 이상으로 상향
MEDIUM + 고위험 키워드 → HIGH로 상향
HIGH + 되돌리기 어려운 행위 → PROHIBITED 후보
PROHIBITED 키워드 → 자동 실행 차단
```

## 5. 3단계 통제

리스크 검사는 다음 세 시점에 수행한다.

| 단계 | 시점 | 책임 |
|---|---|---|
| 생성 전 지침 | 프롬프트 단계 | 프롬프트에 허용/금지 액션과 리스크 정의 포함 |
| 생성 후 검증 | 실행계획 import 시 | 키워드 탐지, 리스크 수준 보정 |
| 실행 직전 차단 | Runner step 시작 직전 | PROHIBITED 차단, HIGH 승인 확인 |

## 6. RiskCheckResult 구조

ExecutionPlan에는 각 step의 리스크 판단 결과가 포함되어야 한다.

```json
{
  "riskLevel": "HIGH",
  "riskFlags": ["DELETE_DATA"],
  "matchedRiskKeywords": ["삭제"],
  "requiresApproval": true,
  "approvalScope": "PER_RUN",
  "reason": "삭제 버튼 클릭이며 데이터 삭제 가능성이 있음"
}
```

### 6.1 필드 정의

| 필드 | 설명 |
|---|---|
| `riskLevel` | LOW, MEDIUM, HIGH, PROHIBITED |
| `riskFlags` | 위험 플래그 목록 |
| `matchedRiskKeywords` | 탐지된 위험 키워드 |
| `requiresApproval` | 사람 승인 필요 여부 |
| `approvalScope` | 승인 범위 |
| `reason` | 판단 이유 |

### 6.2 approvalScope

| 값 | 설명 |
|---|---|
| `NONE` | 승인 불필요 |
| `PER_ACTION` | 해당 action마다 승인 |
| `PER_TC` | 해당 TC 실행 단위 승인 |
| `PER_RUN` | 해당 run에서 한 번 승인 |
| `FORBIDDEN` | 승인 불가, 실행 차단 |

## 7. 실행 시점 처리

```text
LOW
→ 승인된 TC는 자동 실행

MEDIUM
→ 실행 전 경고 표시
→ 실행 자체는 자동 허용

HIGH
→ 실행 전 명시 승인 필요
→ approvalScope에 따라 1회/TC/run 단위 승인

PROHIBITED
→ 실행 차단
→ executionStatus = SKIPPED_RISK
```

## 8. Delete 정책

Delete는 가장 위험한 행동 중 하나이므로 별도 정책을 둔다.

- 기존 운영 데이터 삭제는 기본 차단.
- AutoWebTesting이 생성한 데이터(`CreatedDataRegistry` 등록분)만 삭제 가능.
- 삭제 액션은 기본 HIGH 또는 PROHIBITED로 분류.
- 실행 전 명시 승인 필수.

자세한 내용은 [`07-test-data.md`](07-test-data.md)와 [`ADR-004-test-data-cleanup.md`](../decisions/ADR-004-test-data-cleanup.md) 참고.

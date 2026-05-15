---
status: stable
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 07-test-data.md
  - ADR-003-risk-policy.md
---

# 06. 리스크 정책

## 기본 원칙

리스크 정책은 위험 행동을 다음 세 단계에서 통제한다.

```text
1. 생성 전 지침
2. 생성 후 검증
3. 실행 직전 차단
```

## 리스크 수준

| 수준 | 의미 | 기본 처리 |
|---|---|---|
| `LOW` | 읽기 또는 되돌리기 쉬운 동작 | 승인된 TC는 자동 실행 가능 |
| `MEDIUM` | 제한적 상태 변경 | 실행 전 경고 권장 |
| `HIGH` | 민감하거나 영향이 큰 동작 | 실행마다 명시 승인 필요 |
| `PROHIBITED` | 자동화 금지 | 자동 실행 차단 |

## 리스크 플래그

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

## 위험 키워드 예시

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

## Delete 정책

- AutoWebTesting이 생성한 데이터에 대해서만 제한적으로 허용한다.
- 기존 데이터 삭제는 기본적으로 차단한다.
- 자동 생성 데이터 삭제도 기본 `HIGH`로 보고 명시 승인 후 실행한다.

## 외부 발송 정책

SMS, 메일, 푸시 등 외부 발송은 무조건 제외하지 않는다.

- 기본 `HIGH`
- 테스트 수신자 확인 필요
- 실행 전 명시 승인 필요
- 운영 수신자 또는 불특정 다수 발송은 `PROHIBITED`

## approvalScope

| 값 | 설명 |
|---|---|
| `NONE` | 승인 불필요 |
| `PER_ACTION` | 해당 action마다 승인 |
| `PER_TC` | 해당 TC 실행 단위 승인 |
| `PER_RUN` | 해당 run에서 한 번 승인 |
| `FORBIDDEN` | 승인 불가, 실행 차단 |

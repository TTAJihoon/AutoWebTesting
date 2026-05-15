---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 04-page-state-dom.md
  - 05-execution-plan.md
  - 06-risk-policy.md
  - 08-assertion-policy.md
  - 10-ipc-contract.md
---

# Runner 설계

Playwright Runner는 검증을 마친 ExecutionPlan을 실제로 실행한다.

## 1. Runner 책임

- ExecutionPlan을 step 순서대로 실행
- 각 step 실행 직전 리스크 정책 최종 확인
- elementId를 ElementRegistry를 통해 실제 locator로 변환
- PageState 일치 여부 확인
- expectedTransition 검증
- 실패 시 스크린샷 및 컨텍스트 저장
- IPC Event로 진행 상황 스트리밍
- 실행 결과를 RunResult로 집계

## 2. Runner 구조

```text
src/runner/
├── executor.ts            (실행 오케스트레이션)
├── playwrightDomCapture.ts(DOM 캡처)
├── domSummarizer.ts       (DOM 요소 분류)
├── elementResolver.ts     (elementId → locator) [신규]
├── actionPolicy.ts        (리스크 정책 적용)
├── assertionRunner.ts     (assertion 실행 및 P/F) [신규]
├── transitionVerifier.ts  (화면 전환 검증) [신규]
└── eventEmitter.ts        (IPC Event 발신) [신규]
```

## 3. 실행 흐름

```text
1. ExecutionPlan 로드
2. 환경 준비
   - Playwright 브라우저 시작
   - 시작 URL 접속
   - 로그인 (testDataProfile의 secret 변수 치환)
3. 각 step 순차 실행
   3-1. 리스크 최종 확인 (PROHIBITED 차단, HIGH 승인 확인)
   3-2. PageState 확인 (현재 화면이 step.pageStateId와 일치하는지)
   3-3. stepType에 따른 핸들러 호출
       - ACTION → elementResolver + Playwright 명령
       - ASSERTION → assertionRunner
       - WAIT → waitFor*
       - DIALOG → dialog 핸들러 등록 후 trigger
       - TABLE_ACTION → 테이블 행 매칭 + 행 내 버튼 클릭
       - SCREENSHOT → page.screenshot
       - CLEANUP → 정리 로직 (승인 후)
   3-4. expectedTransition 검증
   3-5. StepResult 기록 + IPC Event 발신
4. 모든 step 완료 시 RunResult 집계
5. 실패 케이스가 있으면 FailurePackage 생성
6. createdDataRegistry에 등록된 데이터의 cleanup 처리
```

## 4. Element Resolve

`elementId` → 실제 Playwright locator 변환.

```text
1. 현재 PageState 확인
2. elementRegistry에서 해당 elementId 조회
3. selectorCandidates를 priority 순서로 시도
   - data-testid 시도
   - role 시도
   - label 시도
   - placeholder 시도
   - text 시도
   - css 시도
   - xpath 시도 (최후)
4. 각 시도 결과를 resolveAttempts에 기록
5. visible/enabled 조건 확인
6. 중복 매칭이면 stableHints로 재필터링
7. 단일 locator 확정 → 반환
8. 실패하면 MAPPING_FAILED + 컨텍스트 저장
```

## 5. PageState 확인

step 실행 전 현재 화면이 기대 PageState와 일치하는지 확인.

```typescript
function verifyPageState(page: Page, expected: PageState): VerifyResult {
  // 1. urlPattern이 있으면 현재 URL과 비교
  // 2. identityHints.requiredTexts 중 일정 비율 이상 표시되는지 확인
  // 3. identityHints.requiredElementIds 존재 확인
  // 4. 일치 → ok, 불일치 → PAGE_STATE_MISMATCH
}
```

**일치 기준 권장값**

- `requiredTexts`: 70% 이상 일치
- `requiredElementIds`: 100% 존재
- `urlPattern`: 완전 매치

## 6. Transition 검증

step 실행 후 expectedTransition을 검증.

| type | 검증 방식 |
|---|---|
| `URL_CHANGE` | `page.waitForURL(urlPattern, { timeout })` |
| `TEXT_APPEAR` | `page.getByText(text).waitFor({ state: 'visible', timeout })` |
| `ELEMENT_APPEAR` | locator.waitFor({ state: 'visible' }) |
| `MODAL_OPEN` | 모달 컨테이너 표시 대기 |
| `POPUP_OPEN` | `context.waitForEvent('page')` |
| `DIALOG_OPEN` | dialog event 대기 |
| `URL_CHANGE_OR_TEXT_APPEAR` | 두 조건 중 먼저 만족하는 것 채택 (Promise.race) |

기본 timeout: 5000ms. step에서 override 가능.

## 7. Dialog 처리

`page.on('dialog', handler)`로 등록한다.

```typescript
page.on('dialog', async (dialog) => {
  // 1. dialog.message()로 위험 키워드 탐지
  // 2. 실행계획의 DIALOG step과 매칭
  // 3. 매칭되면 step.response에 따라 accept/dismiss
  // 4. 매칭되지 않으면 DIALOG_UNHANDLED + 기본 dismiss
});
```

## 8. Secret 변수 치환

`fill` action 등에서 `valueSource`가 `secret` 타입이면 LLM에 전달 없이 Runner 내부에서만 실제 값으로 치환한다.

```typescript
function resolveValue(valueSource: string, profile: TestDataProfile, secrets: SecretStore): string {
  const variable = profile.variables.find(v => v.name === valueSource);
  if (!variable) throw new Error(`Variable not found: ${valueSource}`);
  if (variable.type === 'secret') return secrets.get(variable.name);
  if (variable.type === 'generated') return generatePattern(variable.pattern);
  return variable.value;
}
```

## 9. 실행 이벤트 스트림

각 step 시작/종료 시 IPC Event를 발신한다.

```typescript
eventEmitter.emit('run:step-started', {
  runId,
  tcId,
  stepId,
  action: step.action,
  pageStateId: step.pageStateId
});

// step 실행 ...

eventEmitter.emit('run:step-finished', {
  runId,
  tcId,
  stepId,
  status: 'PASSED' | 'FAILED' | 'SKIPPED',
  message
});
```

자세한 이벤트 목록은 [`10-ipc-contract.md`](10-ipc-contract.md) 참고.

## 10. 실행 취소

`run:cancel` IPC를 받으면 다음 step부터 즉시 중단한다.

- 현재 실행 중인 step은 완료까지 대기 (또는 Playwright timeout으로 자연 종료)
- 이후 step들은 `executionStatus = CANCELLED` 처리
- 부분 결과는 그대로 저장

## 11. 실패 시 컨텍스트 저장

step이 실패하면 다음 정보를 즉시 캡처한다.

- 스크린샷 (`evidence/{stepId}.png`)
- 현재 URL
- 페이지 제목
- 가시 텍스트 목록
- 콘솔 에러 메시지
- 네트워크 에러
- elementResolver attempt log
- 직전 step 결과

이 정보는 FailurePackage 생성 시 활용된다.

## 12. 환경 격리

- 각 RUN마다 새 Playwright `browserContext` 사용 → 쿠키/세션 격리
- `--user-data-dir`은 RUN별 임시 폴더 사용
- 다운로드 폴더는 `runs/{runId}/downloads/`로 설정

## 13. 품질 게이트

- PROHIBITED 자동 실행 차단
- HIGH 실행 전 명시 승인
- 알 수 없는 action 거부
- 알 수 없는 elementId는 `MAPPING_FAILED`
- assertion 없는 TC는 자동 P/F 판단 금지 (testResult = N/A)
- 실패 시 스크린샷 저장 필수

---
status: stable
lastUpdated: 2026-05-15
related:
  - 13-prompt-specs.md
  - 05-execution-plan.md
---

# GPT Web Import Workflow

GPT Web Import Mode는 앱이 LLM API를 직접 호출하지 않는 운용 방식이다. 사용자가 GPT 웹페이지에서 프롬프트를 실행하고 JSON 결과를 앱에 업로드한다.

자세한 결정 근거는 [`ADR-005-gpt-web-import-vs-api-mode.md`](../decisions/ADR-005-gpt-web-import-vs-api-mode.md) 참고.

## Step 1 — 테스트케이스 생성

**사용자 작업**

1. `prompts/testcase-generation.prompt.md`를 연다.
2. 기능목록과 매뉴얼 내용을 GPT에 입력한다.
3. GPT에 JSON만 출력하도록 요청한다.
4. 결과를 `testcases.json`으로 저장한다.
5. 앱에 업로드한다.

**앱 작업**

- JSON 파싱
- 스키마 검증
- TC_ID 형식 검사
- TC_ID 중복 검사
- 필수 필드 검사
- 리스크 수준 표시
- 검토 테이블 표시

---

## Step 2 — DOM 캡처 및 실행계획 생성

**사용자 작업**

1. 대상 URL과 계정 정보를 앱에 입력한다.
2. 앱이 로그인하고 시작 화면으로 이동한다.
3. 앱이 필요한 PageState의 DOM Summary와 Element Registry를 생성한다.
4. 승인된 TC JSON과 DOM Summary JSON을 내보낸다.
5. `prompts/dom-mapping.prompt.md`를 연다.
6. 승인된 TC JSON, DOM Summary JSON, 테스트 데이터 변수 목록, 리스크 정책을 GPT에 입력한다.
7. GPT가 반환한 실행계획 JSON을 저장한다.
8. 앱에 실행계획 JSON을 업로드한다.

**앱 작업**

- 실행계획 JSON 파싱
- 스키마 검증
- action 이름 검증
- elementId 존재 여부 검증
- PageState 존재 여부 검증
- 리스크 정책 적용
- 실행계획 검토 화면 표시

---

## Step 3 — 실행 및 실패분석

**사용자 작업**

1. 실행 가능한 TC를 선택한다.
2. HIGH 리스크 항목이 있으면 명시 승인한다.
3. 실행을 시작한다.
4. 실패 또는 차단 케이스가 있으면 failure package JSON을 내보낸다.
5. GPT 웹에서 실패분석 프롬프트를 실행한다.
6. 실패분석 JSON을 앱에 업로드한다.

**앱 작업**

- 실행 이벤트 표시
- 스크린샷 저장
- 로그 저장
- 실패 패키지 생성
- 실패분석 JSON 검증
- 결과 보고서 반영

---

## GPT 출력 보정 정책

원칙적으로 GPT 출력은 JSON만 허용한다.

다만 GPT 웹 사용 과정에서 흔히 발생하는 형식 오류를 줄이기 위해 다음 보정은 허용한다.

- Markdown 코드펜스 제거
- 첫 번째 `{` 또는 `[` 앞의 텍스트 제거
- 마지막 `}` 또는 `]` 뒤의 텍스트 제거
- UTF-8 BOM 제거
- 보정 적용 시 사용자에게 경고 표시

**앱은 필드 값 자체를 조용히 변경해서는 안 된다.** 보정은 형식에 한정한다.

---

## 업로드 시 검증 순서

```text
1. JSON 파싱 가능 여부
2. schemaVersion 확인
3. 스키마 유효성 검사 (Zod 또는 ajv)
4. 필수 식별자 형식 검사 (TC_ID, elementId, pageStateId)
5. 참조 무결성 검사
   - TC가 참조하는 변수가 TestDataProfile에 존재하는가
   - 실행계획이 참조하는 elementId가 DOM Summary에 존재하는가
   - 실행계획이 참조하는 pageStateId가 PageState 목록에 존재하는가
6. 리스크 키워드 탐지 (보정 적용)
7. 검토 화면 표시
```

검증 단계 중 하나라도 실패하면 사용자에게 어느 단계, 어느 필드, 어떤 이유로 실패했는지 명확히 표시한다.

---

## API Mode와의 관계

API Mode는 위 Step 1~3의 LLM 호출 부분을 앱 내부에서 자동화하는 방식이다. 입력 데이터, 스키마, 검증 절차, 사람 검토 절차는 모두 동일하게 유지한다.

```text
GPT Web Import Mode:
  사용자가 프롬프트 복사 → GPT 웹에서 실행 → JSON 저장 → 앱에 업로드

API Mode:
  앱이 프롬프트 구성 → LLM API 호출 → JSON 자동 수신 → 동일 검증 → 동일 검토
```

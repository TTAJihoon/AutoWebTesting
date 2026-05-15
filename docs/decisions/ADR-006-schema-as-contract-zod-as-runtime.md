# ADR-006: JSON Schema는 사람이 읽는 계약, Zod는 런타임 검증과 TS 타입의 원천

## 상태

- status: accepted
- date: 2026-05-15

## 배경

AutoWebTesting은 GPT 웹 임포트, API Mode, 내부 모듈 간 데이터 교환에서 동일한 JSON 계약을 사용한다.

이 계약은 다음 세 곳에서 동시에 일관성을 가져야 한다.

1. `docs/schemas/*.schema.json` — 사람과 LLM이 읽는 계약 문서
2. `src/shared/types.ts` — TypeScript 타입
3. 런타임 검증 — `import` 시점에 비신뢰 JSON을 검증

세 가지를 따로 관리하면 다음 문제가 발생한다.

- 필드를 한 곳에만 추가하고 다른 곳에 반영하지 않음
- 타입과 런타임 검증이 불일치
- LLM이 잘못된 필드명을 생성해도 통과
- 사람이 읽는 계약 문서와 실제 검증이 다름

## 선택지

### 선택지 A — JSON Schema를 SSOT로, ajv로 검증, TS 타입은 별도 작성

`docs/schemas/*.schema.json`을 직접 작성하고 ajv로 검증한다. TS 타입은 수기 작성하거나 `json-schema-to-typescript`로 자동 생성한다.

- 장점: JSON Schema가 표준이며 GPT가 이해하기 좋음.
- 단점: ajv는 zod보다 TS 타입 통합성이 약하다. 자동 생성 타입은 가독성이 떨어진다.

### 선택지 B — Zod를 SSOT로, TS 타입은 `z.infer`, JSON Schema는 자동 생성

`src/shared/schemas/*.ts`에 Zod 스키마를 작성하고 `z.infer`로 TS 타입을 도출한다. `zod-to-json-schema`로 `docs/schemas/*.schema.json`을 자동 생성한다.

- 장점: TS 타입과 런타임 검증이 자동 일치. 코드 중심 워크플로우에 적합.
- 단점: 자동 생성된 JSON Schema는 사람이 읽기에 가독성이 다소 떨어지고, GPT 프롬프트에 첨부하기에 군더더기가 있다.

### 선택지 C — JSON Schema는 사람용 계약, Zod는 런타임 + 타입 원천, CI로 일치 검증

`docs/schemas/*.schema.json`은 사람과 LLM이 읽는 **계약 문서**로 직접 관리한다. `src/shared/schemas/*.ts`는 동일 계약을 Zod로 표현하며, **TS 타입은 `z.infer`로 도출하고 런타임 검증도 Zod로 수행한다**. CI 스크립트가 두 파일의 일치 여부를 검증한다.

- 장점: 사람용 계약 문서의 가독성을 유지하면서 코드의 타입 안정성과 런타임 검증을 보장.
- 단점: 두 파일을 동기화해야 하지만, CI로 자동 검증되므로 수기 동기화 오류가 빠르게 드러난다.

## 결정

**선택지 C를 채택한다.**

## 이유

AutoWebTesting의 핵심 사용자(QA 담당자, 비개발자)는 JSON Schema를 직접 읽고 GPT 웹 프롬프트에 첨부한다. 따라서 JSON Schema는 사람이 읽기 좋게 수기 관리할 필요가 있다.

반면 코드 측면에서는 Zod의 `z.infer` 패턴이 TS 타입과 런타임 검증의 일치를 자동 보장하므로, 개발자가 두 곳을 따로 관리할 필요가 없다.

두 영역의 일치는 CI 스크립트로 강제한다. 일치 검증 방식은 다음 두 가지를 모두 적용한다.

1. **샘플 JSON 양방향 검증**: `docs/examples/*.sample.json` 각각이 JSON Schema와 Zod 양쪽 모두를 통과해야 한다.
2. **필드 목록 일치 검증**: 각 스키마의 최상위/주요 필드 이름과 enum 값이 두 파일에서 같은지 비교한다.

## 영향 범위

- `docs/schemas/*.schema.json` — 사람용 계약, 수기 관리
- `src/shared/schemas/*.ts` — Zod 스키마, 수기 관리 (계약 동기화)
- `src/shared/types.ts` — Zod에서 `z.infer`로 도출. 기존 수기 타입은 단계적으로 교체.
- `scripts/validate-schemas.mjs` — JSON Schema + Zod 양쪽 검증, 일치 검증 추가
- `package.json` — `zod` (이미 있음), `ajv` (JSON Schema 검증용), `ajv-formats` 추가 필요
- 모든 IPC import 핸들러 — Zod로 검증 후 TS 타입으로 처리

## 작성/수정 절차

새 필드를 추가하거나 변경할 때 순서:

```text
1. docs/schemas/*.schema.json 수정 (사람용 계약 갱신)
2. src/shared/schemas/*.ts 수정 (Zod 스키마 갱신)
3. docs/examples/*.sample.json 갱신 또는 추가
4. npm run schema:check 실행 (CI 검증)
5. 관련 design 문서에 변경 반영
```

## 관련 문서

- [`design/03-data-schema-overview.md`](../design/03-data-schema-overview.md)
- [`design/05-execution-plan.md`](../design/05-execution-plan.md)
- [`design/15-phase-roadmap.md`](../design/15-phase-roadmap.md)

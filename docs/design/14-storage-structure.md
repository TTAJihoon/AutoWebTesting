---
status: stable
lastUpdated: 2026-05-15
related:
  - 03-data-schema-overview.md
  - 09-run-result-failure.md
---

# 저장 구조

## 1. 기본 저장 루트

```text
Documents/AutoWebTesting/projects/{projectName}/
```

`Documents` 폴더는 Electron `app.getPath('documents')`로 얻는다.

## 2. 권장 폴더 구조

```text
Documents/AutoWebTesting/projects/{projectName}/
├── project.json
├── inputs/
│   ├── feature-list.xlsx
│   └── manuals/
├── imports/
│   ├── testcases.import.json
│   ├── execution-plan.import.json
│   └── failure-analysis.import.json
├── testcases/
│   ├── testcases.reviewed.json
│   └── testcases.xlsx
├── dom/
│   ├── page-states.json
│   ├── dom-summary.PAGE_001.json
│   ├── element-registry.PAGE_001.json
│   ├── dom-summary.PAGE_002.json
│   └── element-registry.PAGE_002.json
├── execution-plans/
│   └── execution-plan.reviewed.json
├── runs/
│   └── RUN-20260514-143022/
│       ├── run-result.json
│       ├── failure-package.json
│       ├── report.html
│       └── evidence/
├── reports/
│   ├── execution-result.xlsx
│   └── evidence.zip
└── logs/
    └── app.log
```

## 3. 폴더별 역할

| 폴더 | 역할 |
|---|---|
| `project.json` | 프로젝트 메타정보 (이름, 대상 URL, 생성일 등) |
| `inputs/` | 사용자가 제공한 원본 입력 (기능목록, 매뉴얼) |
| `imports/` | GPT 웹에서 가져온 JSON 원본 보관 |
| `testcases/` | 검토 완료된 테스트케이스 |
| `dom/` | PageState별 DOM Summary와 ElementRegistry |
| `execution-plans/` | 검토 완료된 실행계획 |
| `runs/` | 런별 실행 결과와 증적 |
| `reports/` | 사용자에게 전달할 보고서 (Excel, ZIP) |
| `logs/` | 앱 로그 |

## 4. 저장 원칙

- 실행 결과는 프로젝트 하위에 저장한다.
- runId는 타임스탬프 기반으로 생성한다 (`RUN-YYYYMMDD-hhmmss`).
- DOM Summary와 Element Registry는 실행계획과 함께 추적 가능해야 한다.
- 실패 재현을 위해 실행 당시의 테스트 데이터 snapshot을 저장한다 (secret은 마스킹).
- 한 프로젝트 내에서 여러 런을 누적 저장한다 (덮어쓰지 않음).
- 이전 검토 결과는 `*.reviewed.json`으로 분리 저장한다.

## 5. project.json 예시

```json
{
  "schemaVersion": "0.3",
  "projectId": "PROJECT_USER_MANAGEMENT",
  "name": "사용자관리",
  "targetUrl": "https://example.com/admin",
  "createdAt": "2026-05-15T09:00:00+09:00",
  "lastOpenedAt": "2026-05-15T11:00:00+09:00",
  "testDataProfileId": "PROFILE_DEFAULT",
  "riskPolicyId": "RISK_DEFAULT",
  "appVersion": "0.1.0"
}
```

## 6. 파일명 규칙

- DOM Summary: `dom-summary.{pageStateId}.json`
- Element Registry: `element-registry.{pageStateId}.json`
- 검토 완료 JSON: `*.reviewed.json`
- Import 원본: `*.import.json`
- 보고서: `*.xlsx`, `*.html`, `*.zip`

## 7. 민감정보 처리

- 비밀번호/토큰은 Electron `safeStorage` 또는 OS 키체인에 저장. 파일로 저장하지 않는다.
- `testData.snapshot.json`의 `secret` 변수는 `***MASKED***`로 저장한다.
- 로그 파일에도 secret 값은 마스킹한다.
- 스크린샷에 secret이 노출될 수 있으므로 LLM 전달용 이미지는 별도 마스킹 파일로 만든다.

## 8. SQLite (Phase 8)

후속 Phase에서는 다음 정보를 SQLite로 관리한다.

```sql
projects   (id, name, targetUrl, createdAt, ...)
runs       (id, projectId, runId, startedAt, summary, ...)
testcases  (id, projectId, tcId, reviewStatus, ...)
artifacts  (id, runId, type, path)
```

파일 시스템 저장과 병행한다. SQLite는 인덱스/조회용이며, 실제 콘텐츠는 파일로 유지한다.

## 9. 보존 정책

- 런 결과는 사용자가 직접 삭제할 때까지 보존한다.
- 자동 정리는 하지 않는다 (운영 사고 위험).
- 사용자가 명시적으로 "오래된 런 정리"를 요청하면 시작 일자가 N일 이상 지난 런만 삭제 후보로 표시한다.

## 10. 백업

- 백업은 MVP 범위 밖.
- 사용자가 `Documents/AutoWebTesting` 폴더 전체를 복사하면 백업이 된다는 점만 안내한다.

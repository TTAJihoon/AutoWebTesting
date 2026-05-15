---
status: stable
lastUpdated: 2026-05-15
related:
  - 09-run-result-failure.md
---

# 14. 저장 구조

## 기본 저장 루트

```text
Documents/AutoWebTesting/projects/{projectName}/
```

## 권장 폴더 구조

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
├── exploration/
│   ├── exploration-session.json
│   ├── observations/
│   ├── screenshots/
│   └── candidates/
├── testcases/
│   ├── testcases.reviewed.json
│   └── testcases.xlsx
├── dom/
│   ├── page-states.json
│   ├── dom-summary.PAGE_001.json
│   └── element-registry.PAGE_001.json
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

## 저장 원칙

- 실행 결과는 프로젝트 하위에 저장한다.
- runId는 타임스탬프 기반으로 생성한다.
- DOM Summary와 ElementRegistry는 실행계획과 함께 추적 가능해야 한다.
- 실패 재현을 위해 실행 당시의 테스트 데이터 snapshot을 저장한다.
- 원본 스크린샷과 LLM 전달용 masked screenshot은 구분 저장한다.

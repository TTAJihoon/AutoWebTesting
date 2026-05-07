# AutoWebTesting

AutoWebTesting은 제품 매뉴얼과 기능리스트를 기반으로 웹 테스트케이스를 생성, 검토, 실행, 보고하기 위한 Windows 설치형 로컬 시험 도구입니다.

1차 목표는 Windows 11 시험용 PC에 설치되는 Local Runner입니다. 이 프로그램은 Playwright로 테스트 대상 웹 제품을 조작하고, 결과를 로컬에 저장하며, Excel 결과서, HTML 보고서, 증적 ZIP 파일을 생성합니다.

## 핵심 개념

```text
기능리스트와 매뉴얼
-> LLM이 생성한 테스트케이스 JSON
-> 사람 검토
-> DOM 요약
-> LLM이 생성한 실행계획 JSON
-> Playwright 실행
-> 실패 로그와 증적 저장
-> LLM이 생성한 실패 분석 JSON
-> Excel / HTML / ZIP 산출물 생성
```

AutoWebTesting은 두 가지 LLM 사용 방식을 지원하도록 설계합니다.

```text
API 사용 모드
- 프로그램 안에서 기능리스트와 매뉴얼을 업로드합니다.
- 프로그램이 외부 LLM API를 호출해 테스트케이스 생성, DOM 매핑, 실패 분석을 수행합니다.

GPT 웹 결과물 업로드 모드
- 프로그램은 LLM을 직접 호출하지 않습니다.
- 사용자가 공식 GPT 웹페이지에서 제공된 프롬프트를 실행합니다.
- 프로그램은 GPT 웹에서 받은 JSON 결과물을 업로드 받아 처리합니다.
```

두 모드는 같은 JSON 스키마를 사용합니다. 그래서 초기에는 GPT 웹 결과물 업로드 방식으로 시작하고, 이후 API 연동 방식으로 확장할 수 있습니다.

## MVP 범위

- Windows 11 데스크톱 앱
- Electron + TypeScript 기반 구조
- Playwright 기반 브라우저 자동 실행
- 로컬 프로젝트 폴더 저장
- 고정 기능리스트 양식 사용
  - `대분류`
  - `중분류`
  - `소분류`
  - `기능설명`
- 표준/상세 테스트케이스 생성 모드
- 생성된 테스트케이스 사람 검토
- 실행 전 DOM 요약 생성
- GPT 웹 결과물 JSON 업로드 흐름
- Excel 결과서, HTML 보고서, 증적 ZIP 내보내기

## 현재 구현된 기능

- GPT 웹 결과물 형식의 TC JSON 업로드
- TC JSON 필수 필드 검증
- TC_ID 중복 및 형식 확인
- 위험도 및 자동화 대상 여부 표시
- TC 검토 상태 변경
  - 승인
  - 수정 필요
  - 제외
  - 반려
- 자동화 대상 여부 토글
- 검토 요약 통계 표시

샘플 업로드 파일:

```text
examples/testcases.sample.json
```

## 저장소 구조

```text
docs/
  product-requirements.md
  architecture.md
  data-schema.md
  gpt-web-workflow.md
  prompt-specs.md
  risk-policy.md

prompts/
  testcase-generation.prompt.md
  dom-mapping.prompt.md
  failure-analysis.prompt.md

examples/
  testcases.sample.json

schemas/
  testcase.schema.json
  dom-summary.schema.json
  execution-plan.schema.json
  failure-analysis.schema.json

src/
  main/
  preload/
  renderer/
  shared/
  runner/
```

## 개발 환경

현재 저장소는 아래 기술 스택을 기준으로 초기 골격이 구성되어 있습니다.

- Electron
- React
- TypeScript
- Playwright
- SQLite 호환 로컬 저장소

의존성 설치:

```powershell
npm install
```

개발 모드 실행:

```powershell
npm run dev
```

타입 검사:

```powershell
npm run typecheck
```

JSON 스키마 파싱 검증:

```powershell
npm run schema:check
```

## 개발 브랜치 흐름

`main` 브랜치에 직접 수정하지 않고 기능 브랜치를 만들어 작업합니다.

```powershell
git switch -c codex/my-feature
git add .
git commit -m "작업 내용"
git push -u origin codex/my-feature
```

이후 GitHub에서 Pull Request를 만들어 `main`에 병합합니다.

## 현재 상태

현재 브랜치에는 MVP 기반 작업이 포함되어 있습니다.

- 제품 요구사항 및 아키텍처 문서
- GPT 웹 결과물 업로드 흐름 문서
- JSON 스키마 초안
- Electron 앱 초기 골격
- Playwright Runner 자리표시자 코드

앞으로 기능이 추가되거나 설계가 바뀌면 README도 한국어 기준으로 함께 갱신합니다.

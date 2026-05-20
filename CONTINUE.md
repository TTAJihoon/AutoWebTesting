# 이어서 작업하기 (다른 PC / 다른 세션)

> `git pull` 후 이 문서부터 읽으면 곧바로 작업에 복귀할 수 있다.

---

## 1. 지금 어디까지 했나 (Last updated: 2026-05-20)

### ✅ LLM Provider 추상화 완료 (2026-05-20)

| 구성 요소 | 파일 | 상태 |
|---|---|---|
| 설계 문서 | `doc/07-llm-providers.md` (신규) | ✅ |
| 결정 등록 | `doc/06-decisions.md` → **D48** | ✅ |
| 추상 인터페이스 | `app/api/providers/base.py` (`LLMProvider`, `ChatResult`) | ✅ |
| Anthropic provider | `app/api/providers/anthropic_provider.py` | ✅ |
| OpenAI provider | `app/api/providers/openai_provider.py` | ✅ |
| Gemini provider | `app/api/providers/gemini_provider.py` | ✅ |
| 라우터 | `app/api/providers/__init__.py` (모델 prefix → provider) | ✅ |
| LLMClient 리팩토링 | `app/api/llm_client.py` (provider 라우팅 + 캐시 키에 model 포함) | ✅ |
| settings.py 확장 | `app/config/settings.py` (provider별 키 + active provider) | ✅ |
| UI provider 토글 | `app/ui/dashboard.py` (드롭다운 + 선택된 provider 키만 입력) | ✅ |
| 환경변수 | `.env.example`, `requirements.txt` | ✅ |
| 단위 테스트 | `tests/test_provider_routing.py` (28개 PASS) | ✅ |

회귀 검증:
- pytest 전체 **64개 PASS** (V6 36 + provider 28)
- Mock 파이프라인 재실행: **TC 79개·INFERRED 0%·기법 분포 동일** — baseline 100% 유지
- 모델명 prefix(`claude-*`/`gpt-*`/`gemini-*`)로 자동 라우팅 — 기존 `prompts/*.md` 그대로 사용

### 사용 예
```powershell
# Anthropic (기본)
$env:LLM_PROVIDER="anthropic"; $env:ANTHROPIC_API_KEY="sk-ant-..."
python scripts\run_stage123.py

# OpenAI로 전환 (prompts의 model 필드 일괄 변경 필요)
$env:LLM_PROVIDER="openai"; $env:OPENAI_API_KEY="sk-..."
# prompts/*.md 의 model: claude-sonnet-4-6 → gpt-4o 로 일괄 수정
python scripts\run_stage123.py
```



### ✅ 완료
- **설계 동결** — `doc/` 7개 문서 작성 완료 (D1~D43 확정)
- **PoC-α** — Stage 1~3 시뮬레이션, TC 41개 산출
- **PoC-β** — Reviewer Gate 검토 완료, approved 41/41, PASS
- **PoC-γ** — 자동 실행 41/41, PASS 32 / FAIL 9 (BUG-1~5 검출), PASS
- **Q-INFRA-1~3 결정** — D44(PostgreSQL) D45(PySide6) D46(Inno Setup)

### ✅ Phase 1 완료 (2026-05-19)

| 태스크 | 파일 | 상태 |
|---|---|---|
| T1: 스캐폴드 | `requirements.txt`, 디렉터리 구조 | ✅ |
| T2: Prompts | `prompts/dom_spec.md` 외 3종 | ✅ |
| T3: config + tools | `app/config/`, `app/tools/` | ✅ |
| T4: api | `app/api/llm_client.py`, `call_contracts.py` | ✅ |
| T5: core | `app/core/stage0~7.py`, `orchestrator.py` | ✅ |
| T6: auth | `app/auth/db_client.py`, `admin_cli.py` | ✅ |
| T7: UI | `app/ui/` 5개 창 (PySide6) | ✅ |
| T8: main + installer | `app/main.py`, `installer/` | ✅ |

### ✅ Q-PROD-1 해소 + Phase 2 환경 준비 완료 (2026-05-19)
- **D47: 그누보드5 선정** — [gnuboard/gnuboard5](https://github.com/gnuboard/gnuboard5)
- Docker Compose: `data/oss/gnuboard5/docker-compose.yml`
- 기능 명세서: `data/oss/gnuboard5/manual/gnuboard5_spec.md` (Stage 1 입력)
- 원클릭 셋업: `data/oss/gnuboard5/setup.ps1`
- 실행 스크립트: `scripts/run_stage123.py` (Docker 없이 Stage 1~3 가능)
- 실행 스크립트: `scripts/run_full_pipeline.py` (Stage 0~7 CLI)
- 환경 재현 가이드: `SETUP.md` (다른 PC에서 이 파일 먼저 읽기)
- 의존성 동결: `requirements.lock` (pip freeze 결과)
- Python 의존성: 모두 설치 완료 (이 PC)
- Playwright Chromium: 설치 완료 (이 PC)

### ✅ Mock 파이프라인 실행 완료 (2026-05-19)
- `python scripts\run_stage123_mock.py` 성공
- TC 79개 / V1~V5 모두 PASS (1회) / INFERRED 0% / 0.1초
- 기법: happy_path 23 / negative_basic 28 / equivalence 17 / boundary 9 / state_transition 2
- 산출물: `data/runs/822c7f56/` (tc_verified.json, tc_review.xlsx)
- 버그 수정: `stage2_tc_design.py` — expected_output→expected, technique→design_technique 필드 정규화

### ⚠ 이 PC에서 남은 작업
- **Docker Desktop 미설치** → `winget install Docker.DockerDesktop` 후 재부팅 필요
- **PostgreSQL 미설치** → `winget install PostgreSQL.PostgreSQL.17` 필요 (GUI 앱 실행 시)
- Stage 5~7은 Docker + gnuboard5 설치 후 가능

### ✅ 자산 저장소 (Asset Store) 구현 완료 (2026-05-20)

외부 검토 그룹 제안서(`proposal-for-awt-claude/`) 분석 후 채택·구현:

| 구성 요소 | 파일 | 상태 |
|---|---|---|
| 결함 카탈로그 (PoC-γ 시드 5건) | `data/assets/defect-catalog/BOARD_CMS/` | ✅ |
| 도메인 불변규칙 YAML | `data/assets/domain-invariants/BOARD_CMS.yaml` (8건) | ✅ |
| 도메인 불변규칙 YAML | `data/assets/domain-invariants/USER_AUTH.yaml` (4건) | ✅ |
| 제품 유형 분류기 | `app/assets/product_types.py` (7종) | ✅ |
| 불변규칙 로더 | `app/assets/invariants_loader.py` | ✅ |
| 결함 카탈로그 API | `app/assets/defect_catalog.py` | ✅ |
| PATTERN_EXTRACT Contract | `prompts/pattern_extract.md` (5번째 LLM Contract) | ✅ |
| TC_DESIGN v2 업그레이드 | `prompts/tc_design.md` → invariants + past_defects 주입 | ✅ |
| Stage 2 자산 주입 | `app/core/stage2_tc_design.py` | ✅ |
| Stage 3 V2·V3 3단계 출처 | `app/core/stage3_verify.py` (MANUAL/INVARIANT/INFERRED) | ✅ |
| 자산 이벤트 로그 DB | `app/auth/db_client.py` → `awt_asset_events` 테이블 | ✅ |

Mock 파이프라인 재검증 결과 (2026-05-20):
- TC 79개 생성, V1~V5 모두 PASS (1회차)
- **INFERRED 0%** (목표 <30% 대비 최상)
- source_quote 분포: **MANUAL 92.4% / INVARIANT 7.6% / INFERRED 0%**

핵심 설계 결정:
- D38 Stateless = "API 호출 간 대화 기록 없음" (파일 자산과 별개)
- 3단계 source_quote: INVARIANT 출처는 V3 INFERRED 비율에서 제외
- patternProposal은 AI 자동 생성 → 검수자가 승인/거절만 (30초)
- 제품 유형별 별도 YAML 파일 (`BOARD_CMS.yaml`, `USER_AUTH.yaml` 등)
- 추적성: 파일 `_meta` 블록 + PostgreSQL `awt_asset_events` 테이블

### ✅ V6 선택자 안정성 점수 구현 완료 (2026-05-20)

| 파일 | 내용 |
|---|---|
| `app/validation/v6_selector_stability.py` | 선택자 9계층 점수 + oracle 명료성 + 실패 분류 |
| `app/core/stage5_execute.py` | Stage 5 완료 후 v6_annotate() 자동 연동 |
| `tests/test_v6_selector_stability.py` | 단위 테스트 36개 전체 PASS |

기능 요약:
- `selector_stability_score`: text_exact(0.92) > data_testid(0.88) > url(0.82) > id(0.78) > class(0.62) > xpath(0.32)
- `oracle_clarity_score`: 기대 결과 검증 가능성 (인용문 +0.20, 추상표현 -0.15)
- `classify_failure`: `selector_unstable` | `oracle_mismatch` | `app_defect` | `blocked`
- `exec_confidence`: stability×0.50 + clarity×0.35 + retry_penalty×0.15
- XPath 오분류 방지 3중 필터 (부정형 후방탐색, HTML태그 차단목록, XPath 부분문자열 검사)

### ⏸ 다음 예정
- **Phase 2** — 그누보드5 실전 AWT 실행 (Stage 0~7 end-to-end)

---

## 2. 다음 행동

**→ 새 PC라면 `SETUP.md`를 먼저 읽어라.**

Phase 2 실행 순서:

```powershell
# 옵션 A: Stage 1~3만 (Docker 없이, API key만 필요)
set ANTHROPIC_API_KEY=sk-ant-...
python scripts\run_stage123.py

# 옵션 B: Stage 0~7 전체 (Docker + 그누보드5 설치 필요)
.\data\oss\gnuboard5\setup.ps1          # 그누보드5 Docker 셋업
# → http://localhost:8080/install 에서 초기 설치
set ANTHROPIC_API_KEY=sk-ant-...
python scripts\run_full_pipeline.py `
    --url http://localhost:8080 `
    --manual data\oss\gnuboard5\manual\gnuboard5_spec.md `
    --auth-id admin --auth-pw <비밀번호>

# 옵션 C: GUI 앱 (PostgreSQL + Docker 모두 필요)
python -m app.auth.admin_cli init       # 최초 1회
python -m app.auth.admin_cli create-user
python app\main.py
```

**추천 지금 당장: 옵션 A** — API key만 있으면 Stage 1~3 TC 설계 결과 확인 가능

---

## 3. 문서 읽기 우선순위

**처음이라면 (전체 파악):**
```
1. README.md                        ← 프로젝트 개요
2. doc/README.md                    ← 설계 진입점
3. doc/01-architecture.md           ← 전체 흐름 (Stage 0~7)
4. doc/06-decisions.md              ← 왜 이렇게 됐는지 (주제별 결정 이력)
5. doc/05-poc-plan.md               ← 현재 어디까지 했는지
```

**개발 진입 직전 (Phase 1 본 개발 준비):**
```
1. doc/01-architecture.md §2-§4    ← 디렉터리 + Stage 책임
2. doc/02-llm-contracts.md          ← API 호출 4종 Contract
3. doc/03-tc-schema.md              ← TC 컬럼·검증 규칙
4. doc/06-decisions.md §9           ← 미해결 (Q-INFRA-1~3 결정 필요)
```

**ISO 관련 검수가 필요할 때:**
```
- doc/04-iso-mapping.md             ← 25010/25023/25051/25059 × Layer 매트릭스
```

---

## 4. 핵심 결정 사항 (요약)

진입 전 알고 있어야 할 5가지:

| | 내용 | 근거 |
|---|---|---|
| **무엇** | ISO/IEC 25023 기반 웹 SW 시험 자동화 도구 | D1·D2·D7·D8 |
| **어떻게 (PoC)** | Claude Code 환경에서 prompt 품질 검증 | D25 (PoC 한정) |
| **어떻게 (프로덕션)** | Python Windows 데스크탑 앱 (.exe) | **D37** ← 최신 |
| **LLM** | Anthropic API stateless 호출, 정형화 Call Contract | D38·D41 |
| **인증** | 중앙 DB 서버(PostgreSQL), 처리는 로컬 | D40·**D44** |
| **UI** | PySide6 (LGPL, Qt6 공식) | **D45** |
| **설치** | Inno Setup + PyInstaller | **D46** |
| **LLM Provider** | Anthropic/OpenAI/Gemini 추상화 (모델 prefix 자동 라우팅) | **D48** |

상세는 `doc/06-decisions.md` 참조.

---

## 5. 환경 설정

### 5.1. PoC 환경 (현재)

```bash
# Claude Code 설치되어 있어야 함
# Python (Excel 빌더용)
pip install openpyxl
```

PoC 산출물 재생성:
```bash
python tools/build_tc_review_xlsx.py
# → data/poc/2026-05-19/output/tc_review.xlsx 갱신
```

### 5.2. Phase 1 환경 (구현 완료)

```bash
# PostgreSQL DB 초기화 (최초 1회)
psql -U postgres -f installer/db_init.sql
python -m app.auth.admin_cli init
python -m app.auth.admin_cli create-user   # admin 계정 생성

# 앱 실행
pip install -r requirements.txt
playwright install chromium
python app/main.py

# Windows .exe 빌드 (Inno Setup 설치 필요)
.\installer\build.ps1
```

환경변수 (`.env` 또는 시스템):
```
AWT_DB_HOST=localhost
AWT_DB_PORT=5432
AWT_DB_NAME=awt
AWT_DB_USER=awt_user
AWT_DB_PASSWORD=changeme
```

---

## 6. 단계별 산출물 위치

| 단계 | 산출 | 위치 |
|---|---|---|
| PoC mockup | 미니 게시판 HTML + 합성 매뉴얼 | `data/poc/2026-05-19/sample-board/` |
| PoC-α 산출 | TC 41개 (CSV/Excel/MD) | `data/poc/2026-05-19/output/` |
| PoC-β 진행 | 사용자 검토 결과 | `data/poc/2026-05-19/result.md` (직접 작성) |
| Phase 1 산출 | 데스크탑 앱 소스 | `app/` (완성) |
| Phase 1 인스톨러 | Inno Setup .iss + PyInstaller .spec | `installer/` |

---

## 7. 작업이 막혔을 때

| 상황 | 참조 |
|---|---|
| 설계 의도가 모호 | `doc/06-decisions.md` 주제별 결정 이력 |
| 이전 PoC 방향 vs 현재 차이 | `doc/archive/` (D25 이전 자료) |
| 4인 토론·이론 근거 | `doc/archive/01-theory/01-four-person-debate.md` |
| ISO 매핑 디테일 | `doc/archive/02-iso-25023-mapping/` (요약은 `doc/04-iso-mapping.md`) |
| 폐기된 결정 이유 | `doc/06-decisions.md` 의 ~~취소선~~ 항목 |

---

## 8. 개발 지침 (불변)

1. **설계 우선** — 코딩 전 `doc/`에서 합의·동결
2. **수정계획 제시** — 즉시 코딩 금지, 변경안 사전 제시
3. **추측 금지** — 모르면 묻기
4. **Skill화 고려** — 분리 배포 가능한 단위로 설계 (Phase 2)
5. **디렉터리 확인** — 새 파일 작성 전 위치 확인
6. **단계 제안** — 단계 완료 시마다 다음 후보 + 추천 + 이유 명시

---

## 9. 이 파일 갱신 규칙

PoC 단계가 진행될 때마다 §1 (지금 어디까지 했나)와 §2 (다음 행동) 업데이트.
큰 변경 시 git commit 메시지에 `[CONTINUE]` 태그 포함.

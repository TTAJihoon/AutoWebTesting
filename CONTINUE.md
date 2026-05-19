# 이어서 작업하기 (다른 PC / 다른 세션)

> `git pull` 후 이 문서부터 읽으면 곧바로 작업에 복귀할 수 있다.

---

## 1. 지금 어디까지 했나 (Last updated: 2026-05-19)

### ✅ 완료
- **설계 동결** — `doc/` 7개 문서 작성 완료 (D1~D43 확정)
- **PoC-α** — Stage 1~3 시뮬레이션, TC 41개 산출
  - 결과: V1·V4·V5 PASS / V2(58.5%)·V3(INFERRED 41.5%) 부분 PASS
  - 분석: `data/poc/2026-05-19/output/analysis.md`
  - 산출: `data/poc/2026-05-19/output/tc_review.xlsx`

### ⏳ 진행 중
- **PoC-β** — `tc_review.xlsx` 사용자 검토 대기
  - TC 41개에 A/E/R/P 결정 + 검토 노트
  - 가이드: `data/poc/2026-05-19/HOW-TO-REVIEW.md`

### ⏸ 다음 예정
- **PoC-γ** — β 통과 후 Playwright MCP 자동 실행
- **Phase 1 (Desktop App)** — PoC γ 통과 후 본 개발 진입

---

## 2. 다음 행동

PoC-β를 *이 PC*에서 이어가려면:

```
1. doc/README.md 읽기 (5분) — 전체 구조 파악
2. doc/05-poc-plan.md 읽기 (10분) — PoC 계획 + 현재 상태
3. data/poc/2026-05-19/HOW-TO-REVIEW.md 읽기 (3분) — β 진행 방법
4. data/poc/2026-05-19/output/tc_review.xlsx 열기 → 검토
5. 결과를 data/poc/2026-05-19/result.md 에 기록
```

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
| **인증** | 중앙 DB 서버, 처리는 로컬 | D40 |

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

### 5.2. Phase 1 환경 (미래, 아직 구현 안 됨)

```bash
# (예정)
pip install -r requirements.txt
playwright install chromium
python app/main.py
```

---

## 6. 단계별 산출물 위치

| 단계 | 산출 | 위치 |
|---|---|---|
| PoC mockup | 미니 게시판 HTML + 합성 매뉴얼 | `data/poc/2026-05-19/sample-board/` |
| PoC-α 산출 | TC 41개 (CSV/Excel/MD) | `data/poc/2026-05-19/output/` |
| PoC-β 진행 | 사용자 검토 결과 | `data/poc/2026-05-19/result.md` (직접 작성) |
| Phase 1 산출 | 데스크탑 앱 .exe | `app/` (미생성) |

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

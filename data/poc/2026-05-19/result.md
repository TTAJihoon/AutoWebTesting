# PoC 결과 — 2026-05-19

> PoC 종료 후 본 파일을 채워주세요. 빈 양식은 AWT가 제공.
>
> **양식 변경 (D29):** D25 pivot 후 PoC가 α/β/γ 3종으로 재정의됨. 아래는 *새 양식*. 이전 양식(option a/b/c)은 더 이상 사용 안 함.

## 기본 정보

- PoC 일자: 2026-05-19
- 대상 제품: 미니 게시판 mockup (`sample-board/board.html`)
- 총 소요: __ 시간

## PoC-1: Skill 분리 호출

### Option (a) — "TC만 생성하고 stop"
- 결과: PASS / FAIL / PARTIAL
- skill이 자동실행을 멈췄나? Y/N
- 컬럼 추가됐나? Y/N
- 누락 컬럼: 
- source_quote 채움률: __%
- INFERRED 비율: __%
- design_technique 분포: happy=__, equiv=__, bound=__, neg_basic=__, neg_deep=__, state=__, cross=__
- 메모: 

### Option (b) — 재시험 메커니즘 (옵션 a 실패 시만)
- 결과: PASS / FAIL
- 수정된 TC만 재실행? Y/N
- 기존 결과 보존? Y/N
- 새 TC 생성 여부: Y/N
- 메모: 

### Option (c) — Playwright MCP 직접 (a·b 모두 실패 시만)
- 결과: PASS / FAIL
- Playwright MCP로 실행 가능? Y/N
- steps 자연어 → 액션 변환 성공률: __%
- 메모: 

### 채택 경로
- chosen_path: a / b / c / none
- 이유: 

## PoC-2: source_quote grep 정확도

샘플 10개 기준:
- M1 (완전일치): __/10 = __%
- M2 (공백정규화): __/10 = __%
- M3 (띄어쓰기무시): __/10 = __%
- 채택 매칭 전략: M_
- 메모: 

## PoC-3: INFERRED 비율

- 측정 비율: __%
- 결정 임계: 5% / 10% / 15%
- 결정 사유: 

## PoC-4: 재호출 사이클

- 1회 재호출 통과율: __%
- 2회 누적 통과율: __%
- 3회 누적 통과율: __%
- 채택 상한: _회
- 사유: 

## PoC-5: Prompt 충돌

- 결과: 충돌 없음 / 조정 필요 / 심함
- 충돌 항목 (있다면): 
- 조정 방향 (있다면): 

## PoC-6: Excel 컬럼 수용성

- 결과: AS_IS_OK / NEED_SUFFIX / NEED_RENAME / NEED_SEPARATE_SHEET
- 충돌 컬럼명 (있다면): 
- 채택 전략의 사유: 

## 종합 판정 — Phase 1.1 진입 가능?

- 모든 종료 조건 충족: YES / NO
- 미충족 항목 (있다면): 

## 기타 발견·관찰

<자유 노트>

## AWT가 검토할 항목

- [ ] PoC-1 결과에 따른 §4·§5 TC 스키마 완성
- [ ] PoC-2·3 결과에 따른 V2·V3 임계 확정
- [ ] PoC-5·6 결과에 따른 prompt augmentation §3.1 조정
- [ ] PoC-1 옵션 (c)인 경우 AWT 자체 실행 책임 설계 추가

# Product Requirements

## Purpose

AutoWebTesting is a local Windows desktop program for creating, reviewing, executing, and reporting reusable web test cases.

The program is designed for target products that are accessed by URL and account credentials. It focuses on black-box web testing through Playwright and keeps generated testcases reviewable before execution.

## LLM Modes

### API Mode

The program directly calls an external LLM API.

Required user input:

- Fixed-format feature list Excel
- Product manual files
- Target URL
- Account information

LLM-assisted steps:

- Testcase generation
- DOM to execution plan mapping
- Failure analysis

### GPT Web Import Mode

The program does not call an LLM.

The user runs the provided prompts in an official GPT web page and uploads JSON results into the program.

Required uploaded JSON files:

- Testcase generation JSON
- Execution plan JSON
- Failure analysis JSON when failed cases exist

## Feature List Format

The feature list Excel format is fixed.

| Column | Required | Description |
| --- | --- | --- |
| 대분류 | Yes | Top-level feature group |
| 중분류 | Yes | Middle-level feature group |
| 소분류 | Yes | Minor feature group used for TC_ID numbering |
| 기능설명 | Yes | Natural language feature description |

## Testcase ID Rule

`TC_ID` uses this format:

```text
TC_(minor category number)-(testcase sequence number)
```

Example:

```text
TC_001-001
TC_001-002
TC_002-001
```

Minor category numbers are assigned by feature list order. Testcase sequence numbers start at `001` per minor category.

Excluded or deprecated testcases remain in history instead of being physically removed. This preserves traceability across reviews, executions, and reports.

## Testcase Fields

User-facing fields:

- 대분류
- 중분류
- 소분류
- TC_ID
- 테스트 시나리오
- 입력/사전조건
- 기대 출력/사후조건
- 테스트 결과
- 실패 상세 결과

Internal fields:

- Review status
- Automation target flag
- Risk level
- Risk flags
- Automation reason
- Source mode

## Review Policy

Only approved testcases become execution planning candidates.

Execution planning requires:

- `reviewStatus = APPROVED`
- `automationTarget = true`
- Risk level allowed by policy

## Result Policy

Execution status and testcase result are separated.

`executionStatus` explains whether the test could be executed. `testResult` explains whether the tested behavior passed or failed.

`testResult = P/F` is valid only when `executionStatus = COMPLETED`.

## MVP Output

The MVP exports:

- Testcase Excel
- Execution result Excel
- HTML report
- Evidence ZIP

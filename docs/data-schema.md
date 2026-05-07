# Data Schema Notes

The JSON schemas in `schemas/` are the stable contracts between the app, GPT web import workflow, and future API integration.

## Testcase JSON

Purpose:

- Import generated testcases
- Preserve human review status
- Preserve traceability even when a testcase is excluded

Important fields:

- `tcId`
- `majorCategory`
- `middleCategory`
- `minorCategory`
- `scenario`
- `precondition`
- `expectedResult`
- `reviewStatus`
- `automationTarget`
- `riskLevel`
- `riskFlags`

## Review Status

Recommended values:

| Value | Meaning |
| --- | --- |
| `DRAFT` | Generated but not reviewed |
| `APPROVED` | Approved for execution planning |
| `NEEDS_REVISION` | Needs text or scope correction |
| `REJECTED` | Not accepted as a valid testcase |
| `EXCLUDED` | Valid but intentionally excluded |
| `DEPRECATED` | Retained for traceability but no longer used |

## Execution Status

Execution status is separate from P/F result.

| Value | Meaning |
| --- | --- |
| `NOT_RUN` | Not executed yet |
| `COMPLETED` | Steps completed and P/F can be judged |
| `BLOCKED` | Precondition or environment blocked execution |
| `MAPPING_FAILED` | TC could not be mapped to DOM elements |
| `SCRIPT_FAILED` | Execution plan existed, but Playwright failed |
| `SKIPPED_RISK` | Skipped because of risk policy |
| `MANUAL_REQUIRED` | Requires human confirmation |
| `CANCELLED` | User cancelled the run |

`testResult` should be `P` or `F` only when `executionStatus = COMPLETED`.

## DOM Summary JSON

Purpose:

- Remove unnecessary HTML
- Preserve only elements that help GPT choose actions
- Avoid sending raw selectors or sensitive values to GPT when possible

Recommended element fields:

- `elementId`
- `role`
- `tag`
- `type`
- `label`
- `text`
- `placeholder`
- `name`
- `required`
- `visible`
- `enabled`
- `nearbyText`
- `formId`

## Execution Plan JSON

Purpose:

- Convert reviewed testcases into safe, limited Playwright actions
- Prevent arbitrary code execution

Allowed initial actions:

- `goto`
- `click`
- `fill`
- `selectOption`
- `check`
- `uncheck`
- `uploadFile`
- `waitForText`
- `assertTextVisible`
- `assertUrlContains`
- `assertElementVisible`
- `assertElementNotVisible`
- `assertValueEquals`
- `takeScreenshot`

## Failure Analysis JSON

Purpose:

- Convert machine logs into human-readable failure details
- Classify whether the failure is likely product behavior, mapping error, script error, data issue, or environment issue

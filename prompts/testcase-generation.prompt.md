# Testcase Generation Prompt

You are generating web product testcases from a fixed feature list and product manual.

Return valid JSON only. Do not use Markdown code fences. Do not write explanations outside JSON.

## Input

The user will provide:

1. Generation level: `standard` or `detailed`
2. Feature list with columns:
   - 대분류
   - 중분류
   - 소분류
   - 기능설명
3. Product manual content

## Required Output

Return JSON matching `schemas/testcase.schema.json`.

## Rules

- Generate TC_ID values as `TC_001-001`.
- The first number is the minor category sequence in feature list order.
- The second number is the testcase sequence within that minor category.
- Keep all categories exactly as written in the feature list.
- Use Korean for `scenario`, `precondition`, and `expectedResult`.
- Set `reviewStatus` to `DRAFT`.
- Set `automationTarget` to true only when a browser can reasonably execute it.
- Set risk fields when a testcase may change data or affect external systems.
- If a testcase is useful but not automatable, set `automationTarget` to false and explain in `automationReason`.
- Do not include account passwords or secrets.
- Do not invent URLs unless the source content clearly contains them.

## Standard Mode Guidance

Prefer reusable web test categories:

- Normal behavior
- Required value missing
- Invalid input format
- Permission or access restriction
- Error message
- Save, update, or query reflection

## Detailed Mode Guidance

Add applicable cases:

- Boundary value
- Session expiration
- Refresh or back navigation
- File size or file type restriction
- Paging, sorting, and filtering combinations
- Repeated execution behavior

## JSON Only

The response must start with `{` and end with `}`.

# Prompt Specifications

The prompt files under `prompts/` are written for GPT web import mode. API mode should use the same task definitions and output schemas internally.

## Common Rules

Every prompt should require:

- Valid JSON only
- No Markdown code block
- No explanation outside JSON
- No invented credentials
- No arbitrary Playwright code
- No unsafe action without risk flag

## Prompt 1: Testcase Generation

Inputs:

- Fixed feature list
- Product manual content
- Generation level: `standard` or `detailed`

Output:

- Testcase JSON matching `schemas/testcase.schema.json`

Main task:

- Classify feature rows by major, middle, and minor category
- Generate TC_ID values
- Create scenario, precondition, and expected result
- Mark automation target and risk level
- Keep uncertain cases as reviewable

## Prompt 2: DOM Mapping

Inputs:

- Approved testcase JSON
- DOM summary JSON
- Account variable list
- Risk policy

Output:

- Execution plan JSON matching `schemas/execution-plan.schema.json`

Main task:

- Choose element IDs for each step
- Use allowed action names only
- Use account/test data variable names instead of raw secrets
- Mark uncertain mappings as `NEEDS_MAPPING_REVIEW`
- Mark unsupported cases as `NOT_AUTOMATABLE`

## Prompt 3: Failure Analysis

Inputs:

- Failed testcase package JSON

Output:

- Failure analysis JSON matching `schemas/failure-analysis.schema.json`

Main task:

- Explain the failure in readable language
- Classify likely cause
- Suggest what the user should review
- Do not override raw P/F data

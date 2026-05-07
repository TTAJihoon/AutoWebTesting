# GPT Web Workflow

GPT web import mode exists so the local desktop program can work without calling an LLM API.

In this mode, users run official GPT web pages manually and upload JSON files back into the app.

## Step 1: Testcase Generation

User action:

1. Open `prompts/testcase-generation.prompt.md`.
2. Paste the fixed feature list and manual content into GPT.
3. Ask GPT to return JSON only.
4. Save the result as `testcases.json`.
5. Upload `testcases.json` into the app.

App action:

- Validate JSON
- Check TC_ID pattern
- Check required fields
- Show TC rows in a readable review table

## Step 2: DOM Mapping

User action:

1. Enter target URL and account information in the app.
2. Let the app open the page and generate DOM summary JSON.
3. Export approved TC JSON and DOM summary JSON.
4. Open `prompts/dom-mapping.prompt.md`.
5. Paste approved TC JSON and DOM summary JSON into GPT.
6. Save the returned execution plan JSON.
7. Upload execution plan JSON into the app.

App action:

- Validate execution plan JSON
- Check action names
- Check element IDs exist in DOM summary
- Apply risk policy
- Execute allowed plans through Playwright

## Step 3: Failure Analysis

User action:

1. After execution, export failure package JSON if failed or blocked cases exist.
2. Open `prompts/failure-analysis.prompt.md`.
3. Paste failure package JSON into GPT.
4. Save the returned failure analysis JSON.
5. Upload failure analysis JSON into the app.

App action:

- Validate failure analysis JSON
- Attach failure details to run result
- Show readable failure summary
- Include results in Excel and HTML reports

## JSON Output Rule

GPT output must be valid JSON only.

Do not include:

- Markdown code fences
- Commentary
- Natural language outside JSON
- Example text after JSON

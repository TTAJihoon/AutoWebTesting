# AutoWebTesting

AutoWebTesting is a Windows desktop application concept for generating, reviewing, and executing reusable web test cases from product manuals and feature lists.

The first target is a local runner installed on a Windows 11 test PC. It uses Playwright to operate the target web product, stores results locally, and exports Excel, HTML, and evidence ZIP artifacts.

## Core Idea

```text
Feature list and manual
→ LLM generated testcase JSON
→ Human review
→ DOM summary
→ LLM generated execution plan JSON
→ Playwright execution
→ Failure log and evidence
→ LLM generated failure analysis JSON
→ Excel / HTML / ZIP report
```

The app supports two LLM modes:

```text
API mode
- The app uploads feature lists and manuals.
- The app calls an external LLM API for testcase generation, DOM mapping, and failure analysis.

GPT web import mode
- The app does not call an LLM.
- The user runs the provided prompts in an official GPT web page.
- The app imports the returned JSON files.
```

Both modes use the same JSON schemas so the implementation can switch between manual import and API integration later.

## MVP Scope

- Windows 11 desktop app using Electron and TypeScript
- Playwright based browser execution
- Local project storage
- Fixed feature list format:
  - `대분류`
  - `중분류`
  - `소분류`
  - `기능설명`
- Standard and detailed testcase generation modes
- Human review for generated testcases
- DOM summary generation before execution planning
- JSON import workflow for GPT web results
- Excel result, HTML report, and evidence ZIP export

## Repository Layout

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

## Development Setup

This repository is scaffolded for:

- Electron
- React
- TypeScript
- Playwright
- SQLite compatible local storage

Install dependencies:

```powershell
npm install
```

Run the desktop app in development mode:

```powershell
npm run dev
```

Run type checks:

```powershell
npm run typecheck
```

Validate JSON schema files are parseable:

```powershell
npm run schema:check
```

## Branch Workflow

Use feature branches instead of editing `main` directly.

```powershell
git switch -c codex/my-feature
git add .
git commit -m "Describe the change"
git push -u origin codex/my-feature
```

Then create a pull request into `main`.

## Status

This branch contains the initial MVP foundation:

- Product and architecture documents
- GPT web workflow documents
- JSON schema drafts
- Electron app scaffold
- Playwright runner placeholders

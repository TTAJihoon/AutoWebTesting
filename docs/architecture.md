# Architecture

## Runtime Shape

AutoWebTesting is a Windows 11 desktop application.

```text
Desktop UI
→ Local project store
→ GPT/API adapter
→ DOM summarizer
→ Execution plan importer
→ Playwright runner
→ Evidence collector
→ Report generator
```

The first implementation is local-first. A future version can add API mode or shared storage without changing the core schemas.

## Main Modules

### Renderer UI

The renderer is the user-facing desktop UI.

Initial screens:

- Project setup
- LLM mode selection
- Testcase import or generation
- Testcase review
- Execution settings
- DOM analysis and execution plan import
- Run monitor
- Reports and evidence export

### Main Process

The Electron main process owns privileged operations:

- Local project folder creation
- File import and export
- SQLite access
- Playwright runner process orchestration
- Report generation

### Shared Schemas

Schemas in `schemas/` define the interchange contract for:

- Testcase JSON
- DOM summary JSON
- Execution plan JSON
- Failure analysis JSON

These schemas are shared by GPT web import mode and future API mode.

### Runner

The runner converts execution plan steps into Playwright commands.

The runner does not execute arbitrary GPT-generated code. It executes only known action names and known element IDs.

## GPT Web Import Flow

```text
Prompt file + user supplied input
→ GPT web page
→ JSON result
→ Program validation
→ Human-friendly display
```

The program treats GPT output as untrusted input until it passes schema validation and policy checks.

## DOM Mapping Flow

```text
Target page HTML/DOM
→ Program extracts useful visible elements
→ Program assigns elementId values
→ DOM summary JSON goes to GPT
→ GPT returns execution plan using elementId values
→ Program resolves elementId to internal selectors
→ Playwright executes
```

The GPT output should not contain raw Playwright code.

## Failure Analysis Flow

```text
Failed testcase
→ Failed step
→ Current URL
→ Visible text summary
→ Console/network errors
→ Screenshot path
→ Failure package JSON
→ GPT failure analysis JSON
→ Report field update
```

## Local Data

Default storage root:

```text
Documents/AutoWebTesting/projects/{projectName}/
```

Suggested project folders:

```text
inputs/
llm-tasks/
imports/
testcases/
dom/
execution-plans/
runs/
reports/
evidence/
```

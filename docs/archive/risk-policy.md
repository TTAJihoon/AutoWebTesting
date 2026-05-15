# Risk Policy

Risk policy prevents the runner from executing destructive or external-impact actions without review.

## Risk Levels

| Level | Meaning | Default Behavior |
| --- | --- | --- |
| `LOW` | Read-only or reversible action | Auto execution allowed |
| `MEDIUM` | State change with limited impact | User confirmation recommended |
| `HIGH` | Sensitive or broad impact | Manual approval required |
| `PROHIBITED` | Not allowed for automation | Auto execution blocked |

## Risk Flags

| Flag | Meaning |
| --- | --- |
| `PAYMENT` | Actual payment, card approval, paid order confirmation |
| `DELETE_DATA` | Delete production or important data |
| `SEND_EXTERNAL_MESSAGE` | Send SMS, email, push, or messenger notification |
| `SUBMIT_TO_EXTERNAL_SYSTEM` | Submit data to an external agency or external API |
| `DOWNLOAD_SENSITIVE_DATA` | Download personal, customer, or bulk sensitive data |
| `CHANGE_PERMISSION` | Change user, role, or administrator permission |
| `CHANGE_SECURITY_SETTING` | Change password policy, MFA, or access control |
| `PUBLIC_PUBLISH` | Publish content externally |
| `IRREVERSIBLE_ACTION` | Perform hard-to-rollback action |
| `LEGAL_OR_FINANCIAL_ACTION` | Contract, billing, settlement, tax invoice, or legal commitment |

## Default Execution Rules

```text
LOW
→ execute when testcase is approved

MEDIUM
→ show warning before execution

HIGH
→ require explicit user approval per run

PROHIBITED
→ do not execute automatically
```

## GPT Output Handling

If a GPT result suggests a risky action but does not include the matching risk flag, the app should still detect likely risk keywords and pause execution for review.

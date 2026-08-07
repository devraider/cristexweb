# Replacement-host recovery artifact register/template

## Handling rules

This committed register is deliberately secret-free. Copy it to an approved
incident evidence system before use; keep only sanitized status/evidence summaries
in Git. Never enter a secret value, kubeconfig, private key, recovery code, token,
credential-bearing URL, sensitive endpoint, raw provider state, raw backup manifest,
or host-specific address here.

For sensitive artifacts, `Reference` means a custodian-approved **off-node locator
or record ID only**, not the value or a retrieval command. A reviewer records only
`verified`, `failed`, or `unknown`, plus UTC date and evidence record ID. Any
`UNKNOWN — STOP` row blocks replacement execution. Changing a row does not grant a
mutation approval.

## Incident decision record

| Field | Sanitized entry |
|---|---|
| Incident/reference ID | `<required>` |
| Incident commander | `<required>` |
| UTC opened | `<required>` |
| Event classification | UNKNOWN — STOP |
| Old-host fencing evidence reference | UNKNOWN — STOP |
| Storage exclusivity evidence reference | UNKNOWN — STOP |
| Recovery identity model | UNKNOWN — STOP |
| Identity decision approver and UTC time | UNKNOWN — STOP |
| Approved execution-plan revision | NOT AUTHORED — GATE 3 BLOCKED |
| Declared RPO | UNKNOWN — STOP |
| Declared RTO | UNKNOWN — STOP |
| Expected incident data loss | UNKNOWN — STOP |
| Public PROD route state | must remain disabled/not reactivated during recovery |

Allowed event classifications are `reboot/same-host`, `replacement-host`, or
`unknown`; unknown is handled as replacement and stops execution. Allowed identity
models are `preserve-existing` or `create-new`; never record or execute a hybrid.

## Required artifact register

| Artifact or prerequisite | Required sanitized evidence | Reference (never the value) | Current status |
|---|---|---|---|
| Old-host power/network fencing | Independent proof the old host cannot serve or automatically rejoin; owner, UTC time, rollback owner | `<evidence record ID>` | UNKNOWN — STOP |
| Old-host route isolation | Independent proof old tunnel/DNS/origin paths cannot direct traffic to the old host | `<evidence record ID>` | UNKNOWN — STOP |
| Exclusive storage ownership | Proof exactly one recovery host can attach/mount/write each relevant storage target | `<evidence record ID>` | UNKNOWN — STOP |
| Recovery identity decision | Approved preserve-existing or create-new decision with rationale and no hybrid procedure | `<decision record ID>` | UNKNOWN — STOP |
| k3s datastore | Actual datastore type, backup format/time, integrity check, restore compatibility, and reviewed procedure | `<off-node evidence record ID>` | UNKNOWN — STOP |
| Exact k3s version/configuration | Exact version, architecture, configuration revision, and approved artifact source | `<off-node evidence record ID>` | UNKNOWN — STOP |
| k3s server token | Custodian, independent accessibility, rotation/recovery decision, and successful non-disclosing recovery check | `<off-node secret-manager record ID only>` | UNKNOWN — STOP |
| Host/storage design | Disk identity mapping, filesystem/mount design, capacity, ownership, encryption-access result, and non-destructive attachment plan | `<off-node evidence record ID>` | UNKNOWN — STOP |
| Git desired state | Reviewed repository revision and independent off-node availability | `<repository and immutable revision>` | UNKNOWN — STOP |
| Argo CD component artifacts | Human-selected chart/application versions, independently accepted signing-key trust/status, captured signature/hash-binding, immutable architecture-specific image digests, target-cluster compatibility, soak decision, and independent off-node availability; the source-only [candidate provenance](argocd-candidate-provenance.md) is research evidence, not selection or recovery proof | `<artifact/decision evidence record ID>` | CANDIDATE EVIDENCE ONLY — STOP |
| Immutable workload images/build inputs | Required digests or reproducible-build revisions and confirmed off-node availability | `<registry/build evidence record ID>` | UNKNOWN — STOP |
| OpenTofu state | Protected host-local single-writer owner, exact ignored state path, encryption/key-custody result, timestamped off-node Google Drive copy, integrity check, isolated restore result, and sanitized state revision | `<off-node state-recovery evidence record ID>` | UNKNOWN — STOP |
| Infisical bootstrap material | Custodian, infrastructure/DEV/PROD scope separation, and non-disclosing recovery check | `<off-node secret-manager record ID only>` | UNKNOWN — STOP |
| Application encryption keys | Separate environment custodians and non-disclosing recovery/compatibility checks | `<off-node secret-manager record IDs only>` | UNKNOWN — STOP |
| Argo CD repository access | Custodian and non-disclosing private bootstrap-access check | `<off-node secret-manager record ID only>` | UNKNOWN — STOP |
| GHCR pull access | Custodian and non-disclosing private pull-access check for required immutable images | `<off-node secret-manager record ID only>` | UNKNOWN — STOP |
| Cloudflare/tunnel ownership | Current external owner, route-disabled evidence, recovery/rotation decision, and later reactivation owner | `<off-node provider evidence record ID>` | UNKNOWN — STOP |
| PostgreSQL backups | Environment-separated, application-consistent backup time, integrity result, encryption-access check, and off-node copy | `<off-node backup evidence record ID>` | UNKNOWN — STOP |
| MongoDB backups | Environment-separated, application-consistent backup time, integrity result, encryption-access check, and off-node copy | `<off-node backup evidence record ID>` | UNKNOWN — STOP |
| Other mutable state | Redis/RabbitMQ and application-state disposition, consistency requirement, and off-node recovery evidence where required | `<off-node backup/decision record ID>` | UNKNOWN — STOP |
| RPO/RTO acceptance | Approved RPO/RTO, selected recovery point, expected data loss, and timing/acceptance method | `<decision record ID>` | UNKNOWN — STOP |

## Later-gate artifacts

These rows are not Gate 3 prerequisites. Gate 4 creates and approves the execution
plan from the resolved prerequisite register; Gate 5 executes an isolated rehearsal
and records its outcome.

| Later artifact | Required sanitized evidence | Reference (never the value) | Current status |
|---|---|---|---|
| Replacement execution plan (Gate 4) | Reviewed tool- and version-specific plan with separate approvals and rollback checkpoints | `<approved plan revision>` | NOT AUTHORED — GATE 3 BLOCKED |
| Isolated restore rehearsal (Gate 5) | Clean isolated target, chosen identity model, timed results, integrity/application/isolation checks, and residual risks | `<rehearsal evidence record ID>` | NOT RUN — GATE 4 BLOCKED |

## Per-stage evidence template

Use one row per approved stage. Do not paste raw output if it can contain sensitive
or identifying data.

| UTC start/end | Stage | Approval/evidence record ID | Source revision or digest | Sanitized result | Rollback checkpoint | Residual risk | Reviewer |
|---|---|---|---|---|---|---|---|
| `<required>` | `<required>` | `<required>` | `<required or not applicable>` | `NOT RUN` | `<required>` | `<required>` | `<required>` |

## Final acceptance record

All checks remain `NOT RUN/BLOCKED` in the committed template.

| Check | Result | Sanitized evidence reference |
|---|---|---|
| Exactly one authoritative cluster and one storage writer | NOT RUN/BLOCKED | `<required>` |
| Old host and replacement cannot both rejoin | NOT RUN/BLOCKED | `<required>` |
| Private control-plane and fallback access | NOT RUN/BLOCKED | `<required>` |
| Desired state reconciled from reviewed revision | NOT RUN/BLOCKED | `<required>` |
| Environment isolation and negative cross-access | NOT RUN/BLOCKED | `<required>` |
| Mutable data and application encryption behavior restored | NOT RUN/BLOCKED | `<required>` |
| Recovery point measured against approved RPO | NOT RUN/BLOCKED | `<required>` |
| Recovery duration measured against approved RTO | NOT RUN/BLOCKED | `<required>` |
| Public PROD route separately reviewed after private acceptance | NOT RUN/BLOCKED | `<required>` |
| Final approver, UTC time, and residual-risk acceptance | NOT RUN/BLOCKED | `<required>` |

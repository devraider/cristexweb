# Reactive Resume PostgreSQL exposure-rotation contract

Status: **SOURCE-ONLY DESIGN / NOT RUN / BLOCKED**.

This runbook freezes the separately approved scope for rotating exactly the two
Reactive Resume PostgreSQL credentials that were exposed during review. It is a
value-free, non-executable contract. It adds no Ansible wrapper, action plugin,
playbook, Kubernetes object, Infisical call, PostgreSQL call, Secret write, role
change, database change, NetworkPolicy change, workload rollout, or route change.
No password, username value, Secret data, token, URL credential, request/response
body, hash, or SQL output may be read, generated, logged, copied, or committed by
this source-only contract.

The machine-readable contract is
[`reactive-resume-postgresql-exposure-rotation.yml`](../ansible/files/policies/reactive-resume-postgresql-exposure-rotation.yml),
and the offline contract is
[`test_reactive_resume_postgresql_exposure_rotation_contract.py`](../tests/test_reactive_resume_postgresql_exposure_rotation_contract.py).
The existing broad PostgreSQL uploader, broad Infisical StaticSecret, shared
provisioning wrapper, and all-consumer CloudNativePG source are forbidden inputs.
They must not gain a rotation flag or be invoked indirectly.

## Approved and frozen scope

Only one environment may be handled by one separately approved invocation. DEV and
PROD must never be rotated concurrently. The exact source is:

- Infisical project slug: `cristexweb-infrastructure`;
- project ID: `619656da-14f3-4872-857b-be103cdc5326`;
- environment: `prod`;
- path: `/shared-services/postgresql`;
- source closure: exactly 15 administrator, TLS, CristexHub, Reactive Resume,
  and Keycloak keys recorded in the policy;
- only the selected environment's password key may change;
- the other 14 source keys must remain byte-for-byte untouched by the future
  provider operation, without their values entering evidence.

The exact consumers are:

| Environment | Database | Fixed role/principal | Existing target Secret |
|---|---|---|---|
| DEV | `reactive_resume_dev` | `reactive_resume_dev_owner` | `shared-postgresql-reactive-resume-dev` |
| PROD | `reactive_resume_prod` | `reactive_resume_prod_owner` | `shared-postgresql-reactive-resume-prod` |

Both target Secrets are metadata-only contracts: Namespace `shared-services`, type
`Opaque`, exact keys `username` and `password`, creation policy `Orphan`, and the
Infisical-owned labels in the machine-readable policy. Their values are never
included in source or evidence. Existing broad-lane objects are unaccepted drift;
they are not evidence that this rotation contract is complete.

## Same-principal successor semantics

This is a **new password for the existing principal** (`same-principal-new-password`), not a new PostgreSQL user.
The fixed role name, DatabaseRole resource, Database, Secret name, and source
username key do not change. CloudNativePG `DatabaseRole.spec.name` is immutable;
a future lane must not delete/recreate a role or database to rotate a password.
Username changes, new roles, role memberships, ownership changes, `ALTER ROLE`
operations outside the accepted owner path, database deletion, PVC deletion, and
role/database recreation are forbidden.

There is no RabbitMQ-style username overlap in this contract. A same-principal
password replacement does not revoke existing PostgreSQL sessions. Any application
restart, session termination, or consumer cutover requires a separate approval and
is not implied by this design. The predecessor is considered revoked only after a
fresh protected predecessor authentication attempt fails; an authorization denial
is not authentication revocation.

## Preconditions and no-output custody

A future dedicated lane must install cleanup before generating any successor value:
`umask 077`, a private temporary directory, mode `0600` protected files, traps for
normal and signal exits, and a final residue check. Predecessor custody must be
created and encrypted before a remote source write. Successors are exactly 64
lowercase hexadecimal characters and must never appear in argv, environment,
stdout, stderr, Ansible facts, diffs, plans, traces, logs, Git, or evidence.

Only these metadata fields may appear in a sanitized receipt:

- fixed environment, database, role, Secret, and source path/key names;
- target UID, resourceVersion, generation, and StaticSecret generation;
- Infisical revision/ETag metadata without bodies or tokens;
- DatabaseRole applied/observed-generation and CNPG password-status metadata;
- sanitized timestamps and boolean results such as `successor_auth=true`.

Receipts must not contain password or username values, Secret `.data` or base64,
connection URLs, request/response bodies, bearer tokens, hashes, SQL output, or
provider error bodies. Plaintext residue must be zero before completion. An
ambiguous write may retain only an explicitly approved encrypted pending bundle
bound to the exact scope, expected revision, and run; it must never trigger a blind
retry.

## Infisical CAS gate

Official Infisical documentation was reviewed on 2026-08-21. The ordinary update is
`PATCH /api/v3/secrets/raw/{secretName}` using a Universal Auth bearer token, but the
published contract contains **NO DOCUMENTED CAS**: no expected revision, ETag,
`If-Match`, stale-write conflict status, or transactional bulk guarantee. Secret
history/rollback is not a concurrency primitive. No apply-capable lane may be
created unless Infisical supplies a vendor-confirmed CAS contract or a separately
reviewed external serialization design is explicitly accepted. A returned revision
alone is not proof of CAS.

A future writer must update exactly one selected password key per invocation,
preserve the fixed username, preserve the other 14 source keys, and verify a new
authoritative revision. Required stop results are:

| Condition | Required result |
|---|---|
| expected revision conflict | `CAS-CONFLICT-STOP` |
| timeout/connection loss after submission | `CAS-UNKNOWN-STOP` |
| malformed response or missing authoritative revision | `CAS-UNKNOWN-STOP` |
| partial or ambiguous key update | `PARTIAL-STOP` |
| any unrelated key/target/source change | `SCOPE-STOP` |
| any unknown writer or revision drift | `OWNER-STOP` |

The 15-key bootstrap uploader is not a CAS writer and is forbidden. No broad batch
request, implicit rotation flag, blind retry, or direct Kubernetes Secret update is
acceptable. If the provider cannot prove conditional semantics and unrelated-key
preservation, the operation remains blocked.

## Infisical Operator synchronization

The Infisical Operator remains the sole Kubernetes Secret value owner. A future
rotation lane must not patch or apply either target Secret directly. The existing
StaticSecret identity is `shared-postgresql-infisical-secrets`; its source contract
uses a one-hour refresh interval with `instantUpdates: false`. After a successful
CAS, a future lane must wait at least two refresh intervals, require current
StaticSecret reconciliation, preserve the target Secret UID, observe a resourceVersion
advance, and verify exact type/key/label/owner metadata.

Successor equality may be checked only inside a protected no-output verifier. A
metadata/resourceVersion change without protected successor equality is not
acceptance. Any unexpected UID, generation, owner, target, or StaticSecret state is
`OWNER-STOP`. Direct Secret patch, apply, delete, or replacement is forbidden.

## CNPG Secret-type decision gate

Official CloudNativePG v1.30 documentation, controller/API source, and exact live
status were reviewed on 2026-08-21. Documentation shows a same-Namespace
`kubernetes.io/basic-auth` Secret with `username` and `password`, but the pinned
DatabaseRole controller validates the keys rather than enforcing `Secret.type`.
Both live DatabaseRoles are applied against the current `Opaque` targets. Updating
the Secret rotates the existing role in place, and convergence is proven when
DatabaseRole `status.secretResourceVersion` matches the target and `applied=true`.
The `Opaque` versus documented `basic-auth` difference remains source-normalization
drift for separate review, but it is not itself a rotation blocker. No Secret-type
or DatabaseRole mutation is authorized by this contract.

Any future lane must require DatabaseRole `status.applied=true`,
current observed generation, matching post-sync Secret resourceVersion,
DatabaseRole Secret resourceVersion and a Ready cluster. These are acceptance gates, not runtime
claims in this source-only contract.

## Successor, revocation, and rollback order

1. Bind clean canonical Git, exact source hashes, fixed scope, target metadata,
   StaticSecret identity, DatabaseRole mapping, expected Infisical revision/ETag,
   backup receipt, and Ready CNPG metadata without reading values.
2. Create encrypted predecessor custody and generate the protected successor.
3. Perform the official conditional source write for only the selected password
   key. Stop on conflict, ambiguity, partial update, or scope drift.
4. Wait for Operator reconciliation and verify target metadata plus protected
   successor equality. Never patch the target Secret directly.
5. Verify CNPG status and protected successor authentication to only its own
   database. Run negative checks for opposite-environment databases, CristexHub,
   Keycloak, `CREATE DATABASE`, `CREATE ROLE`, foreign `SET ROLE`, and public schema
   creation. These checks are not authorized by this source-only document.
6. Perform one protected predecessor authentication check. Only explicit
   authentication failure is revocation evidence; authorization denial is not.
7. Destroy plaintext custody after the approved rollback window and emit only a
   sanitized receipt. Existing Infisical history is not purged.

Before CAS, discard the successor custody without remote change. After CAS, a
protected predecessor restore is permitted only when the current source revision
is exactly the recorded successor revision and an explicit emergency approval
exists. A revision mismatch or ambiguous response is `CAS-UNKNOWN-STOP`; preserve
the encrypted bundle and do not overwrite anything. Never delete Secrets, CRs,
roles, databases, PVCs, or Infisical history as routine rollback.

## Broad-lane prohibition and apply boundary

The following remain forbidden: the 15-key bootstrap uploader; the seven-target
Infisical StaticSecret; the all-consumer PostgreSQL provisioning wrapper; the
all-consumer CloudNativePG Database/DatabaseRole source; existing database action
plugins; direct Secret writes; SQL role/database mutation; Argo sync; workload
rollouts; NetworkPolicy changes; route changes; and any delete/recreate path.

This contract intentionally has no executable files, no check/apply wrapper, no
runtime contact, and no provider or cluster operation. The apply gate is:

`blocked-until-infisical-concurrency-and-dedicated-writer`

Unblocking additionally requires dedicated no-output writer review, protected
predecessor custody review, exact successor authentication and negative tests, and
separate PostgreSQL ACL/NetworkPolicy acceptance. Credential rotation does not
repair the existing `INHERIT`, broad PUBLIC privileges, missing PostgreSQL
NetworkPolicy, or unaccepted broad-lane provenance.

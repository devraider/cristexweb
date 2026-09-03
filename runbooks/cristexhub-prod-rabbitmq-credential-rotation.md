# CristexHub PROD RabbitMQ successor-user rotation

Status: **SOURCE-ONLY DESIGN / NOT RUN / BLOCKED** (the check-only preflight exists; the writer and cutover remain blocked).

This runbook is the canonical value-free design for a future guarded rotation of
only the CristexHub PROD RabbitMQ consumer identity. The separate executable
lane is strictly a metadata-only check; it performs no runtime mutation. No
Infisical value, Kubernetes Secret data, password, hash, token, URL credential,
or management response may be read, generated, copied, logged, or committed by
this source-only lane.

The exact rotation contract is defined in this runbook and its offline test.
The existing RabbitMQ bootstrap source remains present-only and immutable; this
plan must not be implemented by adding a rotation flag to that bootstrap path.

The source-value writer lane is currently **ABSENT / NOT IMPLEMENTED**. The
repository has a separate guarded metadata-only preflight at
`ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation`, but it has no
writer or mutation path. There is no dedicated rotation identity and no proven
concurrency/CAS protocol for updating either `/shared-services/rabbitmq` or
`/cristexhub/prod/runtime`. The existing bootstrap and read-only materialization
contracts must not be reused as an implicit writer. No execution is possible
until a separately reviewed writer proves its endpoint, authentication scope,
expected-revision/conditional-write behavior, preservation of unrelated keys,
and sanitized receipts.

## Frozen scope

Only these identities and consumers are in scope:

- broker Namespace: `shared-services`;
- vhost: `/cristexhub-prod`;
- Infisical source: environment `prod`, path `/shared-services/rabbitmq`;
- existing Infisical target metadata: `shared-rabbitmq-cristexhub-prod` with
  `username`, `password`, and `passwordHash` keys;
- derived application source: `/cristexhub/prod/runtime`, key `RABBITMQ_URL`;
- consumers: `cristexhub-prod/backend` and `cristexhub-prod/celery-worker`.

No administrator, DEV, MongoDB, PostgreSQL, Redis, OIDC, GHCR, TLS, Keycloak,
RabbitMQ definitions outside this vhost, Namespace, PVC, database, public route,
or unrelated workload is in scope.

## Implemented check-only source closure

The only executable entrypoint is:

```text
ansible/bin/check-cristexhub-prod-rabbitmq-credential-rotation check
```

It is a one-host, `--check --diff` wrapper bound to the canonical repository,
protected inventory, direct k3s administrator kubeconfig, exact role/playbook/
action/library/policy hashes, and a single-use attestation. Its role performs
metadata-only Kubernetes queries, requests Secret `PartialObjectMetadata` rather
than ordinary Secret JSON, checks Infisical source and runtime paths plus
resourceVersions, checks Operator/Argo/backend/Celery readiness, and runs only
fixed `rabbitmq-diagnostics`/`rabbitmqctl list_*` queries through the broker Pod.
The action plugin strips command output and rejects credential-bearing commands;
all tasks use `no_log`. It never creates users, changes permissions, writes
Infisical, patches Kubernetes Secrets, restarts consumers, deletes a predecessor,
or applies definitions.

The check deliberately ends with `SOURCE_ONLY_STOP`: the source writer, dual-path
expected-revision/CAS protocol, encrypted definitions backup/readback and
isolated restore proof are not available. A successful metadata preflight is not
rotation authorization. Predecessor permission removal/deletion remains a
separate explicitly approved operation, and queued-message recovery is never
claimed by definitions recovery.

The process and source checks establish a boundary around the canonical wrapper,
controller, and files for this invocation; they do not defend against a malicious
process that already runs as the trusted controller UID (`paul`) and can alter or
observe those files or its descendants. That same-UID case is outside the claimed
integrity boundary and requires host-level isolation/incident response rather than
an assertion that this check-only lane provides protection.

## Identity discrepancy is a hard preflight stop

The architecture policy names `cristexhub_prod_rabbitmq` as the canonical PROD
principal, while current runtime evidence reported `cristexhub_prod_user`. The
source Secret intentionally exposes a username key rather than a value in Git.
A future guarded check must resolve the current identity from metadata only and
must stop with `UNKNOWN-STOP` if the source, target metadata, broker metadata, or
protected runtime contract disagree. It must never silently rename the current
user or infer a username from a Secret value.

For the reviewed successor plan, the canonical successor identity is the exact
non-secret username `cristexhub_prod_rabbitmq`. It must be absent before the
rotation begins. If that identity already exists, or if the observed predecessor
is not the separately verified current user, the lane stops for an explicit
identity decision. The predecessor remains untouched until all successor and
application acceptance checks pass.

## Candidate permission contract — not yet proven

The following is a **candidate least-privilege table**, not a statement of the
current broker contract and not an authorization to change it. Current source/live
evidence has a different principal and broad expressions; the predecessor is not
asserted to satisfy this table. Exact Celery exchange, queue, reply, event, and
pidbox resource names required by the deployed worker are **UNPROVEN** until a
fresh live positive/negative probe records them without values. In particular, the
candidate table must not be applied merely because its strings look narrower:

| field | candidate value |
|---|---|
| vhost | `/cristexhub-prod` |
| configure | `^(default|high_priority|low_priority)$` |
| write | `^default$` |
| read | `^(default|high_priority|low_priority)$` |

A future lane must first inventory the actual Celery declarations and prove the
smallest exact permission set with a protected AMQPS probe. It must verify effective
broker permissions from metadata before and after cutover, and must not grant
administrator tags, user/vhost/policy administration, cross-vhost access, or a
pattern that merely excludes a literal asterisk. No wildcard or broader pattern is
allowed once the live probe establishes the final contract. The candidate table becomes a
contract only after that live probe passes for both required producer/consumer
flows; until then, permission acceptance is **NOT RUN / BLOCKED**.

## Required overlap and cutover sequence

The following is a design sequence, not an execution authorization:

1. **Read-only preflight.** Bind a clean canonical checkout, trusted source
   hashes, one approved host, exact kubeconfig, healthy broker, Argo
   `Synced/Healthy` state, and the exact source/target metadata. Inspect only
   names, types, labels, annotations, resourceVersions, source key names, vhost,
   user names, permissions, and readiness. Never inspect `.data` or values.
2. **Recovery gate (currently unavailable).** A fresh encrypted RabbitMQ
   definitions/policies backup, immutable readback receipt, and isolated
   definitions-restore rehearsal are required, but they are currently
   **NOT RUN / BLOCKED**. Definitions recovery does not recover queued messages.
   Refuse the rotation while these receipts, message-recovery disposition, source
   revision, or broker identity are unknown.
3. **Protected successor preparation.** Generate the successor password and
   password hash only inside a protected, mode-0600, cleanup-first custody
   boundary. Keep the successor username fixed as
   `cristexhub_prod_rabbitmq`; never place values in argv, environment, logs,
   plans, diffs, or evidence. The pending bundle must be encrypted before any
   remote write and must support safe interruption without plaintext residue.
4. **Broker overlap (restart behavior is unproven).** Through a separately
   reviewed, exact RabbitMQ rotation lane, create the successor with no
   administrator tag and apply only the permission contract after the live Celery
   probe passes. Do not assume the overlap survives a broker/StatefulSet restart:
   current definitions generation and one-target Secret ownership do not prove
   that both users, passwords, and permissions persist across restart or
   reconciliation. A future lane must either prove restart persistence before
   relying on overlap or refuse all restarts during the overlap window. Do not
   perform this step through the immutable bootstrap StatefulSet or by placing a
   password in `rabbitmqctl` arguments.
5. **Successor acceptance.** Prove protected AMQPS authentication to
   `/cristexhub-prod`, declaration/use of the resource set recorded by the live
   Celery probe, and denial of DEV-vhost, user-management, vhost-management, and
   policy-management operations. Confirm exactly one Ready broker and no public
   management exposure. A user record or Secret resourceVersion change alone is
   not acceptance. A successful login followed by a denied operation is an
   **authorization/permission denial**, not proof that the credential is revoked.
6. **Infisical application cutover (writer and CAS unavailable).** This step is
   design-only and cannot run today. A future dedicated writer must update the
   protected RabbitMQ source and derived `RABBITMQ_URL` through an explicitly
   selected API with an expected revision/conditional write. It must prove that
   unrelated keys are preserved and that a timeout or ambiguous response is
   `UNKNOWN-STOP`; a one-key request or returned revision does not establish
   atomicity or CAS. The Infisical Operator remains the Kubernetes Secret value
   owner; never write `cristexhub-prod-runtime` directly.
7. **Consumer cutover.** Only after the source writer and reconciliation evidence
   pass may a future lane reconcile the protected PROD backend and Celery consumers
   through their reviewed owner path. Wait for both Deployments to be Ready, verify
   backend health and Celery broker readiness, and require Argo `Synced/Healthy`.
   Readiness of old pods is insufficient: require a bounded rollout, new Pod UIDs,
   and broker connection metadata proving the new consumers use the successor
   principal before predecessor revocation. Do not restart DEV, frontend, Redis,
   oauth2-proxy, or unrelated services. Keep the predecessor active during this
   overlap window, but do not assume that state survives a broker restart.
8. **Old-user revocation — separate permission denial from authentication
   revocation.** After private application acceptance and the reviewed overlap
   interval, first remove the predecessor's vhost permissions and prove that a
   still-authenticated predecessor credential receives authorization denial. This
   does **not** prove authentication revocation. Only through a separate explicit
   broker approval may the predecessor user/password be deleted or cleared; then a
   fresh isolated AMQPS login must fail authentication. Recheck that the successor
   alone has the reviewed permission contract and that cross-vhost and
   administration negatives still pass. No destructive revocation is automatic.
9. **Custody completion.** Retain only encrypted recovery material explicitly
   required by the backup policy. Remove plaintext temporary material, rejected
   bundles, and transient credentials. Record sanitized timestamps, resource
   identities, permission-contract results, readiness, and revocation outcome only.

## Failure, rollback, and partial-state boundaries

Cross-system rotation is **NOT ATOMIC**. Broker users/permissions, Infisical source
keys, generated Kubernetes targets, consumer processes, and Argo reconciliation are
different state machines. A stop or timeout can leave a partial or mixed state (for
example, successor broker user created but source unchanged, source changed but
one consumer unreconciled, or predecessor permissions removed while authentication
remains possible). Every stage requires a sanitized receipt and an explicit
resource-version/revision observation; an ambiguous response is `UNKNOWN-STOP`, not
a blind retry.

If any source revision, writer capability, CAS result, user identity, permission,
backup receipt, broker readiness, target reconciliation, or application probe is
unknown, stop with `UNKNOWN-STOP`. The predecessor is not an assumed rollback
artifact: no predecessor URL/password is read, reconstructed, or presumed to be
available from a Kubernetes Secret or source reference. A future lane must create
and verify protected predecessor recovery custody **before** any source cutover, or
must declare rollback unavailable and stop.

The Infisical source-writer lane and conditional/CAS protocol are currently absent;
therefore no source rollback or application cutover is executable. Before predecessor
permissions are removed, a future cutover may restore a proven protected predecessor
bundle only through the approved writer and verified expected revision. After those
permissions are removed, restoring source values alone is unsafe and insufficient:
first restore the predecessor's exact broker permission contract through a separately
approved broker operation, then verify it, or stop without changing application
source. Preserve the successor for diagnosis and never mutate PVCs or use blind broker
rollback. After predecessor authentication revocation, recovery requires a
separately reviewed credential operation; this plan has no automatic rollback or
delete path.

## Existing-source boundaries

- `ansible/bin/bootstrap-rabbitmq` and `ansible/plugins/action/rabbitmq_guarded_k8s.py`
  remain a value-free present-only bootstrap closure. They must not gain
  rotation, overlap, restart, or predecessor-deletion arguments.
- `ansible/files/components/infisical-rabbitmq-secrets/` remains the source-only
  four-target Infisical contract. Its admission boundaries must not be widened to
  accept arbitrary target names or values.
- The derived PROD runtime seam remains the sole owner path for
  `RABBITMQ_URL`; no direct Kubernetes Secret patch is permitted.
- The current executable helper, role, action plugin, wrapper, and playbook are
  a separate hash-bound **check-only** source closure with its own approval,
  no-log checks, metadata-only queries, and no overlap/revocation mode. It has
  no writer, apply, delete, or source-cutover path. Any future executable writer
  must be a separate hash-bound source closure with its own approval,
  concurrency binding, and explicit overlap/revocation mode.

## Current blockers and acceptance evidence required before public routing

RabbitMQ definitions backup/readback and isolated definitions restore are currently
**NOT RUN / BLOCKED**; policy evidence records
`isolated_rabbitmq_definitions_restore_proved: false` and
`rabbitmq_message_reconciliation_proved: false`. No queued-message recovery,
measured RPO/RTO, or production recovery acceptance is available. These are hard
preconditions, not merely post-rotation evidence.

A future execution must additionally provide sanitized evidence for exact successor
and predecessor identity handling, the live Celery resource probe, restart
persistence (or an explicit no-restart overlap boundary), candidate permission
contract, protected Infisical source revision and proven CAS/conditional write,
generated target reconciliation, backend/Celery readiness, AMQPS positive and
cross-vhost/admin negative tests, distinct authorization-denial and authentication-
revocation results, protected predecessor recovery custody, no plaintext residue,
definitions backup/readback and isolated restore, and Argo `Synced/Healthy`. Until
all evidence exists, RabbitMQ credential rotation and any public PROD route remain
**NOT RUN / BLOCKED**.

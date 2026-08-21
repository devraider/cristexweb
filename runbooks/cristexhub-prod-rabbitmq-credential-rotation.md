# CristexHub PROD RabbitMQ successor-user rotation

Status: **SOURCE-ONLY DESIGN / NOT RUN / BLOCKED**.

This runbook is the canonical value-free design for a future guarded rotation of
only the CristexHub PROD RabbitMQ consumer identity. It adds no executable
rotation lane and performs no runtime mutation. No Infisical value, Kubernetes
Secret data, password, hash, token, URL credential, or management response may
be read, generated, copied, logged, or committed by this source-only change.

The exact rotation contract is defined in this runbook and its offline test.
The existing RabbitMQ bootstrap source remains present-only and immutable; this
plan must not be implemented by adding a rotation flag to that bootstrap path.

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

## Exact permission contract

Both the successor during overlap and the predecessor while it is retained must
have only this vhost-scoped permission contract. No wildcard or broader pattern is
allowed:

| field | exact value |
|---|---|
| vhost | `/cristexhub-prod` |
| configure | `^(default|high_priority|low_priority)$` |
| write | `^default$` |
| read | `^(default|high_priority|low_priority)$` |

The lane must verify the effective broker permissions by metadata-only output
before and after cutover. It must not grant administrator tags, user/vhost/policy
administration, cross-vhost access, or a permission pattern that merely excludes a
literal asterisk. The exact contract is required for the successor, and the old
user is removed only after its permissions are removed and predecessor
authentication is proven to fail.

## Required overlap and cutover sequence

The following is a design sequence, not an execution authorization:

1. **Read-only preflight.** Bind a clean canonical checkout, trusted source
   hashes, one approved host, exact kubeconfig, healthy broker, Argo
   `Synced/Healthy` state, and the exact source/target metadata. Inspect only
   names, types, labels, annotations, resourceVersions, source key names, vhost,
   user names, permissions, and readiness. Never inspect `.data` or values.
2. **Recovery gate.** Require a fresh encrypted RabbitMQ definitions/policies
   backup and immutable readback receipt. Definitions recovery does not recover
   queued messages. Refuse the rotation when the receipt, source revision, or
   broker identity is unknown.
3. **Protected successor preparation.** Generate the successor password and
   password hash only inside a protected, mode-0600, cleanup-first custody
   boundary. Keep the successor username fixed as
   `cristexhub_prod_rabbitmq`; never place values in argv, environment, logs,
   plans, diffs, or evidence. The pending bundle must be encrypted before any
   remote write and must support safe interruption without plaintext residue.
4. **Broker overlap.** Through a separately reviewed, exact RabbitMQ rotation
   lane, create the successor with no administrator tag and apply exactly the
   permission table above. Retain the predecessor with its exact permission
   contract. Do not perform this step through the immutable bootstrap
   StatefulSet or by placing a password in `rabbitmqctl` arguments.
5. **Successor acceptance.** Prove protected AMQPS authentication to
   `/cristexhub-prod`, declaration/use of only the reviewed default exchange and
   queue set, and denial of DEV-vhost, user-management, vhost-management, and
   policy-management operations. Confirm exactly one Ready broker and no public
   management exposure. A user record or Secret resourceVersion change alone is
   not acceptance.
6. **Infisical application cutover.** After successor acceptance, update only
   the protected RabbitMQ source keys required to represent the successor and
   then the derived `RABBITMQ_URL` at `/cristexhub/prod/runtime`. The Infisical
   Operator remains the Kubernetes Secret value owner; never write
   `cristexhub-prod-runtime` directly. Preserve every unrelated runtime key and
   verify source revision/concurrency before and after reconciliation without
   outputting values.
7. **Consumer cutover.** Reconcile only the protected PROD backend and Celery
   consumers through their reviewed owner path. Wait for both Deployments to be
   Ready, verify backend health and Celery broker readiness, and require Argo
   `Synced/Healthy`. Do not restart DEV, frontend, Redis, oauth2-proxy, or shared
   unrelated services. Keep the predecessor active during this overlap window.
8. **Old-user revocation.** After private application acceptance and the reviewed
   overlap interval, remove the predecessor's vhost permissions, verify its
   authentication fails, then delete/revoke that predecessor through the explicit
   broker/Infisical rotation approval. Recheck that the successor alone has the
   exact permission contract and that cross-vhost and administration negatives
   still pass. No destructive revocation is automatic.
9. **Custody completion.** Retain only the encrypted recovery receipt required by
   the backup policy. Remove plaintext temporary material, rejected bundles, and
   transient credentials. Record sanitized timestamps, resource identities,
   permission-contract results, readiness, and revocation outcome only.

## Failure and rollback boundaries

If any source revision, user identity, permission, backup receipt, broker
readiness, target reconciliation, or application probe is unknown, stop with
`UNKNOWN-STOP`. During overlap, the predecessor is the explicit recovery path;
never revoke it before successor acceptance. If application cutover fails, restore
only the protected predecessor runtime source through a separately approved
Infisical operation, preserve the successor for diagnosis, and do not delete
users, mutate PVCs, or use blind broker rollback. After predecessor revocation,
recovery requires a separately reviewed successor credential operation; this plan
has no automatic rollback or delete path.

## Existing-source boundaries

- `ansible/bin/bootstrap-rabbitmq` and `ansible/plugins/action/rabbitmq_guarded_k8s.py`
  remain a value-free present-only bootstrap closure. They must not gain
  rotation, overlap, restart, or predecessor-deletion arguments.
- `ansible/files/components/infisical-rabbitmq-secrets/` remains the source-only
  four-target Infisical contract. Its admission boundaries must not be widened to
  accept arbitrary target names or values.
- The derived PROD runtime seam remains the sole owner path for
  `RABBITMQ_URL`; no direct Kubernetes Secret patch is permitted.
- Any future executable helper, role, action plugin, wrapper, or playbook must be
  a separate hash-bound source closure with its own approval, no-log checks,
  concurrency binding, and explicit overlap/revocation mode. This runbook adds
  none of those runtime artifacts.

## Acceptance evidence required before public routing

A future execution must provide sanitized evidence for exact successor and
predecessor identity handling, the permission table, overlap, protected Infisical
source revision and generated target reconciliation, backend/Celery readiness,
AMQPS positive and cross-vhost/admin negative tests, old-user authentication
failure after revocation, no plaintext residue, definitions backup/readback, and
Argo `Synced/Healthy`. Until that evidence exists, RabbitMQ credential rotation
and any public PROD route remain **NOT RUN / BLOCKED**.

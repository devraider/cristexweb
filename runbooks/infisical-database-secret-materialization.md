# Infisical database Secret materialization seam

## Status and boundary

This is a source-only, separately guarded seam for the selected Infisical
Kubernetes Operator `v0.11.7`. It has not contacted a host, Kubernetes API,
Infisical account, registry, or Secret store. It adds no committed or runtime Secret value, credential, Argo Application,
workload, route, PVC, database, or runtime approval. The protected source-only
value lane generates/uploads the database administrator/TLS and seven logical-
consumer values. The Operator's 44-object closure is applied/idempotent, but the
database value lane and this materialization seam remain **NOT RUN/BLOCKED**.

The seam has exactly 15 Ansible-owned value-free objects:

- one shared `shared-services/infisical-cloud` Connection;
- two same-Namespace Universal Auth references and two StaticSecrets;
- four fail-closed ValidatingAdmissionPolicies plus four `Deny` bindings; and
- one exact additive Secret-writer Role plus RoleBinding.

The StaticSecrets materialize exactly eleven orphaned target Secrets, but those
Secret objects and their values are generated only by the future Operator sync and
are not committed here:

| Target Secret | Type | Exact keys |
|---|---|---|
| `shared-postgresql-admin` | `Opaque` | `username`, `password` |
| `shared-postgresql-tls` | `kubernetes.io/tls` | `ca.crt`, `tls.crt`, `tls.key` |
| `shared-mongodb-auth` | `Opaque` | `username`, `password` |
| `shared-mongodb-tls` | `Opaque` | `ca.crt`, `tls.pem` |
| `shared-postgresql-cristexhub-dev` | `Opaque` | `username`, `password` |
| `shared-postgresql-cristexhub-prod` | `Opaque` | `username`, `password` |
| `shared-postgresql-reactive-resume-dev` | `Opaque` | `username`, `password` |
| `shared-postgresql-reactive-resume-prod` | `Opaque` | `username`, `password` |
| `shared-postgresql-keycloak` | `Opaque` | `username`, `password` |
| `shared-mongodb-cristexhub-dev` | `Opaque` | `username`, `password` |
| `shared-mongodb-cristexhub-prod` | `Opaque` | `username`, `password` |

These contracts are identical to the canonical no-log
[`stateful_database_secret_contract`](../ansible/plugins/action/stateful_database_secret_contract.py)
validator. Every target is explicitly templated, labelled
`app.kubernetes.io/managed-by: infisical`,
`app.kubernetes.io/part-of: shared-databases`, and
`cristex.io/value-owner: infisical-cloud`, with `creationPolicy: Orphan`.
Existing foreign, wrong-type, wrong-key, immutable, non-orphan, or drifted targets
are rejected before any source mutation.

## Fixed human-created identifiers

A human operator must create the two runtime Universal Auth credential Secrets
out of band before a separately approved check/apply. Database administrator/TLS
and seven logical-consumer values are generated and uploaded only by the protected
source-only value lane; the materializer never reads values into Git, source hashes,
Ansible output, command arguments, or review artifacts.

- Infisical project slug: `cristexweb-infrastructure`.
- Infisical environment slug: `prod` (this is an Infisical Cloud slug only; it does not activate Kubernetes `cristexhub-prod`).
- PostgreSQL path: `/shared-services/postgresql`.
- MongoDB path: `/shared-services/mongodb`.
- `shared-services/Secret/shared-postgresql-infisical-universal-auth`, type
  `Opaque`, exact keys `clientId` and `clientSecret`.
- `shared-services/Secret/shared-mongodb-infisical-universal-auth`, type
  `Opaque`, exact keys `clientId` and `clientSecret`.
- Both credential Secrets have exactly `app.kubernetes.io/managed-by=ansible`,
  `app.kubernetes.io/part-of=infisical-operator`,
  `cristex.io/component=infisical-runtime-auth`, and
  `cristex.io/value-owner=infisical-cloud`; they are non-immutable with no owner
  references or binary data.
- PostgreSQL source keys: `POSTGRESQL_ADMIN_USERNAME`,
  `POSTGRESQL_ADMIN_PASSWORD`, `POSTGRESQL_TLS_CA_CRT`, `POSTGRESQL_TLS_CRT`,
  `POSTGRESQL_TLS_KEY`, `POSTGRESQL_CRISTEXHUB_DEV_USERNAME`,
  `POSTGRESQL_CRISTEXHUB_DEV_PASSWORD`, `POSTGRESQL_CRISTEXHUB_PROD_USERNAME`,
  `POSTGRESQL_CRISTEXHUB_PROD_PASSWORD`,
  `POSTGRESQL_REACTIVE_RESUME_DEV_USERNAME`,
  `POSTGRESQL_REACTIVE_RESUME_DEV_PASSWORD`,
  `POSTGRESQL_REACTIVE_RESUME_PROD_USERNAME`,
  `POSTGRESQL_REACTIVE_RESUME_PROD_PASSWORD`, `POSTGRESQL_KEYCLOAK_USERNAME`,
  and `POSTGRESQL_KEYCLOAK_PASSWORD`.
- MongoDB source keys: `MONGODB_ADMIN_USERNAME`, `MONGODB_ADMIN_PASSWORD`,
  `MONGODB_TLS_CA_CRT`, `MONGODB_TLS_PEM`,
  `MONGODB_CRISTEXHUB_DEV_USERNAME`, `MONGODB_CRISTEXHUB_DEV_PASSWORD`,
  `MONGODB_CRISTEXHUB_PROD_USERNAME`, and `MONGODB_CRISTEXHUB_PROD_PASSWORD`.

The PostgreSQL and MongoDB Auth objects are separate identities and each points to
its own same-Namespace credential Secret. They both reference the one
`shared-services/infisical-cloud` Connection. No client ID, client secret, project
ID, token, database credential, certificate, private key, or generated value is
committed.

## Admission and RBAC boundary

The Secret VAP is fail-closed only for the eleven exact target names in
`shared-services`. For those targets, validation requires the exact Operator
ServiceAccount, namespace, name/type/key set, three ownership labels, empty binary
data, and no owner references. A non-target Secret name skips this policy. Because
the current writer Role grants unrestricted Secret `create` and broad reads, this
VAP does **not** prove that the Operator cannot create or read an unreviewed Secret.
Therefore the seam remains runtime-blocked and cannot be reused for Reactive Resume
activation until RBAC and admission are redesigned and negative-tested. It does
prove only that:

- a foreign writer cannot write an exact target Secret; and
- the database policy does not match `argocd` namespace writes.

The existing Argo Secret VAP uses the same namespace plus
`(operator identity OR exact Argo target-name set)` match conditions and requires the
Operator identity in validation. This prevents the Argo policy from blocking the
Operator's database writes in `shared-services`, while preventing the database
policy from affecting `argocd`.

A second VAP denies `InfisicalSecret`, `InfisicalPushSecret`, and
`InfisicalDynamicSecret` in `shared-services`. The StaticSecret VAP permits only
the two exact names and requires either the guarded `system:admin` bootstrap writer
or an Operator update with an unchanged `spec`; it then enforces same-Namespace Auth
references, project/environment/path pairs, `recursive: false`, explicit empty
`tagSlugs`, no `projectId`, fixed sync options, and the exact eleven target
identities/types/orphan policies/metadata. PostgreSQL uses seven targets
(administrator, TLS, and five logical-consumer credentials), while MongoDB uses
four (administrator, TLS, and two logical-consumer credentials). This blocks
foreign spec mutation while
allowing controller finalizer/status maintenance. `template.data` remains an
intentionally opaque CRD field and is enforced by the
hash-bound manifests and action guard rather than dereferenced from CEL.

The additive Role grants the trusted controller Secret `get/list/watch`, Secret
`create`, and `update` restricted by `resourceNames` to the eleven targets. It grants
only workload `list/watch` for Deployments, DaemonSets, and StatefulSets, which the
reviewed controller uses for reload decisions. It grants no Secret `patch/delete`
and no workload write or delete. The RoleBinding is to the existing
`shared-services/infisical-operator-controller` ServiceAccount.

## Guarded sequence

Only this non-passthrough entrypoint is authorized:

```text
ansible/bin/bootstrap-infisical-database-secrets check
ansible/bin/bootstrap-infisical-database-secrets apply
```

The wrapper supplies the pinned repository controller, clean environment, exact
inventory, `--diff`, one-host limit, present-only approval, and a mode-`0600`
single-run attestation. Direct playbook use, passthrough arguments, tags,
skip-tags, task selection, and sudo are rejected. The action plugin binds the exact
role task source, five argument fields, 15 canonical object hashes, source bytes,
and the sorted identity-set SHA-256.

The role verifies service health, the established `shared-services` Namespace,
protected kubeconfig metadata, both credential Secret metadata contracts, all eleven
existing target pre-state contracts, all six Infisical CRDs, absence of alternate
target-producing CRs, and canonical-only StaticSecret inventory before mutation.
It applies admission policies first, waits for `TypeChecking`, applies bindings and
waits for effective `Deny`, applies the additive Role/Binding, then reconciles the
Connection, both Auths, and both StaticSecrets. Apply waits for current-generation
`IsReady=True` on Connection/Auths and current-generation
`LastReconcileStatus=True` plus `LastSuccessfulReconcileAt=True` on StaticSecrets.
It verifies exact generated target Secret metadata without logging values.

## Offline validation and rollback

No live check/apply, credential creation, Secret materialization, Infisical sync,
rotation, recovery, database provisioning, StatefulSet readiness, idempotence; the
seam runtime remains **NOT RUN/BLOCKED**. The following offline source claims do not
change that boundary:
NetworkPolicy enforcement, logical authorization, backup/restore, or Argo handoff
is claimed. Before runtime, rollback is a Git revert of this source-only seam; it
never deletes generated orphaned Secrets. After a future runtime approval, any
Secret or source rollback requires a separately reviewed exact change preserving
values and state.

Focused and full offline validation commands are recorded in
[`specs/k3s-iac-foundation/testcases.md`](../specs/k3s-iac-foundation/testcases.md).

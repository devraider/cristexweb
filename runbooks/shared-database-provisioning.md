# Shared database logical provisioning

## Source-only status

**SOURCE-ONLY GUARDED LANE — RUNTIME, BACKUP, AND RESTORE BLOCKED.** This runbook
adds no database, role, user, Secret, PVC, workload, or production state. It defines
an Ansible-owned, one-shot bootstrap lane that may be considered for a future Ready
PostgreSQL or standalone MongoDB engine only after separate approvals. No command in
this document has been run by this source increment.

Infisical Cloud owns all credential values. The five PostgreSQL consumer Secrets and
two MongoDB consumer Secrets must be precreated Infisical-owned Secrets and must already exist in `shared-services`, be materialized
by the separately reviewed Infisical seam, and carry the exact `Opaque`
`username`/`password` contract and labels:

```text
app.kubernetes.io/managed-by=infisical
app.kubernetes.io/part-of=shared-databases
cristex.io/value-owner=infisical-cloud
```

The reviewed Infisical source seam uses project `cristexweb-infrastructure`,
environment `prod`, and `/shared-services/postgresql` or
`/shared-services/mongodb`; `prod` is the Infisical Cloud environment slug
only and does not activate Kubernetes `cristexhub-prod`. Those identifiers carry
no values or permission to contact Infisical. The lane never creates, generates, exports, logs, rotates, or
places credential values in argv. Missing, wrong-type, wrong-key, foreign, short, or username-mismatched
Secrets fail closed. Password rotation is a separate approved operation and is never
inferred from Secret drift.

## Frozen empty reservations

The lane freezes five PostgreSQL and two MongoDB empty reservations. The logical names are fixed and value-free:

| Engine | Consumer | Database | Principal | Required Secret |
|---|---|---|---|---|
| PostgreSQL | CristexHub DEV | `cristexhub_dev` | `cristexhub_dev_owner` | `shared-postgresql-cristexhub-dev` |
| PostgreSQL | CristexHub PROD | `cristexhub_prod` | `cristexhub_prod_owner` | `shared-postgresql-cristexhub-prod` |
| PostgreSQL | Reactive Resume DEV | `reactive_resume_dev` | `reactive_resume_dev_owner` | `shared-postgresql-reactive-resume-dev` |
| PostgreSQL | Reactive Resume PROD | `reactive_resume_prod` | `reactive_resume_prod_owner` | `shared-postgresql-reactive-resume-prod` |
| PostgreSQL | Keycloak | `keycloak` | `keycloak_owner` | `shared-postgresql-keycloak` |
| MongoDB | CristexHub DEV | `cristexhub_dev` | `cristexhub_dev_user` | `shared-mongodb-cristexhub-dev` |
| MongoDB | CristexHub PROD | `cristexhub_prod` | `cristexhub_prod_user` | `shared-mongodb-cristexhub-prod` |

All seven are **empty bootstrap reservations**. PROD remains inactive: this lane
does not create a PROD Namespace, workload, route, migration, application Secret,
traffic path, or acceptance. Reactive Resume and Keycloak workloads are likewise
not deployed by this lane.

## Guarded entrypoints and sequence

Each engine has an independent non-passthrough wrapper. It accepts exactly one mode,
`check` or `apply`, and supplies the repository-pinned controller, clean environment,
`--diff`, the single `crtxweb` limit, a present-only approval, and a mode-`0600`
one-run attestation:

```text
ansible/bin/provision-shared-postgresql check
ansible/bin/provision-shared-postgresql apply
ansible/bin/provision-shared-mongodb check
ansible/bin/provision-shared-mongodb apply
```

Do not append arguments, tags, task-selection controls, internal variables, sudo,
credential values, or a different playbook. Required order for a future approved
run is:

1. Offline source and hash checks.
2. A separate check approval; check is read-only and performs a native state query.
3. A separate first-apply approval after the corresponding engine is Ready and all
   exact Infisical Secrets pass metadata/value-free username checks.
4. A separate idempotence approval; a Ready state must report no logical mutation.
5. Separate live authorization and private network evidence.

The existing engine bootstrap wrappers remain separate. A Ready Pod is a prerequisite,
not permission to run this lane.

## Implementation boundary

The four fixed scripts under
`ansible/files/database-provisioning/` are hash-bound by both action guards and role
defaults. The PostgreSQL scripts use TLS `verify-full`, a CA file, and mode-`0600`
temporary `PGPASSFILE` paths; role passwords enter `psql` only through protected
standard input. The MongoDB scripts use CA-validated TLS and read mounted credential
files inside `mongosh`. No credential value is placed in a Pod environment, process
argument, URI, controller environment, shell trace, or generated source. Output is
reduced to `READY`, `CHANGED:n`,
`BOOTSTRAP_REQUIRED`, or `DRIFT` status markers; values and hashes are suppressed.

Apply first verifies every declared scope. It can create only missing roles/users and
databases in the frozen map. Existing foreign ownership, role/user attribute drift,
credential mismatch, or data-bearing target databases fail closed. A PostgreSQL
role-only interrupted state is repairable only when the role attributes are exact and
the database remains absent; the protected credential is rebound before the missing
empty database is created. It never performs an implicit credential rotation of a
complete scope. PostgreSQL roles are `LOGIN` but `NOSUPERUSER`,
`NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`, `NOREPLICATION`, and `NOBYPASSRLS`;
`PUBLIC` database connect/temporary and schema-create access is revoked, and each
principal receives only its own database/schema grants. MongoDB users receive only
`readWrite` on their own database and no broad or administrative role.

Each apply uses one temporary `database-logical-provisioning` helper Pod and one exact
Ingress/Egress NetworkPolicy in `shared-services`. The policy selects only the helper
and its database, admits helper-to-database traffic, and restricts helper egress to the
exact database port plus TCP/UDP DNS to labeled CoreDNS Pods in `kube-system`; all
other helper egress is denied. The helper uses the already selected engine image digest, exact
Secret references, CA-only TLS material for MongoDB, no service-account token, no
PVC, no host path, a read-only root filesystem, non-root UID/GID `999`, and memory
only temporary storage. The helper and policy names are derived from the one-run
attestation. The action guard refuses arbitrary commands, Secret data, ConfigMaps,
PVCs, Jobs, host paths, mutable images, and foreign names. Cleanup runs in `always`,
reads each exact object, checks both ownership labels and the recorded UID, deletes
only with that UID precondition and `Orphan` propagation, and proves zero helper
Pod/NetworkPolicy residue. A stale helper is a stop condition; selector-based
cleanup is forbidden.

## Authorization evidence required later

The eventual private validation must prove, for every scope:

- TLS positive authentication to the own database and own-schema operation;
- DEV-to-PROD and PROD-to-DEV denial;
- application-to-Keycloak and Keycloak-to-application denial;
- PostgreSQL `CREATE DATABASE` and `CREATE ROLE` denial for every workload role;
- MongoDB bidirectional cross-database denial and user/role-administration denial;
- no broad MongoDB roles (`root`, `readAnyDatabase`, `readWriteAnyDatabase`,
  `dbAdminAnyDatabase`, or `userAdminAnyDatabase`); and
- no unauthorized namespace or direct public endpoint reachability.

NetworkPolicy is only endpoint reachability control and cannot substitute for native
database authorization. Positive/negative live tests, image trust, TLS identity,
Infisical sync/recovery, and idempotence remain unrun.

## Rollback and blocked gates

Rollback is a Git revert or disabling this source path. There is no database/user
rollback operation, no PVC operation, and no deletion path in the roles or action
plugins. Do not delete a database, role, user, PVC, Secret, or StatefulSet as routine
rollback. Existing state or partial creation requires a reviewed recovery decision;
this lane will not reset it.

MongoDB remains standalone and non-authoritative. Replica-set, transaction, HA,
authoritative-data, backup, isolated restore, RPO/RTO, and production acceptance are not
closed. PostgreSQL/MongoDB image trust and pullability, Infisical materialization and
recovery, engine runtime, private TLS/NetworkPolicy enforcement, logical authorization,
Argo handoff, backup, isolated restore, and all check/apply/idempotence results are
**NOT RUN/BLOCKED**. Source validation does not authorize live access.

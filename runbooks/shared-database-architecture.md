# Shared database architecture

## Status

**POLICY ONLY — RUNTIME BLOCKED.** This source-only design selects one PostgreSQL
engine and one MongoDB engine in the future `shared-services` Namespace. It does not
select executable database objects or claim that the Namespace, engines, databases,
users, storage, or backups exist.

The canonical value-free contract is
[`shared-database-architecture.yml`](../ansible/files/policies/shared-database-architecture.yml).
PostgreSQL `17.10` has an existing immutable offline source baseline in the hosted
identity policy, but its trust and recovery are not accepted. MongoDB repository,
version, immutable digest, topology, and trust remain unselected.

## Placement and failure model

The accepted resource-saving model uses exactly one engine of each technology in
`shared-services`:

| Engine | Logical consumers |
|---|---|
| PostgreSQL | CristexHub DEV, CristexHub PROD, Reactive Resume DEV, Reactive Resume PROD, and Keycloak |
| MongoDB | CristexHub DEV and CristexHub PROD |

Keycloak remains a separate deployment. It receives one dedicated PostgreSQL logical
database, owner role, Infisical-owned credential, migration scope, and backup scope;
it receives no separate PostgreSQL engine or PVC and no MongoDB scope. CristexHub
DEV/PROD receive distinct scopes on both shared engines; Reactive Resume DEV/PROD
receive distinct PostgreSQL scopes. Every consumer has separate logical databases,
principals, credentials, migrations, and backups even though the engines are shared.
Application tenants remain application-level concerns inside the environment scope;
they do not receive engines or PVCs.

Future consumers require a reviewed exact policy change. Wildcard, dynamic, default,
or implicit admission is forbidden. Every addition identifies the engine and
consumer, creates dedicated database/principal/Infisical credential/migration/backup
scopes, reviews capacity, adds negative cross-database tests, and updates policy,
tests, and this runbook together.

Both engines are shared failure and contention domains on a single node. Logical
separation does not provide availability, performance, or kernel isolation. Resource,
connection, storage, upgrade, and recovery limits must be reviewed before PROD.

## Authorization contract

### PostgreSQL

Workload roles default to no cross-database access. Future provisioning must revoke
unwanted `PUBLIC` database connection and schema-creation privileges, grant each
principal only its own logical database, and deny workload role/database creation.
Negative tests must prove DEV-to-PROD, PROD-to-DEV, application-to-Keycloak,
Keycloak-to-application, role-creation, and database-creation denials.

### MongoDB

Each environment receives a database-scoped user and no authority over the other
environment. Workload users may not administer users or roles and may not receive
broad built-in roles such as `readAnyDatabase`, `readWriteAnyDatabase`,
`dbAdminAnyDatabase`, `userAdminAnyDatabase`, or `root`. Negative tests must prove
bidirectional cross-database denial and the absence of workload user/role
administration.

NetworkPolicy cannot enforce logical-database isolation because consumers share an
engine endpoint. It can only restrict which workloads reach that endpoint. Database
authorization and functional negative tests remain mandatory.

## Secret and provisioning ownership

Infisical Cloud owns all database credential values. Git may contain only value-free
policy and, after later approval, reviewed references. Workload and Keycloak pods
must never receive the provisioning administrator credential.

The selected ownership direction is an idempotent Ansible bootstrap followed by an
object-by-object Argo handoff. Ansible must use recoverable Infisical-backed
administrator material, prove exact grants with negative tests, and stop reconciling
each handed-off object before Argo starts. The workflow remains unimplemented and
unproved; dual reconciliation is forbidden.

## Exposure boundary

Future `shared-postgresql:5432` and `shared-mongodb:27017` Services are ClusterIP-only.
Ingress, NodePort, LoadBalancer, Cloudflare Tunnel, and any public route are
forbidden. TLS is mandatory and certificate values remain Infisical-owned; exact TLS
identities, selectors, and NetworkPolicy flows remain unselected. No database or
administrative endpoint may become public.

## Storage and recovery blockers

MongoDB topology remains unselected; standalone versus replica-set behavior affects
transactions, upgrade strategy, and application-consistent recovery. The approved
source profile uses NVMe `local-path`, one `ReadWriteOnce` PVC per engine, `40Gi` for
PostgreSQL and `80Gi` for MongoDB, and per-engine requests of `500m` CPU/`1Gi` memory
with limits of `2` CPU/`3Gi` memory. Exact data paths, filesystem ownership, reclaim
behavior, probes, connection limits, and disruption behavior remain unselected.

The canonical [shared backup architecture](shared-stateful-backup-architecture.md)
requires private authenticated operator catalog/retrieval, predictable per-consumer
paths, encrypted timestamped non-destructive off-node copies, integrity verification,
and isolated restore. The approved source profile uses daily archives, 14-day local
and off-node retention, RPO `24h`, RTO `4h`, and independent encryption-key custody.
Exact backup tooling/image, destination identity/folder, staging path, credentials,
and restore implementation remain unknown. Acceptance requires application-consistent PostgreSQL and MongoDB dumps, separate
consumer scopes, and isolated restore proof. PostgreSQL role
and ownership recreation must be proven without leaking credential hashes. A
successful backup job alone is not recovery evidence.

## Executable-source stop gate

No StatefulSet, Deployment, Service, PVC, Secret, Job, CronJob, or NetworkPolicy is
added by this increment. It also adds no Ansible role, playbook, wrapper, Helm values,
Argo Application, Kustomize overlay, route, provider resource, or generated
credential.

Stop before executable source until all of the following are approved or proved:

1. MongoDB immutable source, topology, compatibility, trust, and off-node recovery;
2. PostgreSQL and MongoDB image trust, node pullability, and admission;
3. storage, capacity, security contexts, resources, probes, TLS, and NetworkPolicy;
4. Infisical Universal Auth and administrator credential recovery;
5. one provisioning owner and exact idempotent authorization behavior;
6. backup tooling, destination, key custody, integrity, isolated restore, RPO/RTO;
7. exact Ansible bootstrap ownership and object-by-object Argo handoff;
8. separate check, apply, idempotence, Secret, stateful-service, and runtime approvals.

No host, registry, Kubernetes API, provider, Infisical, Helm, or runtime operation was
authorized or performed for this policy increment.

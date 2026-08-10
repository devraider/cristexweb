# Shared database architecture

## Status

**SOURCE-ONLY DATABASE CLOSURES READY — RUNTIME BLOCKED.** This source-only design
selects one PostgreSQL engine and one standalone MongoDB engine in the future
`shared-services` Namespace. It does not claim that either engine, its Secret
material, databases, users, PVC, or backup exists at runtime. MongoDB is explicitly
non-authoritative and is not an HA, replica-set, transaction, or production-data
acceptance.

The canonical value-free contract is
[`shared-database-architecture.yml`](../ansible/files/policies/shared-database-architecture.yml).
PostgreSQL `17.10` and MongoDB `8.0.28` are bound offline to exact linux/amd64 image
digests. Publisher trust, pullability, compatibility, recovery, and runtime remain
blocked.

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
`dbAdminAnyDatabase`, or `userAdminAnyDatabase`. The bootstrap administrator is used
only by the official image entrypoint to create the initial root user; it is not
available to workloads. Negative tests must prove bidirectional cross-database denial
and the absence of workload user/role administration. The source closure deliberately
uses standalone MongoDB for iteration speed with no current clients; multi-document
transactions, replica-set semantics, HA, and authoritative-data acceptance remain
open decisions.

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
each handed-off object before Argo starts. The separate source-only
[logical provisioning lane](shared-database-provisioning.md) freezes the seven empty
reservations and guarded check/apply wrappers, but its runtime, authorization,
Infisical recovery, backup/restore, and handoff evidence remain blocked; dual
reconciliation is forbidden.

Both bootstrap roles validate the two exact Infisical-owned target Secret objects before
any workload mutation. A canonical-task-bound, no-log action plugin decodes values only
in memory and rejects short credentials, malformed or ambiguous PEM, non-current or weak
certificates/keys, non-CA issuers, missing server-auth EKU, mismatched private keys,
non-direct issuance, and any SAN set outside the exact policy. It does not create,
update, log, or return Secret values. The separate source-only
[Infisical database Secret materialization seam](infisical-database-secret-materialization.md)
now freezes one shared Connection, separate PostgreSQL/MongoDB Auth and Universal Auth
identities, two StaticSecrets, exact eleven engine/per-consumer target contracts,
eight scoped fail-closed VAP/bindings, and additive writer RBAC; its check/apply,
sync, values, and runtime remain
**NOT RUN/BLOCKED**.

## Executable PostgreSQL source closure

[`runbooks/postgresql-bootstrap.md`](postgresql-bootstrap.md) defines the six-object,
present-only guarded closure for `shared-postgresql`: ConfigMap, two NetworkPolicies,
tokenless ServiceAccount, private ClusterIP Service, and one-replica StatefulSet. It
uses the pinned PostgreSQL 17.10 image as UID/GID `999`, a retained `40Gi`
`local-path` PVC, SCRAM-SHA-256, a memory-staged mode-`0600` private key, and probes
that authenticate over CA-validated TLS before proving plaintext rejection. Values
come only from `shared-postgresql-admin` and `shared-postgresql-tls`. The exact server
SAN set is `localhost`, `shared-postgresql.shared-services.svc`, and
`shared-postgresql.shared-services.svc.cluster.local`.

## Executable MongoDB source closure

The dedicated guarded entrypoint
[`ansible/bin/bootstrap-mongodb`](../ansible/bin/bootstrap-mongodb) accepts only
`check` or `apply`; it passes no user arguments through and requires `--diff`, the
one-host limit, a private single-run attestation, established k3s administrator
access, and exact SHA-256-bound manifests. It reconciles only the five committed
objects: a tokenless ServiceAccount, a private `ClusterIP` Service on `27017`, one
one-replica StatefulSet, a default-deny policy, and an exact consumer-ingress policy.
There is no delete path, no PVC manifest, no Ingress, NodePort, LoadBalancer,
Cloudflare Tunnel, or public route. The StatefulSet's `volumeClaimTemplates` retain
its one `ReadWriteOnce` `local-path` `80Gi` PVC when deleted or scaled; destructive
storage operations are outside the wrapper.

The MongoDB image is pinned to
`docker.io/library/mongo@sha256:b112b1c1e552ab2b5bf5935b5662e1d19347d68effa8f2595687a42abfac5df4`.
The only runtime values are expected in the Infisical-owned
`shared-mongodb-auth` (`username`, `password`) and `shared-mongodb-tls` (`ca.crt`,
`tls.pem`) Secrets. The latter's `tls.pem` is the concatenated server certificate and
private key consumed by `--tlsCertificateKeyFile`; both target identities are frozen
by the separate source-only Infisical materialization seam and remain unmaterialized
at runtime. The TLS Secret is mounted only into a same-digest `prepare-tls`
init container. It runs as uid/gid `999`, copies the projected source into a memory
`emptyDir`, applies mode `0400` to the private-key-bearing `tls.pem` and `0444` to
`ca.crt`, and verifies `stat` ownership/mode (`999:400` and `999:444`) before the
MongoDB container starts. The main container mounts only that runtime copy read-only;
it never relies on a projected group-readable private key. The pod starts through the
official image entrypoint with
`--auth --tlsMode=requireTLS --tlsCertificateKeyFile=/etc/mongodb/tls/tls.pem`,
`--tlsCAFile=/etc/mongodb/tls/ca.crt`, and
`--tlsAllowConnectionsWithoutCertificates`. TLS is mandatory, but a client
certificate is not: application identity remains SCRAM-SHA-256, so probes and future
clients must authenticate without receiving a server-CA-issued client key. Passing
the certificate argv is intentional:
the official entrypoint's temporary loopback initialization notices that argument and
changes its temporary TLS mode to `allowTLS`, creates the root user, shuts down, and
then starts the final process with `requireTLS`. Without that argv, temporary init
would use disabled TLS and the final transition would not be proven.

Startup, readiness, and liveness authenticate through `mongosh` JavaScript that reads
the existing Secret-backed environment at runtime; no password value is placed in the
probe argv. Each probe first requires a CA-validated TLS/authenticated ping, then fails
if a second plaintext ping succeeds. This prevents the Pod becoming Ready during the
official entrypoint's temporary loopback `allowTLS` phase and requires final
`requireTLS`. The server certificate must cover `localhost`,
`shared-mongodb.shared-services.svc`, and
`shared-mongodb.shared-services.svc.cluster.local`; cryptographic identity validation
and projected-volume metadata remain live stop gates. Future private negative QA must
also prove invalid-CA/hostname and missing/wrong-auth rejection. No runtime check/apply,
Secret materialization, client authorization, backup, restore, transaction,
replica-set, HA, or authoritative-data acceptance is claimed.

## Exposure boundary

The source `shared-postgresql:5432` and `shared-mongodb:27017` Services are ClusterIP-only.
Ingress, NodePort, LoadBalancer, Cloudflare Tunnel, and any public route are
forbidden. TLS is mandatory and certificate values remain Infisical-owned. MongoDB's
NetworkPolicy defaults to deny ingress and egress, then allows only labeled DEV/PROD
CristexHub database clients on TCP `27017`; logical-database authorization remains a
separate required negative test. No database or administrative endpoint may become
public.

## Storage and recovery blockers

The source-only MongoDB topology is intentionally standalone for fast iteration and
no current clients; standalone versus replica-set behavior still affects transactions,
upgrade strategy, and application-consistent recovery. The source profile uses NVMe
`local-path`, one retained `ReadWriteOnce` PVC per engine, `40Gi` for PostgreSQL and
`80Gi` for MongoDB, and per-engine requests of `500m` CPU/`1Gi` memory with limits of
`2` CPU/`3Gi` memory. MongoDB data is `/data/db`; exact filesystem ownership,
connection limits, disruption behavior, trust, and recovery remain subject to runtime
review. A standalone pod is not an authoritative data store and cannot close the
replica-set, transaction, HA, or authoritative-data acceptance gates.

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

This increment adds only source-ready PostgreSQL and MongoDB manifests, guarded
Ansible roles, playbooks, wrappers, action guards, and offline contracts, plus the
separate value-free Infisical database Secret materialization seam. It adds no Secret
value, Kubernetes Secret manifest, Helm value, Argo Application, Kustomize overlay,
route, provider resource, backup job, or generated credential. No host, registry, Kubernetes
API, provider, Infisical, Helm, or runtime operation was authorized or performed.

Stop before any runtime operation until all of the following are approved or proved:

1. PostgreSQL and MongoDB immutable source trust, node pullability, compatibility, and off-node recovery;
2. PostgreSQL and MongoDB image trust and admission;
3. storage, capacity, security contexts, resources, probes, TLS identity, and NetworkPolicy;
4. Infisical Universal Auth, exact Secret materialization, and administrator recovery;
5. one provisioning owner and exact idempotent authorization behavior;
6. backup tooling, destination, key custody, integrity, isolated restore, and RPO/RTO;
7. exact Ansible bootstrap ownership and object-by-object Argo handoff;
8. separate check, first apply, idempotence, Secret, stateful-service, and runtime approvals;
9. replica-set/transaction/HA and authoritative-data decisions before any real client or data.

The logical provisioning scripts and helper resources are source-only as well. They
require exact precreated Infisical consumer credential Secrets, never generate values,
never use secret-bearing argv, never delete databases/users/PVCs, and clean temporary
UID-bound helpers. PROD remains inactive and MongoDB remains non-authoritative. The
source closure is not runtime evidence and does not authorize Kubernetes apply,
Secret operations, database/user provisioning, backup, restore, or Argo handoff.

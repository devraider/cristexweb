# Shared RabbitMQ architecture

## Current live checkpoint — 2026-08-20

Status: **LIVE / PRIVATE / CELERY VALIDATED; RECOVERY AND LEAST-PRIVILEGE ACCEPTANCE OPEN**.

The shared RabbitMQ `4.3.4-management` runtime is live in `shared-services` and
supports the private CristexHub PROD Celery worker. The live PROD vhost is a dedicated vhost, `/cristexhub-prod`, and the observed
principal is `cristexhub_prod_user`.
Celery logged a TLS connection and ready state after the guarded permission
reconciliation. This runtime evidence is separate from definitions backup,
queued-message reconciliation, measured RPO/RTO, and production recovery acceptance.

The live permission expressions are broader than the least-privilege policy wording
(the write/read expressions are `^[^*]+$`), so broker authorization hardening remains
an explicit residual gate. The exposed PROD RabbitMQ credential also requires
verified rotation before public cutover. No management endpoint or broker route is
public; the MongoDB NetworkPolicy blocker separately prevents full private PROD
acceptance.

The source-only status below is retained as historical evidence from the pre-runtime
checkpoint and must not be read as current broker absence.

## Historical source-only status

**SOURCE SELECTED — RUNTIME BLOCKED.** At that earlier checkpoint the one shared
RabbitMQ engine source was selected for deterministic offline authoring, but no
Kubernetes runtime had been applied. The canonical contract is
[`shared-rabbitmq-architecture.yml`](../ansible/files/policies/shared-rabbitmq-architecture.yml).

The selected source is the official Docker image `docker.io/library/rabbitmq:4.3.4-management`,
using the verified linux/amd64 child digest
`sha256:cd4fd60136781671d125ed68ac4b67900c0726b55e2e8b98719daa616a63240b`.
The future topology was one direct, single-node StatefulSet in `shared-services`;
this is not highly available and is not operator-managed. The `shared-services`
Namespace approved first apply/idempotence passed at `changed=0`; that checkpoint did
not itself authorize RabbitMQ runtime.

## Placement and current consumers

The broker belongs in `shared-services` with one retained `local-path` 20Gi
ReadWriteOnce PVC at `/var/lib/rabbitmq`. The future private Services are
`shared-rabbitmq-amqps` on AMQPS port 5671 and `shared-rabbitmq-management` on
HTTPS management port 15671. Neither Service receives an Ingress, NodePort,
LoadBalancer, Cloudflare Tunnel, or public route.

The policy contract reserves CristexHub DEV and PROD as exact consumers with
separate vhosts, credentials, limits, and recovery scopes. It names DEV principal
`cristexhub_dev_rabbitmq` and PROD principal `cristexhub_prod_rabbitmq`; the live
PROD reconciliation currently observes `cristexhub_prod_user`, which is a documented
identity-drift residual requiring source/evidence reconciliation before final
acceptance. Keycloak and Reactive Resume do not receive RabbitMQ access from this
policy. The broker remains a shared failure and contention domain; vhost isolation
is not availability or kernel isolation.

## Future consumer admission

Every future consumer requires a reviewed exact policy change; wildcard or dynamic admission is forbidden.

## Authorization and management

Cross-vhost access defaults to deny. Workload users cannot create users, vhosts, or
policies and cannot receive administrator or wildcard configure/write/read access.
The default guest account is disabled for hosted use. Required negative tests deny
DEV to PROD, PROD to DEV, workload administration, and public management access.
Management is available only through private authenticated operator access over HTTPS and is never a public application
route.

## TLS and resources

TLS is required for both listeners. The selected broker certificate is owned by
Infisical and must cover exactly:

- `localhost`
- `shared-rabbitmq.shared-services.svc`
- `shared-rabbitmq.shared-services.svc.cluster.local`

The planned StatefulSet resource bounds are CPU 250m / 1 core and memory 512Mi /
1Gi (requests / limits). These are source-selection values, not runtime evidence.

## Backup and message recovery

The shared [backup architecture](shared-stateful-backup-architecture.md) governs
encrypted, off-node, integrity-checked recovery artifacts. RabbitMQ definitions
and policies must be reproducible from value-free Git policy plus Infisical-owned
credentials. Exported definitions are sensitive recovery material and never belong
in Git.

RabbitMQ definitions recovery is not queued-message recovery. Celery broker messages
have the current direction **non-authoritative and reconcilable**: authoritative job
state remains in application databases, and application reconciliation must prove
that interrupted or lost jobs recover safely. Definitions restore, queued-message
reconciliation, measured RPO/RTO, and production recovery acceptance remain blocked.
If any future queue becomes authoritative, stop and add a separate consistent
message-store backup and isolated restore design before promotion.

## Runtime gates

Historical source-only gates at the earlier checkpoint remained **NOT RUN/BLOCKED**:
Infisical secret-zero recovery, runtime check/apply, private AMQPS and management
validation, DEV/PROD negative authorization tests, definitions backup/isolated
restore, queued-message reconciliation, measured RPO/RTO, and one-writer handoff.
That historical record said **No StatefulSet, Deployment, Service, PVC, Secret, Job,
CronJob, or NetworkPolicy** had been applied; the current broker runtime is recorded
above. Recovery, least-privilege authorization, and public-route exclusion remain
separate current gates.

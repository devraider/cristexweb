# Shared RabbitMQ architecture

## Status

**SOURCE SELECTED — RUNTIME BLOCKED.** The one shared RabbitMQ engine source is now
selected for deterministic offline authoring, but no Kubernetes runtime has been
applied. The canonical contract is
[`shared-rabbitmq-architecture.yml`](../ansible/files/policies/shared-rabbitmq-architecture.yml).

The selected source is the official Docker image `docker.io/library/rabbitmq:4.3.4-management`,
using the verified linux/amd64 child digest
`sha256:cd4fd60136781671d125ed68ac4b67900c0726b55e2e8b98719daa616a63240b`.
The future topology is one direct, single-node StatefulSet in `shared-services`;
this is not highly available and is not operator-managed. The `shared-services`
Namespace approved first apply/idempotence passed at `changed=0`; that checkpoint did
not itself authorize RabbitMQ runtime.

## Placement and current consumers

The broker belongs in `shared-services` with one retained `local-path` 20Gi
ReadWriteOnce PVC at `/var/lib/rabbitmq`. The future private Services are
`shared-rabbitmq-amqps` on AMQPS port 5671 and `shared-rabbitmq-management` on
HTTPS management port 15671. Neither Service receives an Ingress, NodePort,
LoadBalancer, Cloudflare Tunnel, or public route.

CristexHub DEV and PROD are the exact current consumers with dedicated vhost permissions. DEV uses vhost
`/cristexhub-dev` and principal `cristexhub_dev_rabbitmq`; PROD uses
`/cristexhub-prod` and principal `cristexhub_prod_rabbitmq`. Each receives a
separate Infisical-owned credential, permissions limited to its vhost, dedicated
limits, and a separate recovery scope. Keycloak and Reactive Resume do not receive
RabbitMQ access from this policy. The broker remains a shared failure and
contention domain; vhost isolation is not availability or kernel isolation.

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

The source selection and offline policy contract are complete, but the following
remain **NOT RUN/BLOCKED**: Infisical secret-zero recovery, runtime check/apply,
private AMQPS and management validation, DEV/PROD negative authorization tests,
definitions backup/isolated restore, queued-message reconciliation, measured RPO/RTO,
and one-writer handoff. No StatefulSet, Deployment, Service, PVC, Secret, Job, CronJob, or NetworkPolicy
has been applied; no operator, role, playbook, wrapper, route, generated credential,
or backup command has been added by this policy increment.

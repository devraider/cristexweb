# Shared RabbitMQ architecture

## Status

**POLICY ONLY — RUNTIME BLOCKED.** This value-free design places one shared RabbitMQ
engine in the future `shared-services` Namespace. It does not select an image,
topology, Service, port, storage, queue policy, credential, or executable object and
does not claim that RabbitMQ exists.

The canonical contract is
[`shared-rabbitmq-architecture.yml`](../ansible/files/policies/shared-rabbitmq-architecture.yml).

## Placement and current consumers

CristexHub DEV and CristexHub PROD are the exact current consumers. Each receives a
dedicated vhost, dedicated workload user, Infisical-owned credential, permissions
limited to its vhost, resource-limit scope, and recovery scope. The one broker is a
shared failure and contention domain; vhost isolation does not provide availability
or kernel isolation.

Redis remains environment-local. Keycloak and Reactive Resume do not receive
RabbitMQ access from this policy.

## Future consumer admission

A future consumer is added only through a reviewed exact policy change. Wildcard,
dynamic, default, or implicit consumers are forbidden. Each addition must define an
exact identifier, dedicated vhost, dedicated principal and Infisical credential,
permissions and limits, capacity review, negative cross-vhost tests, recovery
disposition, and matching policy, test, and runbook updates.

## Authorization and management

Cross-vhost access defaults to deny. Workload users cannot create users, vhosts, or
policies and cannot receive administrator or wildcard configure/write/read access.
The default guest account is disabled for hosted use. Negative tests must deny DEV
to PROD, PROD to DEV, workload administration, and public management access.

RabbitMQ management remains available only through private authenticated operator
access. It receives no public route, Ingress, NodePort, LoadBalancer, or Cloudflare
Tunnel. Private management does not weaken workload-user restrictions.

## Backup and message recovery

The shared
[backup architecture](shared-stateful-backup-architecture.md) governs encrypted,
off-node, integrity-checked recovery artifacts. RabbitMQ definitions and policies
must be reproducible from value-free Git policy plus Infisical-owned credentials.
Exported definitions are sensitive recovery material and never belong in Git.

RabbitMQ definitions recovery is not queued-message recovery. Celery broker messages
have the current direction **non-authoritative and reconcilable**: authoritative job
state remains in application databases, and application reconciliation must prove
that interrupted or lost jobs recover safely. This is a direction, not accepted
runtime evidence. If any future queue becomes authoritative, stop and add a separate
consistent message-store backup and isolated restore design before promotion.

## Resource, storage, and source blockers

Repository, version, immutable linux/amd64 digest, topology, StorageClass, PVC
capacity, reclaim behavior, TLS identity, Service identity and ports, requests,
limits, connection limits, vhost limits, queue limits, probes, disruption behavior,
and NetworkPolicy flows remain unselected. The mutable local Compose
`rabbitmq:3-management` input is not a hosted source selection.

## Executable-source stop gate

No StatefulSet, Deployment, Service, PVC, Secret, Job, CronJob, or NetworkPolicy is
added by this increment. It also adds no Ansible role, playbook, wrapper, Helm values,
Argo Application, route, generated credential, or backup command.

Stop before executable source until immutable image trust and recovery, topology,
storage, resources and limits, TLS, private NetworkPolicy, Infisical secret-zero
recovery, definitions restore, message reconciliation, one-writer handoff, and
runtime approval all pass. `shared-services` check/apply/idempotence remains a
separate NOT RUN approval sequence.

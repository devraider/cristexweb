# Shared stateful backup architecture

## Status

**POLICY ONLY — RUNTIME BLOCKED.** This design covers PostgreSQL, MongoDB, and
RabbitMQ recovery artifacts without selecting a backup image, credential, folder,
local staging path, or executable job. The source profile fixes daily archives,
14-day local/off-node retention, RPO `24h`, and RTO `4h`; no backup or restore has
run.

The canonical contract is
[`shared-stateful-backup-architecture.yml`](../ansible/files/policies/shared-stateful-backup-architecture.yml).

## Easy and safe operator access

Easy access means private authenticated operator retrieval, never a public download
page or anonymous share. A metadata-only catalog must show service, consumer or
purpose, timestamp, integrity status, and restore-test status without exposing
archive contents, credentials, personal data, connection strings, or encryption
material.

Archives use the predictable layout `service/consumer-or-purpose/timestamp`. The
selected implementation must provide a simple private list, retrieve, verify, and
isolated-restore workflow with redacted status output. The off-node destination is
not mounted as live application data.

## Archive and transfer contract

Every archive is compressed, encrypted, timestamped, checksum-manifested, and copied
with non-destructive immutable semantics. Encryption-key custody is independent from
the backup credential. Consumer or purpose paths remain separate. Integrity
verification and an isolated restore are mandatory; a successful upload is not
recovery evidence.

The existing direction is Google Drive through containerized `rclone copy`, but it
remains intended rather than approved until the immutable container image, remote
identity, root folder identity, credentials, and recovery procedure are selected. Use `rclone copy`; never `rclone sync`. Destructive mirror semantics are
forbidden.

## Service-specific recovery

PostgreSQL uses application-consistent logical dumps with role and ownership
recreation. MongoDB uses application-consistent logical dumps compatible with the
selected topology and recreates bounded users and roles. Every current database
consumer receives a separate archive path and isolated restore proof.

RabbitMQ definitions and policies require a protected definitions artifact, but
RabbitMQ definitions recovery is not queued-message recovery. The current direction
classifies Celery messages as non-authoritative and reconcilable from application
state; application reconciliation must still be proved. A definitions export alone
must never be presented as durable-message recovery.

## Future consumer admission

Future services, consumers, or recovery purposes require a reviewed exact policy
change. Each addition receives an exact archive path, retention and capacity review,
integrity check, isolated restore plan, RPO/RTO disposition, and policy, test, and
runbook update. Wildcard or dynamic paths are forbidden.

## Remaining decisions and stop gate

The exact backup-tool image and digest, Google Drive identity and folder, local
staging path and capacity, credential recovery, encryption-key recovery, schedule
implementation, retention enforcement, and measured RPO/RTO remain unselected or
unproved.

No CronJob, Job, PVC, Secret, Service, public download endpoint, or executable
wrapper is added by this increment. Stop before executable source until every
promotion gate passes and a separately approved isolated restore proves recovery.
No host, disk, registry, Google Drive, Infisical, Kubernetes API, backup, restore, or
runtime operation is authorized here.

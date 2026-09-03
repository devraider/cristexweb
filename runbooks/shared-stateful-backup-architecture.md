# Shared stateful backup architecture

## Status

**POSTGRESQL KEYCLOAK SCHEDULER ACTIVE.** The operator approved and completed a
host-managed systemd scheduler for encrypted PostgreSQL backups
to Google Drive, followed by an isolated restore rehearsal before enabling the daily
timer. The pinned host `rclone 1.71.1` and Debian `age 1.2.1-1+b5` are installed. The
existing host-only `drive:` OAuth remote passed an authenticated request without
exposing token content. The dedicated age private identity is held only in Infisical
Cloud at `prod:/shared-services/backup-recovery`; the host retains only its public
recipient.

Installation, one encrypted immutable backup with exact readback, Infisical-held key
recovery, isolated PostgreSQL 17 restore, cleanup, timer enablement, and idempotence
all passed. The timer is enabled and active (`waiting`) for the daily schedule.

The active scheduled PostgreSQL slice covers database `keycloak`. The separate
shared-MongoDB scheduler is also installed and active: it targets the complete
`shared-mongodb` replica set, uses authenticated CA-validated TLS and
`mongodump --archive --oplog`, encrypts to the same public age recipient, uploads to
`drive:cristexweb-recovery/mongodb/shared-mongodb/<timestamp>/`, and schedules at
`03:45` host time plus bounded jitter. Its oplog-consistent backup, immutable
readback, Infisical-key decrypt, isolated MongoDB `8.0.12` restore, cleanup, timer
enablement, and final `changed=0` repeated apply all pass.
Other PostgreSQL consumers, RabbitMQ, remote deletion/retention, and production
acceptance require separate reviewed extensions. The canonical contract is
[`shared-stateful-backup-architecture.yml`](../ansible/files/policies/shared-stateful-backup-architecture.yml).

## Selected host implementation

The only entrypoint is:

```text
ansible/bin/configure-postgresql-keycloak-backup check|apply|test|restore|enable-check|enable-apply
ansible/bin/configure-mongodb-shared-backup check|apply|test|restore|enable-check|enable-apply
```

`check` and `apply` install source while keeping the timer disabled. `test` performs
one separately approved backup through the systemd service. `enable-check` predicts
timer activation. For each active scheduler, `enable-apply` was executed only after
its encrypted archive was downloaded from Google Drive, checked, decrypted with the
Infisical-held age identity in protected temporary storage, and restored without
touching the source database: PostgreSQL into an isolated PostgreSQL 17 runtime and
MongoDB into an isolated MongoDB 8.0.12 runtime.

The PostgreSQL timer runs daily at `03:15` host time and the MongoDB timer at `03:45`;
each has bounded 15-minute randomized delay, `Persistent=true`, RPO direction `24h`,
and local encrypted retention `14d`. Remote objects are never removed automatically. The service runs as the non-root operator,
uses the existing group-readable k3s kubeconfig and host-only rclone configuration,
and has systemd hardening plus an exclusive lock.

## Easy and safe operator access

Easy access means private authenticated operator retrieval, never a public download
page or anonymous share. A metadata-only catalog shows service, database, timestamp,
archive size, checksum, upload/readback result, and restore-test status without
archive contents, credentials, personal data, connection strings, OAuth material, or
encryption keys.

Visibility and traceability use:

```bash
systemctl status cristexweb-postgresql-keycloak-backup.timer
systemctl list-timers cristexweb-postgresql-keycloak-backup.timer
journalctl -u cristexweb-postgresql-keycloak-backup.service
```

The journal emits only sanitized stages and a final one-line receipt. Google Drive
uses the exact immutable layout:

```text
cristexweb-recovery/postgresql/keycloak/<UTC timestamp>/
  keycloak.dump.gz.age
  keycloak.dump.gz.age.sha256
  manifest.json
```

## Archive and transfer contract

The service discovers the ready CloudNativePG primary, executes PostgreSQL 17
`pg_dump` for only database `keycloak`, compresses it, encrypts it to the public age
recipient, removes plaintext under a trap, and creates SHA-256 plus value-free JSON
metadata. It uploads each exact leaf with `rclone copyto --immutable`, downloads each
leaf to a private temporary readback directory, requires byte equality, and removes
readback residue. Use immutable copy semantics; never `rclone sync`, move, purge, delete, or a public share.

The Google Drive OAuth token exists only in the host operator's mode-`0600` rclone
configuration. The age private identity exists only in Infisical and is fetched only
for an explicitly approved restore into trapped private temporary storage. Neither
value is committed, passed in argv/environment, written to evidence, or logged.

The PostgreSQL Keycloak manifest is schema `1` with an exact
`source_closure_sha256` field. The current closure is
`9f19846c97ba16dcf7e394f430b4ac93c1c00a0113a95dddca74787d9518d3c9`; it is computed
from the restore executable (with its self-pin canonicalized), the service unit, and
the timer unit. The backup writes the digest as a JSON value, not a shell literal.
The restore requires the exact pinned digest, archive checksum, archive size, and
field set. Archives made by the previous source, including manifests without the
closure field or with the literal `$source_closure_sha256`, are rejected with the
sanitized `restore_status=failed stage=manifest_contract` receipt and must not be
used as acceptance evidence. A fresh backup and restore are required after this
source-closure correction before any timer-enable gate can be accepted.

## Isolated restore acceptance

A successful upload is not recovery evidence. Before timer activation, the rehearsal
must:

1. enumerate timestamp directories with an explicit, checked `rclone` result;
2. select the newest directory whose exact three-leaf set is complete; newer incomplete directories are ignored and never deleted;
3. reject duplicate timestamps, extra leaves, missing leaves, and duplicate leaves;
4. download archive, checksum, and manifest into mode-`0700` temporary storage;
5. verify manifest closure and SHA-256 before decryption;
6. retrieve the exact age identity from Infisical without output;
7. decrypt and decompress only inside the trapped directory;
8. restore into a temporary PostgreSQL `17.10` runtime with isolated empty storage;
9. validate the restored database/catalog and expected Keycloak schema state;
10. remove the temporary runtime and all plaintext/key residue; and
11. record only sanitized duration, checksum status, restore result, and zero residue.

The production `shared-postgresql` Cluster, database `keycloak`, role, Secret, and PVC
remained unchanged throughout. The final enable apply converged at `changed=0` and
verified both `enabled` and `active`; the next scheduled run was registered by
systemd.

## Service-specific recovery and future admission

PostgreSQL uses application-consistent logical dumps for data recovery. Role,
ownership, ACL/default privileges, and login credential recreation remain a
separate database/Infisical/CNPG custody gate and are never inferred from a data
archive. MongoDB uses one replica-set-wide oplog-consistent archive; the MongoDB
Community Operator plus Infisical remain declarative owners for user/SCRAM recreation,
while the archive recovers application data and compatible database metadata. Its
restore rehearsal uses the same immutable `8.0.12` image digest, isolated `emptyDir`,
no Service/PVC/Secret, and exact UID-precondition cleanup. The RabbitMQ definitions
scheduler requires the exact Infisical-owned `shared-rabbitmq-admin` target contract:
only `username`, `password`, and `passwordHash` keys are accepted. Each backup
manifest carries the actual source-closure digest (the restore self-pin is
canonicalized before hashing to avoid a circular pin), and restore rejects any
missing or mismatched digest. Restore decrypts and decompresses through separate
staged files with independent status checks, so an age failure cannot be masked
by gzip. The management request uses the username/password
pair; `passwordHash` is validated as required
custody material but is never emitted or used as a substitute credential. Backup receipts carry `schema=1` and `readback=verified`; isolated restore receipts carry `schema=1`, the exact source-closure digest, and `checksum=verified`. Enablement parses both receipts without output, requires exact field sets, and binds the backup `timestamp` to the restore `source_timestamp`; mismatched timestamps, schemas, or closure digests cannot enable a timer. RabbitMQ
definitions recovery is not queued-message recovery, and it does not prove consumer
identity, permissions, or message disposition. Each future service or consumer
requires an exact archive path, capacity/retention review, integrity check, isolated
restore, RPO/RTO disposition, and policy/test/runbook change; wildcard admission is
forbidden.

No CronJob, Job, PVC, Kubernetes Secret, Service, or public download endpoint is
created by this host scheduler. Backup credentials remain isolated from application
credentials. Measured multi-run RPO/RTO, independent Google-account recovery, remote retention,
other databases, and production recovery acceptance remain blocked until evidenced.

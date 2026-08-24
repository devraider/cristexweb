# Reactive Resume DEV backup scheduler

## Status

**SOURCE-ONLY DESIGN / NOT RUN / RUNTIME UNINSTALLED.** This runbook defines a
future host-managed weekly backup for the private Reactive Resume DEV logical
PostgreSQL database and private SeaweedFS object storage. It has no Kubernetes
CronJob, PVC copy, remote deletion, public endpoint, or live installation in this
revision. The only permitted rollback is a Git revert before a separately
approved host apply.

The scheduler is intentionally one combined service. Each run uses one UTC
`YYYYmmddTHHMMSSZ` run ID and writes both the PostgreSQL and object-storage
archives under that exact ID. A value-free `run-manifest.json` binds the two
archive checksums, byte counts, database name, bucket, object count, and total
object bytes. This prevents accepting a database archive from one run with
objects from another.

## Scope and ownership

- Host Ansible owns the systemd service, timer, local encrypted staging boundary,
  and exact rclone/age input metadata.
- The live CloudNativePG `shared-postgresql` primary is read through the existing
  group-readable k3s kubeconfig; only database
  `reactive_resume_dev_successor` is dumped.
- SeaweedFS is read through its authenticated TLS S3 API using a temporary
  service-account-free rclone Pod. The production StatefulSet and PVC are never
  mounted, copied, suspended, or deleted.
- Infisical retains the age private identity at
  `prod:/shared-services/backup-recovery`; the host retains only the public age
  recipient. Application and S3 values never enter Git, argv, logs, or evidence.
- The future application remains in `cristexhub-dev`; PROD has no source or
  backup path in this closure.

## Fixed artifacts

The guarded source files are:

```text
ansible/files/backup/reactive-resume-dev-backup
ansible/files/backup/restore-reactive-resume-dev-backup-rehearsal
ansible/files/backup/cristexweb-reactive-resume-dev-backup.service
ansible/files/backup/cristexweb-reactive-resume-dev-backup.timer
ansible/playbooks/configure_reactive_resume_dev_backup.yml
ansible/bin/configure-reactive-resume-dev-backup
```

The only wrapper modes are:

```text
ansible/bin/configure-reactive-resume-dev-backup check
ansible/bin/configure-reactive-resume-dev-backup apply
ansible/bin/configure-reactive-resume-dev-backup test
ansible/bin/configure-reactive-resume-dev-backup restore
ansible/bin/configure-reactive-resume-dev-backup enable-check
ansible/bin/configure-reactive-resume-dev-backup enable-apply
```

`check` and `apply` install source while leaving the timer disabled. `test`
runs one separately approved backup. `restore` requires a separately created
mode-`0600` attestation and token and restores both datasets into isolated
emptyDir runtimes. `enable-check` predicts activation and `enable-apply` is only
permitted after a verified backup and isolated restore. Direct playbook
invocation, extra arguments, task selection, and root execution of the backup
script are refused.

## Weekly schedule and retention

The systemd timer runs:

- `OnCalendar=Sun *-*-* 04:15:00`;
- `RandomizedDelaySec=30m`;
- `Persistent=true`; and
- `AccuracySec=1m`.

The service runs as unprivileged host user `paul` with `k3s-admin` kubeconfig
access, `ProtectSystem=strict`, `ProtectHome=read-only`, `PrivateTmp`,
`NoNewPrivileges`, empty capability sets, and an exclusive flock. It retains
only timestamped encrypted local directories under
`/var/lib/cristexweb-backup/reactive-resume/dev/` for 14 days. It never removes
Google Drive objects and never uses `rclone sync`, move, purge, or delete.

The remote layout is:

```text
drive:cristexweb-recovery/reactive-resume/dev/<run-id>/
  object-storage.manifest.json
  object-storage.tar.gz.age
  object-storage.tar.gz.age.sha256
  postgresql.dump.gz.age
  postgresql.dump.gz.age.sha256
  postgresql.manifest.json
  run-manifest.json
```

Every leaf is uploaded using `rclone copyto --immutable`, downloaded to a
private readback directory, and compared byte-for-byte before the run succeeds.

## PostgreSQL backup

The backup checks the current CNPG primary and ready `postgres` container, then
runs PostgreSQL 17 `pg_dump --format=custom --no-owner --no-privileges` for only
`reactive_resume_dev_successor`. The plaintext dump exists only in the trapped
0700 local run directory, is gzip-compressed and encrypted to the public age
recipient, and is removed before the final receipt. The checksum and manifest
bind the archive to the same run ID as object storage.

A PostgreSQL PVC, the shared engine PVC, other databases, roles, credentials,
and application Secrets are never copied or exported.

## SeaweedFS object backup

The backup verifies the private ClusterIP service, ready one-member StatefulSet,
TLS Secret metadata, and authenticated S3 Secret metadata. It starts one exact,
run-labelled, service-account-free rclone Pod with the pinned rclone `1.71.1`
image, the object-storage CA, and Secret references. It reads the bucket through
S3, not through `/data` or the PVC. Object keys are restricted to the reviewed
DEV prefixes:

- `uploads/user-pictures/`;
- `pictures/`; and
- `uploads/user-agent/`.

The helper produces a sorted value-free object manifest containing keys, sizes,
and available MD5 values, then creates an encrypted `object-storage.tar.gz.age`.
The raw object export and helper Pod are removed on every exit path. No bucket
creation, object deletion, PVC mutation, or raw volume copy is performed by the
backup; there is no raw volume copy.

## Isolated restore rehearsal

Restore selects the newest complete seven-leaf timestamp directory only. It
validates both archive checksums, the per-service manifests, and the correlated
`run-manifest.json` before decryption. It retrieves the Infisical-held age
identity only inside a trapped 0700 temporary directory and removes it before
validation.

PostgreSQL restores into an isolated PostgreSQL 17 temporary Pod with only `emptyDir`,
`listen_addresses=` and no Service, PVC, or source-database connection. It runs
`pg_restore --exit-on-error` and validates the catalog before UID-preconditioned
orphan cleanup.

Objects are path-validated before extraction and restored into an isolated SeaweedFS
Pod with emptyDir data, the pinned SeaweedFS image, the same TLS/auth
contracts, and a temporary rclone sidecar. A loopback host alias is used only to
match the service certificate. The restore checks object count and total bytes,
then deletes only the exact run-labelled Pods using UID preconditions and
`Orphan` propagation. The production StatefulSet, PVC, bucket, and remote
archive remain untouched.

A successful rehearsal emits only:

```text
restore_status=success source_run_id=<timestamp> postgres_catalog_table_count=<n> object_count=<n> object_bytes=<n> checksum=verified target=isolated-emptydir-postgresql-and-seaweedfs private_residue=none
```

No archive contents, Secret values, tokens, credentials, age identity, or
Authorization headers are printed.

## Acceptance gates

Before installation or timer enablement, the operator must separately approve
and evidence:

1. pinned image provenance and vulnerability disposition for rclone, PostgreSQL,
   and SeaweedFS;
2. host disk encryption and backup-directory custody;
3. exact Infisical age-identity recovery without value output;
4. one successful combined backup with immutable Drive readback;
5. one successful combined isolated restore with zero private residue;
6. private application S3 upload/read/delete and PostgreSQL login validation;
7. measured RPO/RTO and at least one multi-run correlation check; and
8. final idempotent scheduler apply.

Remote retention, independent Google-account recovery, destructive restore,
production activation, PROD backup scopes, and public exposure remain blocked.

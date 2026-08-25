# Reactive Resume DEV backup scheduler

## Status

**SOURCE IMPLEMENTED / PRIOR SCHEMA-1 NON-EMPTY BACKUP PASSED / HARDENED SCHEMA-2
INSTALL, BACKUP, AND RESTORE PENDING.** The guarded twice-daily scheduler and
schema-2 backup/restore source are implemented and remain value-free. A prior
installed version produced the sanitized non-empty receipt
`run_id=20260825T065948Z object_count=1 total_object_bytes=50 readback=verified
encrypted=true private_residue=none`. That receipt is schema-1 evidence from the
previous source and is not acceptable evidence for the hardened schema-2 restore.
A hardened source install, fresh schema-2 non-empty backup, isolated restore,
measured RPO/RTO, and final scheduler enable/idempotence remain pending. No
hardened runtime installation or restore is claimed here. There is no Kubernetes
CronJob, PVC copy, remote deletion, or public endpoint. The only permitted
rollback is a Git revert before a separately approved host apply.

The scheduler is one combined service. Each run uses one UTC
`YYYYmmddTHHMMSSZ` run ID and writes both archives under that exact ID. A
value-free `run-manifest.json` binds checksums, byte counts, logical PostgreSQL
entry/table counts, object keys, per-object sizes and SHA-256 checksums, the
snapshot completion timestamp, and backup duration. RPO is measured from that
completion timestamp, not from run start.

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

The only wrapper modes are. Every mode invokes Ansible with
`--ask-become-pass`; enter the sudo password in the controlling terminal and do
not pipe or redirect the wrapper, especially when invoked from another guarded
workflow.

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

## Twice-daily schedule and retention

The systemd timer runs twice daily:

- `OnCalendar=*-*-* 00,12:15:00`;
- `RandomizedDelaySec=0`;
- `Persistent=true`; and
- `AccuracySec=1m`.

The fixed 12-hour cadence keeps the completion-based RPO below 24 hours even
when a run takes its full 60-minute service timeout.

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

The helper produces a sorted value-free object manifest containing every key,
size, and SHA-256 checksum (plus available MD5 values), verifies every copied
object against that manifest before archiving, and then creates an encrypted
`object-storage.tar.gz.age`.
A successful acceptance backup refuses an empty bucket: both `object_count` and
`total_object_bytes` must be greater than zero. The raw object export and helper
Pod are removed on every exit path. No bucket
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
`pg_restore --exit-on-error` and validates the catalog and expected logical table
count before UID-preconditioned orphan cleanup. The backup first runs
`pg_restore --list` and refuses a dump with no logical entries or table entries.

Objects are path-validated before extraction and restored into an isolated SeaweedFS
Pod with emptyDir data, the pinned SeaweedFS image, the same TLS/auth
contracts, and a temporary rclone sidecar. A loopback host alias is used only to
match the service certificate. The restore checks every extracted object against the archived per-object
manifest, then performs a remote per-object listing/checksum comparison after
upload. It still requires object count and total bytes greater than zero, then
deletes only the exact run-labelled Pods using UID preconditions and `Orphan`
propagation. Cleanup errors fail the operation rather than being suppressed. The production StatefulSet, PVC, bucket, and remote
archive remain untouched.

A successful rehearsal emits only:

```text
restore_status=success source_run_id=<timestamp> backup_duration_seconds=<n> restore_duration_seconds=<n> rpo_seconds=<n> postgres_catalog_table_count=<n> object_count=<n> object_bytes=<n> checksum=verified target=isolated-emptydir-postgresql-and-seaweedfs private_residue=none
```

`rpo_seconds` is the measured age of the selected backup's completion timestamp
at restore completion; `restore_duration_seconds` is the measured
isolated-rehearsal runtime. A future completion timestamp fails closed as
`clock_skew`; timestamps are never clamped to zero. The checked targets are RPO
`86400` seconds (24 hours) and RTO `14400` seconds (4 hours); the restore refuses
a receipt outside either bound.

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
7. a successful non-empty backup and isolated restore with measured
   `backup_duration_seconds`, `restore_duration_seconds`, and `rpo_seconds`,
   including logical PostgreSQL content and per-object checksum evidence;
8. measured RPO/RTO within 24-hour/4-hour targets and at least one multi-run
   correlation check; and
9. final idempotent scheduler apply.

## Remaining hardened acceptance sequence

The prior schema-1 receipt is historical and cannot close the hardened schema-2
gates. The operator must separately approve each wrapper invocation and must not
paste or capture credentials. Run these remaining steps in order from the
canonical checkout:

```text
# source-only validation
.venv/bin/python -m unittest tests.test_reactive_resume_dev_backup_contract
sh -n ansible/files/backup/reactive-resume-dev-backup
sh -n ansible/files/backup/restore-reactive-resume-dev-backup-rehearsal

# install/check (sudo prompt stays visible), then separately approved apply and idempotence
ansible/bin/configure-reactive-resume-dev-backup check
ansible/bin/configure-reactive-resume-dev-backup apply
ansible/bin/configure-reactive-resume-dev-backup apply

# separately approved non-empty combined backup; retain only the sanitized receipt
ansible/bin/configure-reactive-resume-dev-backup test
journalctl -u cristexweb-reactive-resume-dev-backup.service -n 1 -o cat --no-pager

# create a one-use mode-0600 attestation containing only <token>:restore,
# export the wrapper's approved restore variables without displaying them,
# keep the sudo prompt attached to the terminal, then run the isolated combined restore
ansible/bin/configure-reactive-resume-dev-backup restore

# separately verify zero exact temporary Pods and no private staging residue;
# record only the sanitized restore receipt and measured RPO/RTO.
# Repeat test + restore once more only for multi-run correlation approval.

# enable only after non-empty backup, restore, RPO/RTO, cleanup, and correlation pass
ansible/bin/configure-reactive-resume-dev-backup enable-check
ansible/bin/configure-reactive-resume-dev-backup enable-apply
ansible/bin/configure-reactive-resume-dev-backup enable-check
```

The restore attestation file and token are operator inputs and must never appear
in shell history, chat, plans, logs, or evidence. The `journalctl` receipt must
be reviewed for only the allowlisted `backup_status=success` fields; never use
`kubectl get secret`, `infisical secrets get`, `env`, or debug tracing that could
print values. Capture wall-clock start/end separately if an external evidence
record is required, while treating the script's sanitized duration and RPO
fields as the canonical measurements.

Remote retention, independent Google-account recovery, destructive restore,
production activation, PROD backup scopes, and public exposure remain blocked.

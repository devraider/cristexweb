# OpenTofu GitHub state backup and restore lane

## Status

This is a **source-only** Ansible lane for the separate GitHub OpenTofu root. It has
not contacted the inventory host, Google Drive, Infisical, OpenTofu provider APIs, or
GitHub. No timer, state file, archive, credential, or host configuration was
created or changed while authoring this source.

The lane is deliberately independent of the Cloudflare/foundation state lane. It
cannot select or parameterize the foundation state, archive directory, lock, unit,
timer, or restore executable.

## Fixed boundary

| Item | Fixed value |
|---|---|
| OpenTofu state | `/var/lib/opentofu/cristexweb/github.tfstate` |
| Local archive root | `/var/lib/cristexweb-backup/opentofu/github` |
| Remote archive root | `drive:cristexweb-recovery/opentofu/github` |
| Backup executable | `/usr/local/libexec/cristexweb/opentofu-github-state-backup` |
| Restore executable | `/usr/local/libexec/cristexweb/restore-opentofu-github-state-rehearsal` |
| Lock | `/run/lock/cristexweb-opentofu-github-state-backup.lock` |
| Service/timer | `cristexweb-opentofu-github-state-backup.{service,timer}` |
| Timer | Daily at `03:15:00`, with a 15-minute randomized delay |
| Infisical recovery path | `prod:/shared-services/backup-recovery` |
| Infisical recovery key | `SHARED_DATABASE_BACKUP_AGE_IDENTITY` |

The lane accepts no state path, archive path, remote, lock, unit, identity, or
retention parameters. The only wrapper-selected modes are the bounded lifecycle
modes `install`, `test`, `restore`, and `enable`; the wrapper supplies the approval
attestation and the playbook independently checks it.

The existing public age recipient at `/etc/cristexweb-backup/age.recipient` and its
reviewed SHA-256 contract are reused. The private age identity is retrieved only by
the isolated restore executable into a mode-0700 temporary directory, then removed.
It is never installed, logged, copied into state, or committed.

## Archive contract

Each timestamped run contains exactly these leaves:

- `github.tfstate.age` — age-encrypted local state;
- `github.tfstate.age.sha256` — checksum of the encrypted leaf; and
- `manifest.json` — schema-1 metadata containing the fixed state path, archive
  size/checksum, timestamp, local backend marker, and `opentofu-github` service
  marker.

The backup executable validates the state file owner/mode and runs only
`tofu state list` before encryption. It uses `rclone copyto --immutable` for each
leaf, reads each remote leaf back, and compares it byte-for-byte with `cmp`. It
never uses `sync`, remote deletion, or remote retention deletion. Local retention
removes only timestamp directories under the fixed GitHub archive root after 14
 days; it cannot reach the foundation archive root.

The service runs as `paul` under a dedicated systemd unit with strict filesystem and
capability restrictions. Its writable archive path is only the fixed GitHub archive
path (plus the lock and protected rclone configuration paths).

## Isolated restore contract

Restore selects the newest timestamp directory under the fixed GitHub remote root,
retrieves the three exact leaves, verifies the checksum and complete manifest
closure, and decrypts only into a mode-0700 `/dev/shm` temporary directory. It then
validates the JSON shape and runs `TOFU_DISABLE_CHECKPOINT=1 tofu state list` against
the temporary state copy. It never writes the protected state path, runs `tofu
apply`, runs `state push`, imports resources, or contacts a provider. Cleanup removes
the decrypted state, resource listing, identity, and temporary directory. The only
accepted receipt is the sanitized `restore_status=success ... non_mutating=true`
line asserted by the playbook.

A restore is blocked until a verified timestamped GitHub archive exists and the
protected Infisical recovery identity can be retrieved without value output. An
empty or absent `/var/lib/opentofu/cristexweb/github.tfstate` is expected before the
separate GitHub provider/root checkpoint; it is not synthesized by this lane.

## Guarded entrypoint and lifecycle

The only entrypoint is:

```text
ansible/bin/configure-opentofu-github-state-backup
```

It requires one of `check`, `apply`, `test`, `restore`, `enable-check`, or
`enable-apply`, fixes the repository-local controller and inventory, requires the
single `crtxweb` host and clean attestation, and rejects symlinked wrappers or
controllers. `check` is the installation check; `apply` installs only this lane's
files and directories. `test` runs one explicitly approved backup, `restore` runs
one explicitly approved isolated rehearsal, and `enable-*` is reserved for after
backup/readback and restore acceptance. Installation, backup, restore, and timer
enablement remain separate approvals.

Install/test/restore modes keep this timer disabled. No task in this playbook
stops, starts, enables, disables, or reloads the foundation
`cristexweb-opentofu-state-backup.timer`; that timer and
`foundation.tfstate` remain outside this lane's source closure.

Before any future host run, perform the wrapper `check` and inspect the exact
predicted files. Before `test`, verify a protected GitHub state file, rclone
`drive:` configuration, age recipient, and source state contract. Before
`restore`, verify an immutable archive exists. Before `enable-apply`, require the
fresh backup/readback and isolated restore receipts, then require a second
idempotence check. These source files authorize no provider apply, repository
creation, source push, workflow, package publication, Kubernetes object, Secret,
Infisical write, or public route.

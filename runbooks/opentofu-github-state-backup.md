# OpenTofu GitHub state recovery lane

## Status

This is a **source-only** Ansible lane for the separate GitHub OpenTofu root. It has
not contacted the inventory host, Google Drive, Infisical, OpenTofu provider APIs, or
GitHub. No timer, state file, archive, credential, or host configuration was
created or changed while authoring this source.

The lane is independent of the Cloudflare/foundation state lane. It cannot select,
parameterize, stop, or mutate the foundation state, archive, lock, unit, timer, or
restore executable. Its only runtime entrypoint creates a per-run mode-0600
attestation and uses an allowlisted clean controller environment. Direct playbook
execution is rejected by the token, attestation, diff, host, and internal-variable
guards.

## Fixed boundary

| Item | Fixed value |
|---|---|
| OpenTofu state | `/var/lib/opentofu/cristexweb/github.tfstate` |
| State parent | `paul:root` mode `0700`, non-symlink, exact real path |
| State contract | `paul:paul` mode `0600`, non-symlink, exact real path |
| Local state archive root | `/var/lib/cristexweb-backup/opentofu/github` |
| Remote state archive root | `drive:cristexweb-recovery/opentofu/github` |
| Local absence archive root | `/var/lib/cristexweb-backup/opentofu/github-absence` |
| Remote absence archive root | `drive:cristexweb-recovery/opentofu/github-absence` |
| State backup executable | `/usr/local/libexec/cristexweb/opentofu-github-state-backup` |
| State restore executable | `/usr/local/libexec/cristexweb/restore-opentofu-github-state-rehearsal` |
| Absence attestation executable | `/usr/local/libexec/cristexweb/opentofu-github-state-absence-attestation` |
| Absence restore executable | `/usr/local/libexec/cristexweb/restore-opentofu-github-state-absence-rehearsal` |
| Lock | `/run/lock/cristexweb-opentofu-github-state-backup.lock` |
| Service/timer source | `cristexweb-opentofu-github-state-backup.{service,timer}` |
| Timer schedule | Daily at `03:15:00`, with a 15-minute randomized delay |
| Infisical recovery path | `prod:/shared-services/backup-recovery` |
| Infisical recovery key | `SHARED_DATABASE_BACKUP_AGE_IDENTITY` |

The lane accepts no state path, archive path, remote, lock, unit, identity, or
retention parameters. The bounded wrapper modes are only `check`, `apply`, `test`,
`restore`, `attest`, and `restore-absence`. There is deliberately no scheduler
state mode or task: timer activation remains blocked until a separately reviewed
receipt-gated lifecycle exists.

The exact host age recipient is copied with `remote_src: true` from
`/home/paul/.config/cristexweb/backup/shared-database-backup.recipient`; both source
and installed copy must match the reviewed SHA-256 contract. The host rclone config
must return exactly `drive: drive` from `listremotes --long`, binding the sole
remote name and Google Drive backend type. No token/config value is logged.

## Post-genesis state archive contract

Each complete timestamped state run contains exactly these three leaves:

- `github.tfstate.age` — age-encrypted local state;
- `github.tfstate.age.sha256` — checksum of the encrypted leaf; and
- `manifest.json` — schema-1 metadata containing the fixed state path, exact-three
  address scope, archive size/checksum, timestamp, local backend marker, and
  `opentofu-github` service marker.

Before encryption, the backup validates the state parent and file closure and
compares `tofu state list` to exactly these addresses:

```text
github_actions_repository_permissions.reactive_resume_mirror
github_repository.reactive_resume_mirror
github_repository_vulnerability_alerts.reactive_resume_mirror
```

The encrypted payload and checksum upload first; `manifest.json` is uploaded last,
so an interrupted upload cannot appear complete. Restore enumerates only strict UTC
timestamp directories, requires exactly the three leaves, skips incomplete or
extra-leaf directories, and selects the newest complete candidate. It verifies
checksums, manifest closure, decrypts only into a mode-0700 `/dev/shm` directory,
checks the exact state address scope, and runs only a non-mutating
`TOFU_DISABLE_CHECKPOINT=1 tofu state list`.

The state service uses `rclone copyto --immutable`, byte-for-byte readback, no
`sync`, no remote deletion, and fixed-root local retention. It never writes the
protected state path. Its sanitized receipt is the only accepted restore evidence:
`restore_status=success ... address_scope=exact-three non_mutating=true`.

## First-genesis absence attestation

Before the first provider apply there is no meaningful state snapshot to back up.
The `attest` mode therefore records an encrypted, hash-bound absence condition,
not a manufactured empty state. It requires the exact parent contract and both
`-e` and `-L` absence checks for `github.tfstate`, then writes only the dedicated
absence archive root. It never creates or writes the state file.

Each absence run contains exactly three immutable leaves:

- `absence-attestation.json.age`;
- `absence-attestation.json.age.sha256`; and
- `manifest.json`.

The payload includes `state_present:false`, the exact state/parent paths and
ownership/mode contract, `attested_at_utc`, and `expires_at_utc` exactly 15 minutes
later. The manifest is uploaded last, and all three leaves are read back and compared
with `cmp`. Before the success receipt, parent identity and state absence are checked
again. The accepted receipt is:

```text
absence_status=success service=opentofu-github artifact=absence-attestation state=github timestamp=<UTC> readback=verified state_absent=verified encrypted=true expires_at=<UTC>
```

`restore-absence` selects only strict timestamp directories with the exact three
leaves, verifies checksum and manifest closure, retrieves the Infisical age identity
only into mode-0700 `/dev/shm`, decrypts only the attestation payload, validates its
exact keys and unexpired 15-minute contract with explicit Python error checks, and
rechecks state absence before and after the rehearsal. It never invokes OpenTofu,
`state list`, `state push`, `import`, `apply`, or a provider/API operation. Its
accepted receipt includes `state_absent=verified state_write=false non_mutating=true`.

## Guarded lifecycle

The only entrypoint is:

```text
ansible/bin/configure-opentofu-github-state-backup
```

`check` is the installation check; `apply` installs only this lane's files and
fixed directories; `attest` creates first-genesis evidence; `test` runs one
explicitly approved post-genesis backup; `restore` runs one isolated post-genesis
rehearsal; and `restore-absence` runs one isolated absence rehearsal. Every
non-check invocation explicitly keeps the unaccepted timer stopped and disabled.
Systemd unit source remains present only for a future separately reviewed,
receipt-gated scheduler checkpoint; no mode can enable or start the timer.

Before any future host run, perform wrapper `check` and inspect the exact predicted
files. Before `attest`, verify the protected parent/state absence and exact rclone
backend. Before `restore-absence`, verify an unexpired complete absence archive.
Before `test` or `restore`, require a post-genesis state file with exact scope and
fresh immutable archive evidence. These source files authorize no provider apply,
repository creation, source push, workflow, package publication, Kubernetes object,
Secret, Infisical write, or public route.

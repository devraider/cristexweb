# Guarded import of the Reactive Resume GitHub repository

## Status

This is a **source-only** guarded workflow for importing the existing private
`devraider/cristex-reactive-resume` repository into the independent GitHub
OpenTofu root. No provider call, state write, import, backup, or restore was run
while authoring this source. The existing repository is not created by this
workflow; this import workflow never creates a repository.

The canonical entrypoint is:

```text
opentofu/github/bin/import-existing-repository check
opentofu/github/bin/import-existing-repository import
```

The entrypoint is intentionally not an Ansible passthrough and accepts no
provider, state, address, repository, or backup-path arguments.

## Exact import boundary

| Item | Fixed value |
|---|---|
| OpenTofu root | `/home/paul/projects/cristexweb/opentofu/github` |
| Backend state | `/var/lib/opentofu/cristexweb/github.tfstate` |
| Repository owner | `devraider` |
| Repository name | `cristex-reactive-resume` |
| Provider API | `https://api.github.com/` |
| Repository import ID | `devraider/cristex-reactive-resume` |
| Vulnerability-alert import ID | `cristex-reactive-resume` |
| Actions-permissions import ID | `cristex-reactive-resume` |

The three and only three imported addresses are:

```text
github_repository.reactive_resume_mirror
github_repository_vulnerability_alerts.reactive_resume_mirror
github_actions_repository_permissions.reactive_resume_mirror
```

The preflight uses a read-only GitHub API request and requires the authenticated
login, owner, full name, and private visibility to match exactly. It rejects
endpoint overrides and proxies. It also rejects inherited upper/lowercase proxy
variables, `TF_CLI_ARGS*`, `TF_LOG*`, `TF_DATA_DIR`, `TF_WORKSPACE`, `TF_VAR_*`,
and Terraform/OpenTofu CLI configuration overrides. Every provider/helper command
runs from an explicit `env -i` environment with only fixed non-secret inputs;
the protected token is transferred to the GitHub child through an anonymous pipe,
never placed in argv, a file, plan output, or evidence. Provider command output is
captured in mode-0600 temporary files and only sanitized receipts are printed.
The nested backup/restore-absence calls intentionally retain the controlling
terminal because their Ansible wrapper uses `--ask-become-pass`; enter sudo
credentials there and do not pipe or redirect the import command.

The backend file is exact-content bound to SHA-256
`318f268e4f93ae5c7775b798a88db997f4e47d1e32374432cf5c438f63a8e487` and its
literal local path must remain `/var/lib/opentofu/cristexweb/github.tfstate`.
Before the token prompt or any provider command, the entrypoint also verifies
`opentofu/github/SOURCE.sha256` and its pinned manifest digest. That manifest
covers every tracked GitHub-root/source leaf, exact expected mode, and SHA-256
content; the importer is checked through a canonical digest with its two
embedded digest literals normalized. The direct OpenTofu root `.tf`/`.tf.json`
loadable set is compared against the manifest and rejects every extra file.
Missing, extra, symlinked, mode-drifted, or partially changed source fails
closed. These embedded hashes are a reviewed
consistency closure, not an external signature or immutable trust root: a
coordinated rewrite of the importer, manifest, and pins is visible Git source
change requiring review and is not claimed to resist a compromised operator UID. The importer repeats the complete manifest, mode, path, and content-hash
closure immediately before every root consumer (`tofu`, the repository/API
helper, and the plan validator), detecting accidental or cooperative concurrent
drift at each boundary. Before each backup/restore-absence, backup-test, or
restore gate it also hashes the exact Ansible wrapper, playbook, four installed
backup/restore scripts, and their systemd units, then verifies the root-owned
installed copies after the wrapper completes. The trusted operator UID is the
local security boundary:
a malicious process already running as that UID could also inspect process
memory or pipes and is therefore explicitly out of scope; revalidation is not
misrepresented as protection from same-UID compromise. A protected first-genesis `flock` is acquired
below the state parent before the absence check and held through initialization
and all three imports. Absence is
rechecked after the restore-absence gate and after initialization immediately
before the first import.

## Required gates and sequence

1. Verify the canonical worktree and complete the source-closure gate, then run
   the read-only `check` mode. The closure must pass before the check can
   authorize any provider-backed step. The check must confirm the pinned OpenTofu
   path `/usr/local/bin/tofu` resolves to
   the exact regular file `/opt/opentofu/1.12.5/tofu` (root:root:0755); the
   distribution symlink itself is intentional.
2. Independently complete the first-genesis absence attestation and its
   encrypted readback/isolated rehearsal through the guarded state-backup lane.
   The import entrypoint requires the successful `restore-absence` gate immediately
   before mutation; that rehearsal never receives `GITHUB_TOKEN` and never writes
   the state file. The import lock remains held and state absence is rechecked
   after this gate. If the recovery gate fails or its exact 15-minute
   `expires_at_utc` window has elapsed, the entrypoint exits before collecting
   the import confirmation.
3. After the successful recovery gate and absence recheck, obtain separate
   approval for importing an existing private repository and type the exact
   confirmation requested by the entrypoint. The entrypoint then rechecks state
   absence after `tofu init`, reruns the complete encrypted restore-absence
   rehearsal, and rechecks state absence immediately before the first import.
   This second recovery gate is mandatory: an attestation that expires while
   waiting for confirmation or initialization is rejected fail-closed.
4. The entrypoint initializes the pinned provider, then runs only the three exact
   `tofu import` commands above. It has no `tofu apply`, create, delete, destroy,
   `tofu state push`, or `tofu state rm` path. A partial import fails closed and requires
   operator review; it is never repaired by deleting a remote repository.
5. Render a protected mode-0600 binary plan and JSON plan. The
   `validate-import-plan` guard accepts only the exact three managed addresses,
   provider scope, the pinned provider's explicit after-attribute closure,
   expected private metadata, no sensitive values, and exactly `actions=[]` for
   every resource. Any unknown attribute, deferred change, deposed instance,
   unresolved value, drift, or replacement is refused.
6. After the no-op plan is accepted, run the separate guarded post-genesis backup
   test. It encrypts the state with the custody age recipient, uploads immutable
   ciphertext/checksum/manifest leaves, reads them back byte-for-byte, and emits
   no values.
7. Run the separate isolated restore rehearsal. It downloads the newest complete
   archive, verifies checksum/manifest, decrypts only in a mode-0700 temporary
   filesystem, checks `TOFU_DISABLE_CHECKPOINT=1 tofu state list` against the same
   exact three addresses, and removes private residue. It never writes the protected state path.
8. Require a second no-op plan after backup/restore, validate its JSON against
   the same exact three-address guard, rerun the exact private-repository API
   postcheck, and compare `TOFU_DISABLE_CHECKPOINT=1 tofu state list` to the
   three imported addresses before accepting the import. All OpenTofu child
   commands, including the final state-list gate, run with
   `TOFU_DISABLE_CHECKPOINT=1`. Source push, workflow enablement, GHCR publication,
   package visibility, collaborators, deployments, Kubernetes, Infisical, DNS,
   and public routing remain separate approvals.

The encrypted backup/readback and isolated restore implementation is the
independent lane in
[`runbooks/opentofu-github-state-backup.md`](opentofu-github-state-backup.md).
Its fixed archive roots, age custody, retention, and timer boundary must not be
changed by this import workflow.

## Rollback and failure handling

There is no remote delete or destructive rollback. Before import, the state file
must be absent and an expiring absence archive must be recoverable. After import,
any non-no-op plan, provider drift, address mismatch, checksum failure, or restore
failure stops the workflow. Preserve the state for review and use Git/provider
state recovery under a separately reviewed operation; never run `tofu destroy`,
`state rm`, `state push`, or a blind re-import.

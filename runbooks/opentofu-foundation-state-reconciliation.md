# Guarded Cloudflare foundation-state reconciliation

## Status

This is a **source-only** closure for importing the already-live
`resume-dev.cristex-soft.com` DNS record into the protected Cloudflare
OpenTofu foundation root. No provider command, state import, state write, backup, restore, or PROD plan
was run while authoring this source. The
reconciliation is a prerequisite to (and not part of) the separately approved
PROD Tunnel/DNS plan.

The only entrypoint is:

```text
opentofu/bin/reconcile-foundation-state check
opentofu/bin/reconcile-foundation-state import
```

It is a direct, non-passthrough `/usr/bin/dash` entrypoint. It accepts no
provider, backend, workspace, address, path, or arbitrary command arguments.
It rejects traced shell execution, inherited provider/OpenTofu overrides,
symlinked or non-canonical source, and source mode/hash drift. A process already
running as the trusted `paul` UID remains outside the source-attestation threat
boundary.

## Exact boundary

| Item | Fixed value |
|---|---|
| OpenTofu root | `/home/paul/projects/cristexweb/opentofu` |
| Backend | `/var/lib/opentofu/cristexweb/foundation.tfstate` |
| Pinned CLI | `/usr/local/bin/tofu` → `/opt/opentofu/1.12.5/tofu` |
| Existing state addresses | five exact Cloudflare/Tunnel addresses |
| Reconciled address | `cloudflare_dns_record.reactive_resume_dev_tailscale` |
| Post-reconciliation state addresses | six exact addresses |
| Record contract | `resume-dev.cristex-soft.com`, A, `100.122.139.32`, DNS-only |
| PROD plan | separate later operation; not run by this entrypoint |

The pre-state closure is:

```text
cloudflare_dns_record.argocd_tailscale
cloudflare_dns_record.cristexhub_dev
cloudflare_dns_record.keycloak
cloudflare_zero_trust_tunnel_cloudflared.keycloak
cloudflare_zero_trust_tunnel_cloudflared_config.keycloak
```

The post-state closure establishes the exact six-address closure and adds exactly:

```text
cloudflare_dns_record.reactive_resume_dev_tailscale
```

The state parent and state file are fixed, regular, non-symlinked, and mode
`0700`/`0600` with the reviewed owner/group contract. A protected `flock` on
the state-parent directory inode is held from the first pre-state inspection
through the import and final checks. The state-list helper validates exact
membership, uniqueness, shape, owner, and mode without requesting provider
state or secret values. The guarded source closure also rejects any extra root
`.tf`, `.tf.json`, auto-variable, override, symlink, directory, or other
non-regular entry (apart from the explicitly allowed `bin`, `github`, and
OpenTofu-generated `.terraform` directories) before a state consumer runs.
OpenTofu's generated data is instead directed to a private mode-`0700`
`TF_DATA_DIR` under the ephemeral work directory, so a clean source root remains
clean after initialization; any pre-existing `.terraform` directory is still
allowlisted only as a non-symlinked directory.

## Required sequence and approvals

1. `check` verifies the complete root source closure, exact OpenTofu binary,
   backend path, protected state paths, and the five-address pre-state. It
   performs no provider command and emits only a sanitized receipt.
2. `import` requires the exact interactive approval:
   `IMPORT EXISTING reactive_resume_dev_tailscale DNS`.
3. Before the state mutation, the entrypoint calls the existing guarded
   foundation state-backup `test` and `restore` gates. They must complete with
   immutable encrypted readback and isolated non-mutating restore evidence. The
   restore manifest must carry the exact `source_closure_sha256` digest, and the isolated
   decrypted state must contain exactly the five-address pre-closure or six-address
   post-closure (with no duplicates or foreign addresses); its receipt emits
   `address_scope=exact-five` or `address_scope=exact-six`. Backup receipts use
   `readback=verified`; restore receipts use `checksum=verified`, `non_mutating=true`,
   an independent `run_id`, matching `source_run_id`/`source_timestamp`, the exact
   address scope, and the current source-closure digest. Duplicate manifest or state
   JSON keys fail closed. Their become prompt remains attached to the controlling
   terminal; passwords are never piped, logged, or entered in chat. The pre-state
   closure is rechecked after recovery.
4. The operator enters the account ID, zone ID, existing DNS record ID, and
   Cloudflare API token through protected prompts. IDs are validated as fixed
   lowercase 32-hex identifiers. The token is transferred to the provider child
   through an anonymous pipe, never argv, a file, plan output, state evidence,
   or a receipt. Provider output is captured in mode-`0600` temporary files and
   is never emitted.
5. The pinned root is initialized with `-lockfile=readonly` and only the exact
   DNS address is imported with the fixed `zone-id/record-id` form. There is no
   create, delete, destroy, state-removal, state-push, or apply path. OpenTofu
   data is isolated under the ephemeral `TF_DATA_DIR`.
6. The six-address post-state is validated, then a provider-backed
   `plan -refresh-only` is rendered and validated as an exact six-address
   no-op. This is a fail-closed state-refresh check and does not authorize the
   pending PROD configuration plan. The backup `test` and isolated `restore`
   gates run again, the six-address closure is validated again, and the
   refresh-only no-op check is repeated.
7. The entrypoint emits a sanitized success receipt saying the PROD plan is a
   separate gate. It does not run or approve that plan.

The refresh-only plan JSON is mode-`0600`, consumed only by the local
source-checked validator, and removed with the ephemeral work directory. The
validator requires exactly the six post-reconciliation managed resources, empty
plan actions, no resource drift, no deferred changes, no output changes, and no
sensitive values; it rejects malformed, expanded, or mutating plans.

The foundation backup/restore source must itself pass its own pinned source,
recipient, rclone, immutable-readback, and isolated-restore contracts. A
backup or restore failure stops the transition and leaves state for operator
review; no blind re-import or destructive rollback is attempted.

## PROD plan boundary

After this reconciliation has separately passed, an operator may review a
new protected plan. The expected subsequent plan is still separate: the
existing Tunnel configuration update plus the `hub.cristex-soft.com` DNS
resource create. It must have its own fresh encrypted foundation-state
backup/readback/restore, provider credential with DNS permission, exact plan
review, private validation, and public-cutover approval. This source does not
run that plan and does not make `hub.cristex-soft.com` public.

## Validation

```bash
sh -n opentofu/bin/reconcile-foundation-state
python3 -m py_compile opentofu/bin/validate-foundation-state-scope
.venv/bin/python -m unittest tests.test_opentofu_foundation_state_reconciliation_contract
```

All commands above are offline/source checks. No provider, protected state,
Google Drive, Infisical, DNS, Tunnel, Kubernetes, or PROD operation is implied
by passing them.

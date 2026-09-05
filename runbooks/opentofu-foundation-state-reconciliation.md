# Guarded Cloudflare foundation-state reconciliation

## Status

This is a **source-only** closure for importing the already-live
`dev-resume.cristex-soft.com` DNS record into the protected Cloudflare
OpenTofu foundation root. No provider command, state import, state write, backup,
restore, or PROD plan was run while authoring this source. The reconciliation is
a prerequisite to (and not part of) the separately approved PROD Tunnel/DNS plan.

The only entrypoint is:

```text
opentofu/bin/reconcile-foundation-state check
opentofu/bin/reconcile-foundation-state import
```

It is a direct, non-passthrough `/usr/bin/dash` entrypoint. It accepts no
provider, backend, workspace, address, path, or arbitrary command arguments.
It rejects traced shell execution, inherited provider/OpenTofu/plugin overrides
(including `TF_*`, `TOFU_*`, `OPENTOFU_*`, and dynamic-loader `LD_*`/`DYLD_*`),
symlinked or non-canonical source, and source mode/hash drift. A process already
running as the trusted `paul` UID remains outside the source-attestation threat
boundary. Metadata/dev:ino checks are consistency checks, not a claim to defeat
a coordinated trusted-UID or root pathname replacement between the final check
and a consumer.

## Exact boundary

| Item | Fixed value |
|---|---|
| OpenTofu root | `/home/paul/projects/cristexweb/opentofu` |
| Backend | `/var/lib/opentofu/cristexweb/foundation.tfstate` |
| Pinned CLI | `/usr/local/bin/tofu` → `/opt/opentofu/1.12.5/tofu` |
| Existing state addresses | five exact Cloudflare/Tunnel addresses |
| Reconciled address | `cloudflare_dns_record.reactive_resume_dev_tailscale` |
| Post-reconciliation state addresses | six exact addresses |
| Record contract | `dev-resume.cristex-soft.com`, A, `100.122.139.32`, DNS-only |
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
`0700`/`0600` with the reviewed owner/group contract. The directory contract
accepts the normal Debian link count (at least two); only state/capture regular
files require a single link. A protected `flock` on the state-parent directory
inode is held from the first pre-state inspection through the import and final
checks. State metadata (path, owner, mode, type, link count, and realpath) plus
the state file device/inode identity are revalidated after acquiring the lock and immediately
before every state consumer, backup gate, import, and plan/show operation; this
metadata check never reads state bytes. The exact five-address pre-import and exact
six-address post-import state-list helper validates membership, cardinality,
uniqueness, shape, owner, and mode without requesting secret values. The
protected state JSON proof validates root-only managed resources, provider
identity, imported DNS
values, five non-sensitive outputs, the hyphenated Tunnel UUID, and the allowed
null-only nested `sensitive_values.tunnel_secret` marker. Both backup and isolated-restore
state-list calls use the pinned `/usr/local/bin/tofu` target through
`/usr/bin/env -i` with exactly `TF_CLI_CONFIG_FILE=/dev/null`, a mode-0700
ephemeral `TF_DATA_DIR`, `TF_WORKSPACE=default`, and
`TOFU_DISABLE_CHECKPOINT=1`; the fixed state path is passed explicitly
(`/var/lib/opentofu/cristexweb/foundation.tfstate` for the backup and the
isolated temporary state for restore). They reject inherited OpenTofu CLI,
backend, provider, registry, and proxy override variables before any recovery
operation, and never collapse duplicate state addresses into a set. Every
embedded Python validator is invoked through a clean `env -i` environment with
`PYTHONNOUSERSITE=1` and `PYTHONDONTWRITEBYTECODE=1`; inherited `PYTHON*`
overrides (including `PYTHONOPTIMIZE`, `PYTHONPATH`, and `PYTHONHOME`) are
rejected before any validator runs. The validators use explicit exceptions and
exit statuses rather than security-sensitive Python `assert` statements, so
optimized Python cannot bypass manifest or state-closure checks. The
guarded source closure also rejects any extra root `.tf`, `.tf.json`,
auto-variable, override, symlink, directory, or other non-regular entry (apart
from the explicitly allowed `bin`, `github`, and OpenTofu-generated
`.terraform` directories) before a state consumer runs. OpenTofu's generated
data is instead directed to a private mode-`0700` `TF_DATA_DIR` under the
ephemeral work directory, so a clean source root remains clean after
initialization; any pre-existing `.terraform` directory is still allowlisted
only as a non-symlinked directory.

## Required sequence and approvals

1. `check` verifies the complete root source closure, exact OpenTofu binary,
   backend path, protected state paths, and the five-address pre-state. It first
   runs the pinned clean `tofu init -reconfigure -input=false -lockfile=readonly
   -no-color` with an ephemeral `TF_DATA_DIR`. This may initialize or download
   the locked provider package from the OpenTofu registry, but it receives no
   Cloudflare token and performs no Cloudflare provider/API operation. Registry
   or provider-package initialization failure stops the check; only the
   subsequent state validation emits the sanitized check receipt.
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
   JSON keys and non-standard JSON constants fail closed. Their become prompt remains attached to the controlling
   terminal; passwords are never piped, logged, or entered in chat. The restore
   catalog captures every rclone listing directly and fails closed on any listing
   error. It considers only strict UTC timestamp directories with no nested
   directories and the exact three leaves `foundation.tfstate.age`,
   `foundation.tfstate.age.sha256`, and `manifest.json`; extra leaves and duplicate
   leaves are rejected, while newer incomplete directories are ignored without
   remote deletion. The newest complete candidate is selected, and the pre-state
   closure is rechecked after recovery.
4. The operator enters the account ID, zone ID, all four existing DNS record IDs
   (Argo, CristexHub DEV, Keycloak, and Reactive Resume DEV), and the Cloudflare
   API token through protected prompts. The account and zone must equal the fixed
   foundation identities; every record ID is a distinct lowercase 32-hex value and
   is written to a temporary identity profile. The post-import state proof and
   every refresh-only prior-state proof require the exact four IDs and fixed zone;
   no sparse or format-only DNS projection is accepted. The profile also binds the
   fixed Tunnel UUID and account tag to the exact Tunnel and Tunnel-config
   resources, and the validator checks the exact three current ingress rules,
   including hostname, service, null path, and null origin-request semantics. The
   PROD plan validator binds every existing record ID and the same Tunnel account
   tag to its descriptor-bound identity profile. The
   token is transferred to the provider child
   through an anonymous pipe, never argv, a file, plan output, state evidence,
   or a receipt. Provider output is captured in mode-`0600` temporary files and
   is never emitted.
5. The pinned root has already been initialized by the clean `-reconfigure`
   operation above, using only the locked provider package and ephemeral
   `TF_DATA_DIR`; that initialization may contact the OpenTofu registry but does
   not contact Cloudflare. Only the exact DNS address is then imported with the
   fixed `zone-id/record-id` form. There is no create, delete, destroy,
   state-removal, state-transfer, or apply path. OpenTofu data remains isolated
   under the ephemeral `TF_DATA_DIR`.
6. The exact six-address post-state is validated through both `state list` and
   `show -json`; the imported DNS values are proved by the protected state JSON
   proof. A provider-backed `plan -refresh-only` is then rendered and validated
   as a no-drift envelope. OpenTofu 1.12.5 may omit `resource_changes` and emits
   `planned_values.root_module` as an empty object; the validator requires that
   exact empty root, exact five variables, the exact seven-resource source
   configuration closure (including source-only PROD), five no-op outputs, and
   empty drift/deferred/check surfaces. This exact seven-resource configuration
   closure and exact five-variable closure do not authorize the
   pending PROD configuration plan. The backup `test` and isolated `restore`
   gates run again, and all post-state/plan proofs are repeated.
7. The entrypoint emits a sanitized success receipt saying the PROD plan is a
   separate gate. It does not run or approve that plan.

The refresh-only plan-envelope proof consumes a mode-`0600` plan JSON only in
the local source-checked validator. A provenance sidecar is mandatory; missing
or path-only provenance is refused. Both guarded producers create each capture
with `O_CREAT|O_EXCL|O_NOFOLLOW` and retain the verified descriptor; after every
producer returns, the reconciler revalidates the source closure and state
metadata. Immediately before every validator execution, it repeats the source
closure/state check, hashes the validator against its pinned manifest digest,
and copies it into a sealed Linux memfd. Pathname inputs are opened once with
`O_NONBLOCK|O_NOFOLLOW`, checked as mode-`0600` regular files, and passed by
verified descriptor; a FIFO replacement therefore fails immediately rather than
blocking. The child executes only those immutable verified bytes; pathname
replacement or in-place mutation cannot
change validator code after the last check. The
reconciler and PROD route planner pass device/inode receipts and the validators
consume `fd:N`, never reopening the capture by pathname. The binary plan is
likewise held on one verified descriptor for both `plan -out=/proc/self/fd/N`
and `show`, so a FIFO or regular-file pathname replacement cannot redirect
 either consumer. A sanitized mode-`0600` provenance receipt is itself passed
by descriptor and binds the plan JSON digest to the pinned
OpenTofu 1.12.5 path/digest and Cloudflare 5.23.0; the validator requires that
receipt before accepting the plan. Each producer applies an inherited
`RLIMIT_FSIZE` of exactly 16 MiB per stdout, stderr, and binary-plan capture,
and verifies final descriptor sizes before returning; an oversized stream fails
closed while retaining at most the bounded diagnostics. The sealed validator
runner rejects source files larger than 256 KiB before allocating or hashing
their bytes. The JSON validators cap each input at 4 MiB and enforce a
15-second validation deadline. A producer failure still executes the
post-producer source/state revalidation, including the protected state content
hash, before reporting its failure. HUP/INT/TERM traps remove private staging
and then exit nonzero; cleanup cannot fall through into provider work. They reject inherited `TF_*`,
`TOFU_*`, `OPENTOFU_*`, `TF_PLUGIN_CACHE_DIR`, and
`LD_*`/`DYLD_*` overrides along with Python/provider overrides. It requires the
exact seven-resource configuration closure and exact five-variable closure, the
complete `planned_values.outputs` and `prior_state` projections, and no
provisioner/count/for_each/dependency additions. Each resource expression,
including the ingress expression, provider configuration, output references,
and marker/sensitivity field is compared to OpenTofu 1.12.5's actual reference
expression tree rather than substituting evaluated constants or checking only
key names. The plan proof
deliberately does not infer state membership from `planned_values`:
OpenTofu 1.12.5's valid refresh-only no-op has an empty `root_module` and may
omit `resource_changes`. It instead requires exact variables/configuration
closures, exactly five output changes with `actions=["no-op"]`, equal before/after
values, required false sensitivity/unknown markers, and empty drift/deferred/relevant/check
surfaces. Top-level `checks: []` is accepted; non-empty or malformed checks,
configuration, variables, outputs, prior state, arbitrary secret/token-shaped
fields, or nested sensitive markers fail closed.

The foundation backup/restore source must itself pass its own pinned source,
recipient, rclone, immutable-readback, and isolated-restore contracts. A
backup or restore failure stops the transition and leaves state for operator
review; no blind re-import or destructive rollback is attempted.

## PROD plan boundary

After this reconciliation has separately passed, an operator may review a
new protected plan through the separate guarded entrypoint:

```text
opentofu/bin/plan-foundation-prod-route check
opentofu/bin/plan-foundation-prod-route plan
```

`check` proves the exact six-address protected state without contacting the
provider. `plan` is a separate provider-backed plan-only operation; it never apply and never performs state mutation. The expected plan has exactly two changes: the existing Tunnel configuration update and the
`hub.cristex-soft.com` DNS resource create, with the new ingress inserted
immediately before the existing terminal `http_status:404` rule. The reviewed
identity binding is account `8b0f511214c7a4a52ddfb62ca92c5e80`, zone
`3cbee16e56d7656440f93e685807e779`, and Tunnel
`f9442440-96df-4cf1-855b-7257868ed9bc`; those values remain plan-input
contracts, not credentials or approval. The validator rejects no replacement, destroy, deferred, unknown, or sensitive values. It never authorizes an apply.

The expected subsequent plan is still separate from this reconciliation. It
must have its own fresh encrypted foundation-state backup/readback/restore,
provider credential with DNS permission, exact plan review, private validation,
and public-cutover approval. This source does not run that plan and does not
make `hub.cristex-soft.com` public.

## Validation

```bash
sh -n opentofu/bin/reconcile-foundation-state
sh -n ansible/files/backup/opentofu-state-backup
sh -n ansible/files/backup/restore-opentofu-state-rehearsal
python3 -m py_compile opentofu/bin/validate-foundation-state-scope
python3 -m unittest tests.test_opentofu_foundation_state_reconciliation_contract
.venv/bin/python -m unittest tests.test_opentofu_state_backup_contract tests.test_opentofu_foundation_state_reconciliation_contract
```

All commands above are offline/source checks. The source checks do not run
`tofu init`; the guarded wrapper's `check` does run its pinned initialization,
which can contact the OpenTofu registry for the locked provider package but does
not contact Cloudflare or use a token. No protected-state mutation, Google Drive,
Infisical, DNS, Tunnel, Kubernetes, or PROD operation is implied by passing them.

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
membership, list cardinality, uniqueness, shape, owner, and mode without
requesting provider state or secret values. Both backup and isolated-restore
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
   JSON keys and non-standard JSON constants fail closed. Their become prompt remains attached to the controlling
   terminal; passwords are never piped, logged, or entered in chat. The restore
   catalog captures every rclone listing directly and fails closed on any listing
   error. It considers only strict UTC timestamp directories with no nested
   directories and the exact three leaves `foundation.tfstate.age`,
   `foundation.tfstate.age.sha256`, and `manifest.json`; extra leaves and duplicate
   leaves are rejected, while newer incomplete directories are ignored without
   remote deletion. The newest complete candidate is selected, and the pre-state
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
validator requires exactly the six post-reconciliation managed resources with
`["no-op"]` actions, the exact five declared root outputs as nonsensitive
`["no-op"]` entries with concrete equal before/after values, the exact five passing
source-variable checks, and the exact dependency paths emitted by OpenTofu. It
requires no resource drift and no unknown/deferred surface. It models the pinned
Cloudflare provider 5.23.0 DNS/Tunnel computed-field schema with explicit
allowlists and types; every computed/unintended field present in a no-op must be
present and exactly equal before and after. It rejects malformed, expanded,
unknown, sensitive, or mutating plans. Its configuration projection is
source-bound: provider/resource/output/variable expressions are exact, and the
provider token expression is accepted only as the fixed sanitized fixture
placeholder. Real provider credentials are never accepted in plan JSON, even
when a caller supplies a matching digest. A mode-0600 identity profile is
byte-hash-bound into the wrapper attestation before provider planning; the
validator consumes that exact mode-0600 attestation and rejects direct unbound
invocation. Its DNS IDs and tunnel account tag must match the exact prior-state
projection, not merely a format or before/after comparison. The offline fixture's
one-to-one sanitization receipt is consumed by the contract tests and never
represents live identity values.

The foundation backup/restore source must itself pass its own pinned source,
recipient, rclone, immutable-readback, and isolated-restore contracts. A
backup or restore failure stops the transition and leaves state for operator
review; no blind re-import or destructive rollback is attempted.

## PROD plan boundary

After the six-address reconciliation has separately passed, the only entrypoint
for the pending route plan is the source-only guarded wrapper:

```text
opentofu/bin/plan-foundation-prod-route check
opentofu/bin/plan-foundation-prod-route plan
```

`check` validates the exact six-address protected state without contacting the
provider. `plan` is provider-backed but plan-only; this provider-backed plan
requires the exact
interactive approval `PLAN PROD ROUTE 6 TO 7`, prompts for the fixed account/zone
IDs, the tunnel `account_tag`, every existing DNS record ID in the six-address
prestate, and the token through protected input. Provider output and the plan JSON
are mode-`0600` ephemeral artifacts; the validator refuses any token-bearing JSON
rather than treating a digest as proof of safety. The wrapper creates a
mode-`0600` ephemeral identity profile from those prompts; the validator requires
that profile and compares every DNS ID/account tag exactly, never merely by
format or by before/after equality. The account, zone, and tunnel IDs are fixed
semantic values.

The token crosses the provider process boundary through an anonymous pipe into a
clean same-UID child. That child reads stdin, exports
`CLOUDFLARE_API_TOKEN` immediately before execing pinned OpenTofu 1.12.5, and
uses no sudo, PTY, or privileged I/O-logging policy. No token is placed in argv,
a caller-supplied/inherited environment, plans, logs, or files before the
provider child starts. Because the provider contract requires an environment
variable, the token-bearing child environment can be observable to a same-UID
process or privileged observer; this lane makes no `/proc` confidentiality
claim. Both modes use a clean environment, `TF_CLI_CONFIG_FILE=/dev/null`,
`TF_DATA_DIR` under a private temporary filesystem, `TF_WORKSPACE=default`,
`TOFU_DISABLE_CHECKPOINT=1`, and the protected foundation state path.

The wrapper validates the state list before planning as exactly these six
addresses, with no duplicates or foreign resources:

```text
cloudflare_dns_record.argocd_tailscale
cloudflare_dns_record.cristexhub_dev
cloudflare_dns_record.keycloak
cloudflare_dns_record.reactive_resume_dev_tailscale
cloudflare_zero_trust_tunnel_cloudflared.keycloak
cloudflare_zero_trust_tunnel_cloudflared_config.keycloak
```

The local `validate-foundation-prod-plan` validator accepts exactly seven plan
resource entries: the six existing resources, one
`cloudflare_zero_trust_tunnel_cloudflared_config.keycloak` update that adds only
one `hub.cristex-soft.com` ingress immediately before the existing terminal
`http_status:404` rule, and one `cloudflare_dns_record.cristexhub_prod` create
with the exact proxied CNAME contract. The protected identity is fixed to
account `8b0f511214c7a4a52ddfb62ca92c5e80`, zone
`3cbee16e56d7656440f93e685807e779`, and Tunnel
`f9442440-96df-4cf1-855b-7257868ed9bc`; DNS target and all existing no-op
configuration fields must match those exact values. Existing ingress order and
content are compared as a complete list, not as an unordered set. DNS provider
computed fields (`id`, timestamps, `proxiable`, `data`, `meta`, `priority`,
`private_routing`, `settings`, `tags`, and tag timestamps) and Tunnel provider
fields (`account_tag`, `connections`, connection timestamps, `metadata`,
`remote_config`, `status`, `tun_type`, and null-only `tunnel_secret`) use
explicit allowlists/types and must not drift. OpenTofu
1.12.5 encodes a no-op action as `["no-op"]`; the route create carries explicit
`before: null` and `before_sensitive: false`, while update/no-op entries carry
both concrete state values. The five root output changes are validated as
`["no-op"]` with concrete equal before/after values, matching the pinned CLI's actual output
projection. The exact policy is: no replacement, destroy, deferred, unknown, or sensitive values.
The same-UID integrity boundary is explicit: a process already running as the
trusted controller UID is outside the claim; all source, identity, and wrapper
hashes nevertheless fail closed for ordinary tampering or untrusted ancestry.
The validator rejects non-empty replacement/deposed/action-reason,
deferred, unknown, or sensitive metadata; it also requires exactly the five
`outputs.tf` output names (`tunnel_id`, `tunnel_name`, `public_hostname`,
`dns_record_name`, and `token_handoff`) as exact no-op entries whose concrete before/after values are fixed and equal. It rejects delete,
changed/extra/missing output,
drift, duplicate, foreign, malformed, or schema-incompatible changes and any
unknown top-level/resource/change keys. Documented optional 1.12.5 envelope,
resource, and change fields are accepted only when they have their exact safe
empty/value form.
The wrapper also hashes the state before and after all plan/show operations and
refuses any state mutation. It never runs `tofu apply`, import, destroy, state
removal, or state push, and it does not make `hub.cristex-soft.com` public.

`planned_values` and `prior_state` are recursively schema-bounded: their root
modules, resource identities, values, sensitive markers, and output maps must
match the corresponding validated change projection exactly. Sensitive-looking
keys (including `tunnel_secret`) are rejected when non-null even if a forged
sensitivity marker says false. OpenTofu 1.12.5 create changes must carry
`before: null` and `before_sensitive: false`; omission or substitution is refused.

The exact two-change plan is exactly two changes and still requires its own fresh encrypted
foundation-state backup/readback/restore, provider credential with DNS
permission, private validation, and separate public-cutover approval before any
future apply. The wrapper must never apply; no apply is authorized by this source-only plan
wrapper or by a passing validator.

## Validation

```bash
sh -n opentofu/bin/reconcile-foundation-state
sh -n opentofu/bin/plan-foundation-prod-route
sh -n ansible/files/backup/opentofu-state-backup
sh -n ansible/files/backup/restore-opentofu-state-rehearsal
python3 -m py_compile opentofu/bin/validate-foundation-state-scope
python3 -m py_compile opentofu/bin/validate-foundation-prod-plan
.venv/bin/python -m unittest tests.test_opentofu_state_backup_contract tests.test_opentofu_foundation_state_reconciliation_contract
.venv/bin/python -m unittest tests.test_opentofu_foundation_prod_plan_contract
```

These are source-only checks. They do not invoke the PROD `plan` wrapper, the
OpenTofu provider, Cloudflare, or any apply path.

All commands above are offline/source checks. No provider, protected state,
Google Drive, Infisical, DNS, Tunnel, Kubernetes, or PROD operation is implied
by passing them.

# Cloudflare OpenTofu source

This is no longer a zero-resource scaffold: it contains only the reviewed
Cloudflare Tunnel and DNS resource boundaries described below.

The private standalone GitHub repository boundary is intentionally a separate
source root at [`opentofu/github`](github/README.md), with independent state
`/var/lib/opentofu/cristexweb/github.tfstate`. Never combine that root with this
Cloudflare root or reuse this root's state. The existing private repository import
workflow is documented at
[`runbooks/opentofu-github-repository-import.md`](../runbooks/opentofu-github-repository-import.md);
it imports only the exact existing addresses and requires protected no-op-plan,
encrypted backup/readback, and isolated-restore gates.

This module is initialized against protected host state. The protected local backend
at `/var/lib/opentofu/cristexweb/foundation.tfstate` contains exactly five imported
resource addresses: the Tunnel, its configuration, Keycloak DNS, DEV DNS, and the
private Argo DNS record. The older checkpoint described six resource addresses;
the current committed source defines seven resource addresses.
`cloudflare_dns_record.reactive_resume_dev_tailscale` is already live but remains a
separate source-only import prerequisite, and `cloudflare_dns_record.cristexhub_prod`
remains absent from state. The guarded reconciliation is documented in
[`runbooks/opentofu-foundation-state-reconciliation.md`](../runbooks/opentofu-foundation-state-reconciliation.md)
and must establish the exact six-address state closure before any PROD plan. The
source-only `opentofu/bin/plan-foundation-prod-route` wrapper then provides the
separate check/plan-only gate. The protected route identity is fixed to account
`8b0f511214c7a4a52ddfb62ca92c5e80`, zone
`3cbee16e56d7656440f93e685807e779`, and Tunnel
`f9442440-96df-4cf1-855b-7257868ed9bc`; these are public resource identifiers,
not credentials. It accepts exactly one Tunnel-config update adding
the reviewed `hub.cristex-soft.com` ingress and one proxied DNS-record create,
with no replacement, destroy, deferred, unknown, sensitive, or state mutation. Its
exact five root outputs are required as nonsensitive `["no-op"]` entries with
concrete equal before/after values. No
provider/state operation has run for either pending change. The Argo CD and
Reactive Resume DEV records point to current Tailscale IPv4 `100.122.139.32`;
access remains restricted by the host/cluster Tailscale-only ingress boundary and
is not routed through the Cloudflare proxy or Tunnel.

The guarded foundation reconciliation initializes with `-lockfile=readonly` and
uses a private ephemeral `TF_DATA_DIR`, keeping a clean source root free of
OpenTofu-generated provider data. After the exact sixth-address import it runs a
provider-backed `plan -refresh-only` twice (before and after backup recovery).
A local mode-`0600` validator accepts only the exact six managed resources with
`["no-op"]` actions and requires the exact five declared root outputs as
nonsensitive no-ops with concrete equal before/after values. It also requires the exact
five passing source-variable checks and dependency paths emitted by OpenTofu.
The validator models the pinned Cloudflare 5.23.0 DNS and
Tunnel computed-field schema, requiring every provider-emitted computed field on
both sides of a no-op and rejecting computed drift, deferred changes, sensitive
values, or any expanded/mutating plan. The PROD validator consumes a mode-0600
identity attestation from the canonical wrapper and rejects direct unbound
invocation. This state-refresh gate does not run or authorize
the separate PROD Tunnel/DNS plan.

## State and secret boundary

The Cloudflare provider stores resource arguments and provider-managed attributes
in OpenTofu state. The `cloudflare_zero_trust_tunnel_cloudflared` resource accepts
an optional `tunnel_secret`; this module deliberately does **not** set it. It also
does not use the `cloudflare_zero_trust_tunnel_cloudflared_token` data source or
expose a token output. Therefore this source does not retrieve or intentionally
place a Tunnel token in state. The completed token handoff used the separately
approved Cloudflare/Infisical path and writes only to the runtime secret path; the
token must never be passed through OpenTofu variables, tfvars, CLI arguments,
environment examples, plans, outputs, or state. This source neither retrieves nor
prints it.

OpenTofu outputs contain only the Tunnel UUID/name, hostname, DNS record name, and
the explicit marker `MANUAL_INFISICAL_HANDOFF_REQUIRED`. The tunnel UUID is not a
secret. The committed `.terraform.lock.hcl` pins the reviewed provider selection;
state, plans, credentials, and provider cache remain uncommitted and protected.
`prevent_destroy` is set on every resource to avoid accidental public-route,
private-DNS, or tunnel deletion.

## Inputs

- `cloudflare_account_id`: required 32-character lowercase hexadecimal account ID.
- `cloudflare_zone_id`: required 32-character lowercase hexadecimal zone ID for
  `cristex-soft.com`.
- `cloudflare_tunnel_name`: defaults to `cristexhub-keycloak`.
- `public_hostname`: fixed to `auth.cristex-soft.com`.
- `traefik_origin_service`: defaults to the private cluster Traefik Service URL.

The private Argo CD record is intentionally fixed to `argo.cristex-soft.com`,
`100.122.139.32`, DNS-only (`proxied = false`), with a 300-second TTL. A
Tailscale address in public DNS is not itself an access control mechanism;
private ingress enforcement and tailnet membership remain required.

Identifiers must be supplied through an uncommitted variable mechanism after
provider-backed work is separately approved. No credentials, tfvars, plans,
`.terraform` directory, or state file are committed here. The provider lockfile is
intentionally tracked so its exact selection is reviewable.

## Completed Tunnel handoff and pending PROD route

The imported Tunnel UUID was recorded without secret output. Its token was recovered
through the approved Infisical path `prod:/platform-edge/cloudflared`, key
`CLOUDFLARE_TUNNEL_TOKEN`, and materialized into the live `platform-edge`
cloudflared workload through the guarded lane. Token-bearing material remains absent
from Git, OpenTofu state/plan/output, argv, evidence, and manifests. The PROD route
adds no token. It still requires a protected DNS-capable provider
credential and separate approvals for Tunnel-config mutation, DNS publication, and
public cutover. Before any apply, require a fresh encrypted state backup/readback,
independent-key restore rehearsal, and an exact reviewed plan containing only the
Tunnel-config update and `cloudflare_dns_record.cristexhub_prod` create, with no
replacement or destroy actions. This module does not create Kubernetes resources,
install cloudflared, create the Infisical secret, create a Traefik route, or approve
public cutover. Those are separate ownership and approval boundaries.

The local backend remains a single-node failure domain and protected single-writer
boundary. Encrypted timestamped off-node copy/readback, independent-key retrieval,
integrity verification, and isolated `tofu state list` restore rehearsal have passed.
After a future approved apply, post-validation must include provider/API state
verification, a second no-op plan, positive `hub.cristex-soft.com` authentication
and routing tests, negative admin/management/DEV/Argo/data/direct-origin tests, and
rollback evidence. These controls do not authorize the pending PROD route.

### Provider credential process boundary

The provider credential is read only from protected terminal input and crosses to
OpenTofu through an anonymous pipe. It is never placed in argv, a caller-supplied
or inherited environment, a plan, a log, or a file. OpenTofu's Cloudflare
provider requires `CLOUDFLARE_API_TOKEN` in its process environment, so a clean
same-UID child reads the token from stdin, exports it immediately before exec,
and runs the pinned OpenTofu 1.12.5 binary. No sudo, setuid-root transition,
PTY, or sudoers I/O-logging policy is assumed. As required by this provider
contract, the token-bearing child environment may be observable to a same-UID
process or privileged observer; this lane makes no `/proc` confidentiality
claim. The local validator rejects token-bearing JSON unconditionally, even if
a caller supplies a matching digest, accepting only the fixed sanitized fixture
placeholder.

## Encrypted state recovery boundary

The Ansible-owned host workflow `configure-opentofu-state-backup` is the only
approved source for encrypted local state copies. It protects
`/var/lib/opentofu/cristexweb/foundation.tfstate`, encrypts with the public age
recipient, uploads immutable timestamped leaves to Google Drive under
`drive:cristexweb-recovery/opentofu/foundation/`, and reads them back byte-for-byte.
The private identity is retrieved only during the isolated restore rehearsal from
Infisical `prod:/shared-services/backup-recovery`; it is never retained on the
host, in OpenTofu state, or in Git. Approved backup, decrypt, `tofu state list` validation, cleanup, and non-mutation
restore rehearsal have passed. Restore selects the newest strict UTC timestamp
archive with no nested directories and exactly the three expected leaves;
newer incomplete or extra-leaf directories are ignored without remote deletion,
while duplicate candidates and every rclone listing error fail closed. Source
authoring itself still runs no backup or restore command.

The separate GitHub root has an independent, fixed source-only backup lane at
[`runbooks/opentofu-github-state-backup.md`](../runbooks/opentofu-github-state-backup.md).
It protects only `/var/lib/opentofu/cristexweb/github.tfstate`, stores encrypted
leaves only under `opentofu/github`, and uses unique executables, lock, systemd
units, timer, wrapper, and playbook. It does not read, write, start, stop, enable, disable, or restore the foundation
state/timer. Before the GitHub state producer exists, its dedicated absence
attestation/readback/restore records only the missing-state condition and never
manufactures `github.tfstate`; post-genesis backup/readback/restore remain unrun
until the state producer and separate approvals exist.

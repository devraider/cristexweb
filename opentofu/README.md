# Cloudflare OpenTofu source

This is no longer a zero-resource scaffold: it contains only the reviewed
Cloudflare Tunnel and DNS resource boundaries described below.

The private standalone GitHub repository boundary is intentionally a separate
source root at [`opentofu/github`](github/README.md), with independent state
`/var/lib/opentofu/cristexweb/github.tfstate`. Never combine that root with this
Cloudflare root or reuse this root's state.

This module is initialized against protected host state. The protected local backend
at `/var/lib/opentofu/cristexweb/foundation.tfstate` contains exactly five imported
resource addresses: the Tunnel, its configuration, Keycloak DNS, DEV DNS, and the
private Argo DNS record. The committed source defines six resource addresses; only
`cloudflare_dns_record.cristexhub_prod` is absent from the imported state. The PROD
change is therefore still pending: one Tunnel-config update adding the reviewed
`hub.cristex-soft.com` ingress and one proxied DNS-record create. No apply has run
for that pending change. The Argo CD record points to current Tailscale IPv4
`100.122.139.32`; access remains restricted by the host/cluster Tailscale-only
ingress boundary and is not routed through the Cloudflare proxy or Tunnel.

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
from Git, OpenTofu state/plan/output, argv, evidence, and manifests. The PROD route adds no token. It still requires a protected DNS-capable provider
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

## Encrypted state recovery boundary

The Ansible-owned host workflow `configure-opentofu-state-backup` is the only
approved source for encrypted local state copies. It protects
`/var/lib/opentofu/cristexweb/foundation.tfstate`, encrypts with the public age
recipient, uploads immutable timestamped leaves to Google Drive under
`drive:cristexweb-recovery/opentofu/foundation/`, and reads them back byte-for-byte.
The private identity is retrieved only during the isolated restore rehearsal from
Infisical `prod:/shared-services/backup-recovery`; it is never retained on the
host, in OpenTofu state, or in Git. Approved backup, decrypt, `tofu state list` validation, cleanup, and non-mutation
restore rehearsal have passed. Source authoring itself still runs no backup or
restore command.

The separate GitHub root has an independent, fixed source-only backup lane at
[`runbooks/opentofu-github-state-backup.md`](../runbooks/opentofu-github-state-backup.md).
It protects only `/var/lib/opentofu/cristexweb/github.tfstate`, stores encrypted
leaves only under `opentofu/github`, and uses unique executables, lock, systemd
units, timer, wrapper, and playbook. It does not read, write, enable, disable, or
restore the foundation state/timer. Backup, readback, and isolated restore remain
unrun until the GitHub state producer and separate approvals exist.

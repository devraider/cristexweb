# Cloudflare OpenTofu source

This is no longer a zero-resource scaffold: it contains only the reviewed
Cloudflare Tunnel and DNS resource boundaries described below.

This module is initialized against protected host state. The existing remotely
managed Tunnel, its active Keycloak/DEV ingress configuration, the Keycloak/DEV
proxied CNAMEs, and the private Argo DNS record are imported and managed. Source now
adds the exact PROD Tunnel ingress and proxied CNAME, but that two-change plan has
not completed because the available OAuth credential lacks DNS-record permission.
The Argo CD record points to the current
Tailscale IPv4 `100.122.139.32`; access remains restricted by the host/cluster
Tailscale-only ingress boundary and is not routed through the Cloudflare proxy
or Tunnel.

## State and secret boundary

The Cloudflare provider stores resource arguments and provider-managed attributes
in OpenTofu state. The `cloudflare_zero_trust_tunnel_cloudflared` resource accepts
an optional `tunnel_secret`; this module deliberately does **not** set it. It also
does not use the `cloudflare_zero_trust_tunnel_cloudflared_token` data source or
expose a token output. Therefore this source does not retrieve or intentionally
place a Tunnel token in state. The resulting token must still be obtained through
the separately approved Cloudflare/Infisical handoff and written only to the
runtime secret path; it must never be passed through OpenTofu variables, tfvars,
CLI arguments, environment examples, plans, outputs, or state.

OpenTofu outputs contain only the Tunnel UUID/name, hostname, DNS record name, and
the explicit marker `MANUAL_INFISICAL_HANDOFF_REQUIRED`. The tunnel UUID is not a
secret. `prevent_destroy` is set on every resource to avoid accidental public-route,
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
provider-backed work is separately approved. No credentials, account IDs, zone
IDs, tfvars, plans, provider lockfile, `.terraform` directory, or state file are
committed here.

## Completed Tunnel handoff and pending PROD route

The imported Tunnel UUID was recorded without secret output. Its token was recovered
through the approved Infisical path `prod:/platform-edge/cloudflared`, key
`CLOUDFLARE_TUNNEL_TOKEN`, and materialized into the live `platform-edge`
cloudflared workload through the guarded lane. Token-bearing material remains absent
from Git, OpenTofu state/plan/output, argv, evidence, and manifests. The PROD route
adds no token; it still requires a protected DNS-capable provider credential and an
exact reviewed plan/apply.

This module does not create Kubernetes resources, install cloudflared, create the
Infisical secret, create a Traefik route, or approve public cutover. Those are
separate ownership and approval boundaries. The local backend remains a single-node failure domain and is operated as a protected single-writer boundary. Encrypted timestamped
off-node copy/readback, independent-key retrieval, integrity verification, and an
isolated `tofu state list` restore rehearsal now pass. These controls do not authorize
the pending PROD route.

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

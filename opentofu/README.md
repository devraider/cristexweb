# Cloudflare OpenTofu source

This is no longer a zero-resource scaffold: it contains only the reviewed
Cloudflare Tunnel and DNS resource boundaries described below.

This module is source-only and has not been initialized, planned, applied, or
used against the Cloudflare API. It manages exactly one remotely managed
Cloudflare Tunnel, its remote public-hostname configuration, and the proxied
CNAME for `auth.cristex-soft.com`.

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
secret. `prevent_destroy` is set on all three resources to avoid accidental
public-route or tunnel deletion.

## Inputs

- `cloudflare_account_id`: required 32-character lowercase hexadecimal account ID.
- `cloudflare_zone_id`: required 32-character lowercase hexadecimal zone ID for
  `cristex-soft.com`.
- `cloudflare_tunnel_name`: defaults to `cristexhub-keycloak`.
- `public_hostname`: fixed to `auth.cristex-soft.com`.
- `traefik_origin_service`: defaults to the private cluster Traefik Service URL.

Identifiers must be supplied through an uncommitted variable mechanism after
provider-backed work is separately approved. No credentials, account IDs, zone
IDs, tfvars, plans, provider lockfile, `.terraform` directory, or state file are
committed here.

## Required handoff (not executed)

After a reviewed OpenTofu apply creates the Tunnel, record its output UUID without
secret values. Separately create/recover the remotely managed Tunnel token from
Cloudflare, transfer it through the approved Infisical path
`prod:/platform-edge/cloudflared` under `CLOUDFLARE_TUNNEL_TOKEN`, and materialize
it into the future `platform-edge` cloudflared workload using a guarded Ansible /
Infisical lane. Verify token-bearing material never appears in Git, OpenTofu
state/plan/output, argv, environment evidence, Kubernetes manifests, or logs.

This module does not create Kubernetes resources, install cloudflared, create the
Infisical secret, create a Traefik route, or approve public cutover. Those are
separate ownership and approval boundaries. The current local backend remains a
single-node failure domain; encrypted timestamped off-node copies to Google Drive,
independent key recovery, integrity verification, and isolated restore are
prerequisites before any provider-backed plan or apply. Until that evidence exists,
state recovery is `UNKNOWN — STOP` and no apply is permitted.

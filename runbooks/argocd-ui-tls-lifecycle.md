# Private Argo CD UI TLS lifecycle

This source-only contract selects a browser-trusted ACME certificate for
`https://argo.cristex-soft.com` while keeping the endpoint DNS-only and reachable
only through the Tailscale boundary. It does not create a Cloudflare Tunnel or
proxy the record.

## Exact ownership

- Cloudflare/OpenTofu owns only the DNS-only `argo.cristex-soft.com` A record.
- A guarded controller performs ACME DNS-01 using a narrowly scoped Cloudflare
  DNS credential. The credential is entered through hidden input or supplied from
  an approved protected file; it never enters Git, argv, environment evidence,
  logs, OpenTofu state, or Kubernetes.
- The controller uploads only `ARGOCD_UI_TLS_CRT` and `ARGOCD_UI_TLS_KEY` to
  Infisical `prod:/argocd-ui`. It validates SAN, validity, key correspondence,
  and exact PEM closure without printing values.
- Infisical Operator materializes `argocd/argocd-ui-tls` with `creationPolicy:
  Orphan`; direct `kubectl` writes and a second Secret writer are forbidden.

## Renewal

Renewal is a guarded controller operation when less than 30 days remain. It
creates an isolated mode-0700 workspace, uses DNS-01 only for
`_acme-challenge.argo.cristex-soft.com`, verifies the resulting certificate, and
uploads the replacement values through the existing Infisical API lane. The
workspace is removed before success is reported. Existing certificate values are
never read into output or evidence. Renewal refuses any DNS response or plan that
contains a name other than the exact hostname and challenge name.

The existing Argo CD bootstrap TLS Secret (`argocd-server-tls`) is unrelated: it
is the internal Argo server certificate and must not be replaced by this browser
certificate. `argocd-ui-tls` is consumed only by Traefik.

## Gates and rollback

Source authoring does not issue certificates, mutate DNS, update Infisical, or
apply Kubernetes. Each operation requires separate provider, value, and cluster
approval. Before first apply, verify encrypted recovery for state and protected
credential custody. On failure, remove only the exact challenge record, revoke
the certificate if issued, delete temporary artifacts, and leave the existing
Kubernetes Secret and DNS record unchanged.

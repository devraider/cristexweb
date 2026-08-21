# Guarded OIDC CONNECT proxy

Status: **APPLIED / IDEMPOTENT / PRIVATE PROD VALIDATED**.

## Current live checkpoint — 2026-08-20

The guarded source is applied in `shared-services` and the exact client ingress
policy includes the CristexHub DEV and PROD backend, Celery, and oauth2-proxy
workloads. The proxy Service is healthy. Private PROD validation observed backend
HTTP `200`, oauth2-proxy root/start redirects (`302`), backend startup completion,
and a ready Celery worker connected to the TLS RabbitMQ broker. The proxy remains
CONNECT-only to `auth.cristex-soft.com:443`; no public Keycloak administration,
management, or direct-origin path is added. This evidence does not authorize the
Cloudflare PROD route.

The source-only status below is retained as historical evidence from the pre-apply
checkpoint. Its exact status was **source-only; runtime not run and blocked**. It
must not be read as current absence of the proxy or its PROD policy.

## Historical source-only closure

`ansible/files/components/oidc-connect-proxy/` contains exactly ten value-free
objects: one ConfigMap, one ServiceAccount, one ClusterIP Service, one Deployment,
and seven NetworkPolicies. The Deployment uses the pinned Ubuntu Squid image,
non-root UID 13, a read-only root filesystem, dropped capabilities, RuntimeDefault
seccomp, memory-backed writable paths, and no service-account token. Access logs
are disabled; Squid errors contain no credential values.

The Squid ACL is deliberately narrower than ordinary HTTPS forwarding:

- only the `CONNECT` method is accepted;
- only destination port 443 is accepted;
- only the exact `auth.cristex-soft.com` destination ACL is accepted;
- private, loopback, link-local, documentation, multicast, and reserved ranges
  are denied; and
- all other requests are denied.

A Kubernetes NetworkPolicy cannot match an FQDN. Therefore the proxy egress
policy allows public TCP/443 only after excluding private/reserved IPv4 ranges,
while the Squid ACL is the authoritative hostname and port boundary. DNS is
limited to the kube-system CoreDNS pods. Proxy ingress is limited to pods named
`cristexhub-backend` and `oauth2-proxy` in the exact `cristexhub-dev` Namespace.
Each consumer policy selects only its named workload and permits DNS plus TCP
3128 to the proxy; selecting egress makes all other egress unavailable unless a
separately reviewed policy adds it.

Consumers must use the in-cluster proxy endpoint
`http://oidc-connect-proxy.shared-services.svc.cluster.local:3128` for HTTPS OIDC
requests. They must not set `NO_PROXY` for `auth.cristex-soft.com`; internal
cluster names should remain in `NO_PROXY`. No proxy credential or TLS Secret is
needed: ingress is enforced by the exact NetworkPolicy and the proxy has no
other allowed destination.

## Guarded execution

The only executable entrypoint is:

```text
ansible/bin/bootstrap-oidc-connect-proxy check|apply
```

It accepts no task selection, requires `--limit crtxweb --diff`, a private
single-run attestation, the exact source hashes, active `shared-services` and
reviewed consumer Namespaces, healthy k3s/Tailscale, and present-only object
arguments. It has no delete path and refuses Secrets, PVCs, Ingresses, and
ServiceMonitors. The separately approved apply and idempotence evidence above
reconciles only this proxy closure; it does not authorize any public route.

The source and applied policy must continue to verify exact workload labels and
separate non-OIDC internal flows. Ongoing validation must prove positive CONNECT
to the issuer and negative CONNECT to another hostname, port 80, an IP literal,
private/reserved destinations, and non-CONNECT HTTP, without recording tokens,
cookies, Authorization headers, or proxy logs. Residual rotation of the exposed
PROD MongoDB/RabbitMQ URL credentials and GHCR pull credential remains required
before public cutover.

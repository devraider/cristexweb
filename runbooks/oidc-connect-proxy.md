# Guarded OIDC CONNECT proxy

Status: **source-only; runtime not run and blocked**.

This closure provides a dedicated Squid CONNECT proxy for the future CristexHub
DEV backend and `oauth2-proxy` workloads. It permits only CONNECT requests to
`auth.cristex-soft.com:443`, which is the selected Keycloak OIDC issuer host.
It does not expose Keycloak, publish DNS, create an Ingress, or perform a live
Kubernetes mutation.

## Source closure

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
`cristexhub-dev` Namespaces, healthy k3s/Tailscale, and present-only object
arguments. It has no delete path and refuses Secrets, PVCs, Ingresses, and
ServiceMonitors. Runtime execution requires a separate reviewed approval; this
change performs no check, apply, or API mutation.

Before any future apply, verify both target workloads have exactly the labels
used by the policies, establish their required non-OIDC internal flows through
separate policies, run check mode, and separately approve apply and idempotence.
Validation must prove positive CONNECT to the issuer and negative CONNECT to
another hostname, port 80, an IP literal, private/reserved destinations, and
non-CONNECT HTTP, without recording tokens, cookies, Authorization headers, or
proxy logs.

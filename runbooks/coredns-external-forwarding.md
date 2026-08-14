# CoreDNS external forwarding recovery

The k3s-owned CoreDNS ConfigMap originally forwarded external queries through
the host `/etc/resolv.conf`. On 2026-08-14 that produced repeated timeouts to
`192.168.1.1:53` and an unusable link-local IPv6 resolver, while cluster-local
DNS continued to work. Argo could therefore resolve Kubernetes Services but not
`ssh.github.com`.

`ansible/bin/configure-coredns-external-forwarding check|apply` performs one
JSON Patch guarded by an exact test of the complete existing Corefile. It
replaces only `forward . /etc/resolv.conf` with
`forward . 1.1.1.1 1.0.0.1`. It does not replace the k3s-owned ConfigMap,
NodeHosts, Kubernetes zone, cache, health, metrics, or other CoreDNS settings.
Any absent, repeated, or drifted directive fails closed.

The approved apply changed one field. CoreDNS was restarted once so its mounted
Corefile reloaded. External resolution of `ssh.github.com` then passed from the
Argo namespace. Final guarded idempotence passed with `changed=0`.

Rollback uses the same guarded exact-field mechanism with old/new directives
reviewed in reverse; blind ConfigMap replacement or Namespace/Pod deletion is
not a rollback mechanism. The residual dependency is direct reachability to
Cloudflare DNS over UDP/TCP 53.

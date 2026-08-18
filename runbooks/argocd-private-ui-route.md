# Private Argo CD UI route

The guarded route source serves `https://argo.cristex-soft.com` through bundled
Traefik. Traefik terminates public-CA TLS using the precreated
`argocd/argocd-ui-tls` Secret and forwards plain HTTP to the Argo CD Service on
port 80. Argo CD's `server.insecure: true` is therefore intentional and is
reconciled by the main Argo CD closure; the Argo Service remains ClusterIP and
Traefik is the only allowed pod ingress.

The route source is present-only, hash-bound, and refuses Secrets. The TLS
Secret must already exist with exact type `kubernetes.io/tls` and keys
`tls.crt`/`tls.key`; certificate values are never committed. Run the dedicated
wrapper only with separate approval:

```text
ansible/bin/bootstrap-argocd-route check
ansible/bin/bootstrap-argocd-route apply
```

No Cloudflare Tunnel or public Argo route is created by this source. DNS and
certificate renewal remain separate ownership boundaries. Validate the UI from
a Tailscale-connected client and verify that non-tailnet access is unreachable.

# Reactive Resume DEV private route

## Status and ownership

This is a **source-only guarded closure** for the private Reactive Resume DEV
route. It is not evidence of a live route, DNS record, certificate issuance,
Kubernetes apply, Argo handoff, or public exposure. The route remains disabled
until a separate operator-approved check/apply sequence succeeds.

- Ansible owns this bounded bootstrap closure until object-by-object handoff.
- Traefik in `kube-system` is the only ingress controller and the only allowed
  source of application ingress.
- The Reactive Resume workload and route belong in `cristexhub-dev`.
- OpenTofu owns Cloudflare resources; this closure has no DNS/provider path.
- `reactive-resume-dev-tls` is precreated and value-owned outside this source.
  This closure consumes its metadata only and refuses to create or modify it.
- No Keycloak, Infisical, Secret, PROD, NodePort, LoadBalancer, or second
  ingress-controller object is included.

## Exact route contract

The two value-free manifests are:

```text
ansible/files/components/reactive-resume-dev-route/network/allow-traefik.yaml
ansible/files/components/reactive-resume-dev-route/route/ingress-reactive-resume-dev.yaml
```

The Ingress is exactly:

- host `resume-dev.cristex-soft.com`;
- Traefik class and `websecure` entrypoint with TLS enabled;
- precreated Secret `reactive-resume-dev-tls` (never written here);
- Service `reactive-resume-dev`, port `3000`, path `/`.

The NetworkPolicy selects only Reactive Resume DEV pods in `cristexhub-dev` and
allows only TCP `3000` from a `kube-system` namespace peer whose pod label is
`app.kubernetes.io/name=traefik`. No other ingress peer or port is admitted by
this route policy. Existing workload default-deny/egress policies remain the
workload closure and are not broadened here.

The component ledger is `MANIFESTS.sha256`; source leaves must be regular
mode-`0644` files and hash-match the role defaults before any action is reached.
The role also checks, without logging data, that the precreated TLS Secret has
exact type `kubernetes.io/tls` and exactly `tls.crt`/`tls.key` keys.

## Guarded entrypoint

Only the fixed non-passthrough wrapper is permitted:

```text
ansible/bin/bootstrap-reactive-resume-dev-route check
ansible/bin/bootstrap-reactive-resume-dev-route apply
```

The wrapper pins the repository and controller, limits execution to `crtxweb`,
creates one ephemeral attestation, uses an allowlisted clean environment, and
passes no task-selection or extra arguments. The role requires diff mode,
`state: present`, one host, the protected k3s kubeconfig, the exact two-object
inventory, and the existing `cristexhub-dev` Namespace. Its focused action
plugin refuses Secrets, PVCs, Services, Deployments, IngressRoutes, deletion,
foreign objects, hash drift, and any object outside the exact identity set.

Check mode must be run first. Apply remains a separate operator approval. The
closure has no deletion or rollback path; rollback is a reviewed Git revert and
removal of only these exact route objects through a separately approved
operation. A label is not an Argo handoff: registration, adoption, successful
sync, and managed-fields evidence are still required before ownership changes.

## Validation and residual risks

Offline validation includes YAML/ledger checks, wrapper shell syntax, Ansible
syntax, source-hash checks, namespace/host/service/TLS assertions, exact
NetworkPolicy peer/port assertions, and rejection of Secret values and foreign
route objects. No provider, DNS, Infisical, Keycloak, Kubernetes, or live host
command is part of source validation.

Before activation, separately verify the precreated certificate SAN and validity,
Tailscale/private reachability, negative non-Tailscale reachability, OIDC
callback/logout using the selected hostname, application health, and no public
Cloudflare route. Public `resume.cristex-soft.com` and PROD remain out of scope.

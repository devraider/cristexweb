# Reactive Resume DEV Argo desired state

This source-only closure is the canonical Argo desired-state path for the
private Reactive Resume DEV workload:

```text
ansible/files/components/reactive-resume-dev-argocd/
```

It contains exactly eight value-free Kubernetes objects in
`cristexhub-dev`: one immutable-digest Deployment, one migration Job, one
ClusterIP Service, one tokenless ServiceAccount, three workload NetworkPolicies,
and the private Traefik Ingress. The Ingress references the precreated
`reactive-resume-dev-tls` Secret; this path never creates or updates Secrets,
PVCs, Namespaces, RBAC, object storage, database, or Infisical resources.

## Fixed object contract

- Runtime image:
  `ghcr.io/devraider/cristex-reactive-resume@sha256:720ff5a60a7f6b91a75535e230dbb664207fdf1bc5cb8732d584bae7ebdac13c`
- Migration image:
  `ghcr.io/devraider/cristex-reactive-resume@sha256:a4f0157e023c10c1c6ff163d34bf25c3343647247eddb1d4f9bfa9b46e1a3093`
- Migration object: `job/reactive-resume-dev-migrate` (not
  `job/reactive-resume-dev-migration`).
- Runtime and migration consume only precreated Infisical-owned Secrets and
  ConfigMaps through `secretKeyRef`/`configMap`; no value is present here.
- The Service remains `ClusterIP` on port `3000`; no NodePort, LoadBalancer, or
  alternate ingress is permitted.
- Route traffic is only `resume-dev.cristex-soft.com` through Traefik
  `websecure` and the precreated `reactive-resume-dev-tls` Secret.
- Argo registration pins a reviewed immutable repository revision and uses
  `prune=false`, `selfHeal=true`, `allowEmpty=false`, and
  `CreateNamespace=false`.

The manifest hash ledger is `MANIFESTS.sha256`. Changes to image digests,
object names, selectors, Secret/ConfigMap references, or route boundaries
require a new reviewed source closure and updated contract tests. Do not
reintroduce the stale migration name: the guarded deployment orchestration and
all acceptance checks must query `job/reactive-resume-dev-migrate`.

## Handoff sequence

Ansible remains the bootstrap writer until the guarded Argo registration has
verified all eight existing live objects, no Argo managed fields/tracking
annotation, the exact repository credential, and a no-dual-reconciliation
preflight. Only then may the separate registration gate reconcile the Argo
Application. No Argo sync, Kubernetes apply, workload restart, migration rerun,
Secret mutation, or PVC operation is authorized by this source alone.

Before accepting the handoff, independently verify the runtime Secret,
migration Secret, PostgreSQL CA ConfigMap, object-storage CA Secret, image-pull
Secret, TLS Secret, Service endpoints, successful migration Job, Deployment
readiness, private route, and cross-namespace NetworkPolicies. Evidence must
remain value-free.

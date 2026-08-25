# Reactive Resume DEV Argo CD registration and handoff

This is a source-only, guarded registration closure for the private Reactive
Resume DEV workload in `cristexhub-dev`. It does not perform a Kubernetes,
Argo, provider, DNS, Infisical, or PROD operation by itself.

## Exact source and scope

The registration Application uses the infrastructure repository
`ssh://git@ssh.github.com:443/devraider/cristexweb.git`, immutable revision
`9a9b96c193e7021030dc36e631a08ca0146d5799`, and the future desired-state
path `ansible/files/components/reactive-resume-dev-argocd`. The checked-in
value-free handoff inventory under
`ansible/files/policies/reactive-resume-dev-argocd-handoff` identifies exactly
eight namespaced DEV workload objects: the Deployment, migration Job, Service,
ServiceAccount, two workload NetworkPolicies, the Traefik-only route
NetworkPolicy, and the private Ingress. Secret, Namespace, PVC, RBAC, shared
service, Keycloak, Infisical, and PROD objects remain outside this handoff.
The desired-state directory is intentionally not present in this source-only
registration revision; a later source-reconciliation task must publish it
before any sync/adoption approval.

An Infisical-owned, value-bearing-free repository Secret named
`argocd-repository-cristexweb` must already exist in `argocd`; this closure only
checks its metadata and never reads or prints its private key. The destination
is the existing `cristexhub-dev` Namespace through the namespace-limited
`reactive-resume-dev-local` cluster registration.

## Safety and ownership boundary

The five registration objects are an AppProject, Application, Role,
RoleBinding, and namespace-limited cluster Secret. The AppProject permits only
Deployment, Job, Service, ServiceAccount, Ingress, and NetworkPolicy in
`cristexhub-dev`; it permits no cluster-scoped resources or Secrets. The Role
has only get/list/watch/create/patch and no delete. The cluster Secret sets
`clusterResources=false` and `namespaces=cristexhub-dev`.

The Application is automated only with safe controls:
`prune=false`, `selfHeal=true`, `allowEmpty=false`, `Prune=false`, and
`CreateNamespace=false`. An always-active deny sync window keeps the
registration from synchronizing while Ansible still owns the live objects.
The handoff preflight requires every inventoried live object to exist with
`app.kubernetes.io/managed-by=ansible`, a reviewed bootstrap-writer label,
and `cristex.io/desired-owner=argocd`, and rejects Argo tracking annotations,
Argo managed fields, owner references, and finalizers. Registration reconciles
only its five registration objects; it never changes the workload objects.
This is the no-dual-reconciliation boundary: no dual reconciliation is permitted. A later, separately approved adoption must
first stop the Ansible workload owner, remove the deny window through a reviewed
source revision, sync once, and collect managed-field evidence.

There is no PROD path in this closure. `cristexhub-prod`,
`reactive-resume-prod`, public routing, and production promotion are rejected
by source scope and remain separate approvals.

## Guarded entrypoint

```text
ansible/bin/bootstrap-reactive-resume-dev-argocd-registration check
ansible/bin/bootstrap-reactive-resume-dev-argocd-registration apply
```

The wrapper accepts exactly `check|apply`, uses the pinned controller and
clean environment, binds a single-run 0600 attestation, forces `--diff` and
`--limit crtxweb`, and refuses task-selection or passthrough controls. Check
must pass before any separately approved apply. This source-only revision was
not run against the live cluster.

## Remaining gates

The repository credential `argocd-repository-cristexweb`, exact live RR object
set, and absence of Argo managed fields are required before a guarded check
can pass. A successful check, separately approved apply, idempotence retry,
Argo sync/adoption evidence, and private hostname/backup/soak acceptance are
still required. No source commit authorizes Kubernetes mutation or PROD.

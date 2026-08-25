# Reactive Resume DEV Argo CD registration and handoff

This is a source-only, guarded registration closure for the private Reactive
Resume DEV workload in `cristexhub-dev`. It does not perform a Kubernetes,
Argo, provider, DNS, Infisical, or PROD operation by itself.

## Exact source and scope

The registration Application uses the infrastructure repository
`ssh://git@ssh.github.com:443/devraider/cristexweb.git`, immutable revision
`dd7d4cedd902e68266d9713d1dbb8e90f0b529b1`, and the desired-state path
`ansible/files/components/reactive-resume-dev-argocd`. The checked-in
value-free handoff inventory under
`ansible/files/policies/reactive-resume-dev-argocd-handoff` identifies exactly
eight namespaced DEV workload objects: the Deployment, migration Job, Service,
ServiceAccount, two workload NetworkPolicies, the Traefik-only route
NetworkPolicy, and the private Ingress. Secret, Namespace, PVC, RBAC, shared
service, Keycloak, Infisical, and PROD objects remain outside this handoff.
Only seven of those objects are automated Argo desired state: the migration
Job remains inventory-only and is a separately guarded one-shot prerequisite.
The migration Job is excluded from the automated Argo desired-state.

An Infisical-owned, value-bearing-free repository Secret named
`argocd-repository-cristexweb` must already exist in `argocd`; this closure uses
`hidden_fields` to suppress `data`, `stringData`, and `binaryData` at the
Ansible result boundary, and never reads, decodes, or prints its private key.
The exact Infisical-owned runtime and migration Secrets, PostgreSQL and object
storage CA outputs, GHCR pull Secret, and browser TLS Secret must also exist
with their reviewed labels, version annotation, type, owner-reference, and
resource-version contracts. The workload Deployment must be Available and the
migration Job complete before registration proceeds. The destination is the
existing `cristexhub-dev` Namespace through the namespace-limited
`reactive-resume-dev-local` cluster registration.

## Safety and ownership boundary

The five registration objects are an AppProject, Application, Role,
RoleBinding, and namespace-limited cluster Secret. The AppProject permits only
Deployment, Service, ServiceAccount, Ingress, and NetworkPolicy in
`cristexhub-dev`; it permits no Jobs, cluster-scoped resources, or Secrets. The
Role has only get/list/watch/create/patch for those runtime object classes and
no delete. The cluster Secret sets `clusterResources=false` and
`namespaces=cristexhub-dev`.

The Application is automated only with safe controls:
`prune=false`, `selfHeal=true`, `allowEmpty=false`, `Prune=false`, and
`CreateNamespace=false`. An always-active deny sync window keeps the
registration from synchronizing while Ansible still owns the live objects.
The handoff preflight requires every inventoried live object to exist with
`app.kubernetes.io/managed-by=ansible`, a reviewed bootstrap-writer label,
and `cristex.io/desired-owner=argocd`, and rejects Argo tracking annotations,
Argo managed fields, owner references, and finalizers. Registration reconciles
only its five registration objects; it never changes the workload objects.
This is the no-dual-reconciliation boundary: no dual reconciliation is permitted. The
route wrapper also refuses to run once the Argo Application handoff marker exists,
so the duplicate Ansible route source cannot reconcile after handoff. A later,
separately approved adoption must first stop the Ansible workload owner, remove
the deny window through a reviewed source revision, sync once, and collect
managed-field evidence.

There is no PROD path in this closure. `cristexhub-prod`,
`reactive-resume-prod`, public routing, and production promotion are rejected
by source scope and remain separate approvals.

The fixed-name migration Job is deliberately not an Argo resource. Before
runtime handoff, a separately approved one-shot migration gate must verify the
precreated migration Secret and PostgreSQL CA, apply or confirm only
`job/reactive-resume-dev-migrate`, wait for successful completion, and record a
sanitized receipt. It must never be placed back into the automated source,
rerun through `selfHeal`, or updated in place; any new migration requires a
new reviewed Job identity and separate approval.

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

The repository credential `argocd-repository-cristexweb`, exact value-suppressed
Secret/CA/pull/TLS dependency metadata, ready live RR workload set, and absence
of Argo managed fields are required before a guarded check can pass. A successful check, separately approved apply, idempotence retry,
Argo sync/adoption evidence, and private hostname/backup/soak acceptance are
still required. No source commit authorizes Kubernetes mutation or PROD.

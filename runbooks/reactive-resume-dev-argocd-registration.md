# Reactive Resume DEV Argo CD registration and handoff

## Status

**LIVE / SYNCED / HEALTHY.** The five-object registration closure, exact
migration prerequisite, dependency key closure, and pinned seven-object desired
state passed the guarded preflight. Current HEAD contains an eighth checked-in
YAML, `networkpolicy-allow-backend.yaml`, which is source-only and is not claimed
live, Argo-managed, or applied. The alignment
apply converged and its retry passed at `changed=0`; registration then applied
and converged at `changed=0`. After the approved deny-window removal and exact
in-cluster destination correction, Argo reconciled revision
`faf2e5f108d02e096379b4619ee78b114f6219a7` to `Synced/Healthy` with a successful
operation. All seven objects have Argo tracking annotations; this k3s API omits
`metadata.managedFields`, so manager-field evidence is unavailable rather than
claimed. Argo reports 15 intentionally out-of-scope namespace resources as
orphans; this is a warning only and `prune=false` must remain in force. The
superseded alignment wrapper now fails closed on the Argo tracking markers,
proving that its Ansible reconciliation lane cannot be reopened.

This is a source-only, guarded registration closure for the private Reactive
Resume DEV workload in `cristexhub-dev`. It does not perform a Kubernetes,
Argo, provider, DNS, Infisical, or PROD operation by itself.

## Exact source and scope

The registration Application uses the infrastructure repository
`ssh://git@ssh.github.com:443/devraider/cristexweb.git`, immutable revision
`faf2e5f108d02e096379b4619ee78b114f6219a7`, and the desired-state path
`ansible/files/components/reactive-resume-dev-argocd`. The checked-in
value-free handoff inventory under
`ansible/files/policies/reactive-resume-dev-argocd-handoff` identifies exactly
eight namespaced DEV workload objects: the Deployment, migration Job, Service,
ServiceAccount, two workload NetworkPolicies, the Traefik-only route
NetworkPolicy, and the private Ingress. Secret, Namespace, PVC, RBAC, shared
service, Keycloak, Infisical, and PROD objects remain outside this handoff.
Only seven of those objects are automated Argo desired state at pinned revision
`faf2e5f108d02e096379b4619ee78b114f6219a7`: the migration Job remains
inventory-only and is a separately guarded one-shot prerequisite. The current-HEAD
`networkpolicy-allow-backend.yaml` is outside that pinned revision and carries no
live or Argo-managed claim.
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
exact in-cluster server destination `https://kubernetes.default.svc`; the dedicated cluster credential remains separately registered.

## Safety and ownership boundary

The five registration objects are an AppProject, Application, Role,
RoleBinding, and namespace-limited cluster Secret. The AppProject permits only
Deployment, Service, ServiceAccount, Ingress, and NetworkPolicy in
`cristexhub-dev`; it permits no Jobs, cluster-scoped resources, or Secrets. The
Role has only get/list/watch/create/patch for those runtime object classes and
no delete. The cluster Secret sets `clusterResources=false` and the exact
comma-delimited Argo allowlist
`namespaces=cristexhub-dev,cristexhub-prod`. All three same-server registration
Secrets use this identical cache scope; the Reactive Resume AppProject and
namespaced Role still restrict writes to `cristexhub-dev`. The owner wrapper
accepts the previous exact `namespaces=cristexhub-dev` Secret only as the
bounded pre-state: `check` predicts its replacement, `apply` reconciles the
shared allowlist, and apply post-validation re-reads the Secret and requires the
exact five-object registration closure.

The Application is automated only with safe controls:
`prune=false`, `selfHeal=true`, `allowEmpty=false`, `Prune=false`, and
`CreateNamespace=false`. An always-active deny sync window kept the initial
registration quiescent while Ansible still owned the live objects; the separately
approved adoption transition removed that window only after exact alignment.
The handoff preflight requires every inventoried live object to exist with
`app.kubernetes.io/managed-by=ansible`, a reviewed bootstrap-writer label,
and `cristex.io/desired-owner=argocd`, and rejects Argo tracking annotations,
Argo managed fields, owner references, and finalizers. Registration reconciles
only its five registration objects; it never changes the workload objects.
This is the no-dual-reconciliation boundary: no dual reconciliation is permitted. The
route wrapper also refuses to run once the Argo Application handoff marker exists,
so the duplicate Ansible route source cannot reconcile after handoff. The adoption stopped the Ansible workload lane, removed the deny window through
reviewed source, synced once, and collected the available tracking evidence.
Manager-field evidence remains unavailable because this API omits the field.

There is no PROD path in this closure. `cristexhub-prod`,
`reactive-resume-prod`, public routing, and production promotion are rejected
by source scope and remain separate approvals.

The fixed-name migration Job is deliberately not an Argo resource. Its complete
value-free policy is hash-bound in
`ansible/files/policies/reactive-resume-dev-argocd-handoff/migration-job.yaml`
(`sha256:b262ddb6834eb9d14d0eb279bb1a1c8686df83fedea56dc51d01fddc2281a3ac`).
Before runtime handoff, the guarded registration preflight compares the live
completed Job's immutable metadata labels/annotations, runtime image digest,
command/args, environment values and exact migration Secret key references,
pull Secret, PostgreSQL CA ConfigMap, security context, resources, volumes, and
workload labels to that source. It also requires one successful completion with
no active or failed attempts. The gate only reads and validates this Job; it
never reconciles it. A separately approved one-shot migration gate must verify
the precreated migration Secret and PostgreSQL CA, apply or confirm only
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
must pass before any separately approved apply. The latest guarded `check` reached the live dependency preflight and live
cluster metadata preflight; registration and handoff now pass with the
repository credential present. This is apply and handoff evidence.

## Remaining gates

The repository credential and exact value-suppressed dependency metadata/key
closure passed: runtime has the reviewed 15 keys, migration has its exact two,
each CA target has only `ca.crt`, the pull Secret only `.dockerconfigjson`, and
TLS only `tls.crt`/`tls.key`. Names were checked under `no_log`; values were never
emitted. Registration, idempotence, sync, adoption, and private hostname health
now pass. Hardened schema-2 backup/restore, TLS renewal installation/enablement,
the 15-minute soak, and protected GitHub-state recovery remain separate pending
gates. Nothing here authorizes PROD or public routing.

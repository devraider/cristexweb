# CristexHub PROD Argo registration and private activation

Status: **SOURCE DIRECT-SERVER READY / ONE-TIME ALIAS TRANSITION PENDING / PUBLIC ROUTE PENDING**.

The canonical PROD registration source now uses the in-cluster Kubernetes API
server directly. The separate cache-scope lane must first complete the exact
three-Secret namespace-scope transition. This registration lane then accepts
only the already-existing PROD five-object closure and performs the bounded
alias-to-direct-server repair. It does not inspect or reconcile DEV or Reactive Resume registration objects, does not create a Namespace, and never changes Secret values.

## Canonical five-object closure

The source contains exactly these Ansible-owned objects:

1. `argoproj.io/v1alpha1|AppProject|argocd|cristexhub-prod`;
2. `argoproj.io/v1alpha1|Application|argocd|cristexhub-prod`;
3. the namespaced PROD controller `Role`;
4. its namespaced `RoleBinding`;
5. `v1|Secret|argocd|argocd-cluster-cristexhub-prod`.

The cluster Secret is value-free registration metadata. Its server is
`https://kubernetes.default.svc`, its exact namespace allowlist is
`cristexhub-dev,cristexhub-prod`, `clusterResources` is `false`, and `config`
is `{}`. The cache-scope transition is a separate one-time lane that updates
all three same-server cluster Secrets. This PROD lane requires the shared PROD
Secret scope and refuses the old single-namespace value, preventing a partial
cache repair from being silently overwritten.

The final Application is pinned to repository
`ssh://git@ssh.github.com:443/devraider/cristexhub.git`, path
`infra/kubernetes/cristexhub-prod`, and revision
`751885a42798d282e168131db147f13694a0a621`. Its destination is exactly
`server: https://kubernetes.default.svc` and `namespace: cristexhub-prod`.
Its automated policy is `selfHeal=true`, `prune=false`, `allowEmpty=false`,
with `CreateNamespace=false`, `Prune=false`, `Replace=false`, and
`FailOnSharedResource=true`. The final AppProject permits only that server and
namespace, has no cluster-resource whitelist, and permits only the reviewed
ConfigMap, Service, Deployment, NetworkPolicy, and Ingress kinds.

## One-time alias-to-direct-server transition

`ansible/bin/bootstrap-cristexhub-prod-registration check|apply` is the only
registration entrypoint. After the cache-scope lane, the exact expected
pre-state is the existing alias form:

- AppProject destinations: only `name: cristexhub-prod-local` with
  `namespace: cristexhub-prod`;
- Application destination: `name: cristexhub-prod-local`, empty `server`, and
  `namespace: cristexhub-prod`.

The guarded transition is exactly three ordered JSON Patch operations:

1. replace only AppProject `/spec/destinations` with the exact temporary list
   containing the direct server and the alias, both for `cristexhub-prod`;
2. replace only Application `/spec/destination` with the direct server while
   preserving its exact source and non-pruning sync policy;
3. replace only AppProject `/spec/destinations` with the direct-server-only
   list.

Each patch is built from a fresh per-step GET and tests the immutable live UID,
resourceVersion, exact ownership labels, and complete preceding `spec` first. A
failed test is a conflict and stops without retrying or widening the operation. The accepted mixed recovery states are only:

- alias AppProject + alias Application: all three steps;
- temporary AppProject + alias Application: steps two and three;
- temporary AppProject + direct Application: step three;
- direct AppProject + direct Application: no steps (idempotent).

A final AppProject with an alias Application, an alias AppProject with a direct
Application, a changed UID, metadata drift, a foreign spec, or any missing or
extra object fails closed. The patch contains no delete, prune, sync, status,
workload, DEV, or Reactive Resume operation; `resourceVersion` appears only as an
optimistic-concurrency `test` precondition.

## Guard and post-validation

The wrapper rejects passthrough arguments, task-selection controls, extra-variable
and inventory overrides, symlinked paths, non-canonical repositories, and
non-canonical source hashes. The action guard independently binds the canonical
wrapper process, operator, controller, Python, kubeconfig, inventory, task/action
identity, and source closure. It runs the
pinned project controller against only `crtxweb`, with `--diff`, a clean
allowlisted environment, and a single-use `0600` attestation that is removed on
exit. The role binds all five live UIDs, resourceVersions, generations, exact
metadata, and ownership before any write. It reconciles only the three
unchanged PROD support objects; the two transition objects are dispatched
through `kubernetes.core.k8s_json_patch`.

Check mode performs only read-only GETs and predicts the exact remaining
transition steps. Apply is a separately approved mutation. After the transition
it waits for a fresh PROD Application to become `Synced/Healthy`, then checks
same-UID post-state, the pinned revision, direct-server
`status.comparedTo.destination.server` and namespace, exact final AppProject
and Application specs, no-prune policy, and unchanged support objects.

No Cloudflare route or public DNS record is part of this lane. Public cutover
remains blocked by the independent state-import, credential-rotation,
NetworkPolicy, recovery, provider-authorization, and private acceptance gates.

## Offline validation

```bash
/home/paul/projects/cristexweb/.venv/bin/python -m unittest -v tests.test_cristexhub_prod_registration_contract
/home/paul/projects/cristexweb/.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-cristexhub-prod-registration
sh -n tests/reject_cristexhub_prod_registration_resource_version.sh
tests/reject_cristexhub_prod_registration_resource_version.sh
cd ansible && ../.venv/bin/ansible-playbook playbooks/bootstrap_cristexhub_prod_registration.yml --syntax-check
```

These checks are source-only. They do not apply the transition, change Argo
state, create Secrets, or alter the public route. A separately approved apply
must be run only after the cache-scope check/apply and must record a fresh
`Synced/Healthy` post-state.

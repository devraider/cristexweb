# Guarded Argo target-cache repair

## Scope and status

This is a one-time, source-only guarded repair for the already-running private Argo
application-controller. It is not the 32-object Argo bootstrap and does not own
any Secret, Deployment, server, repo-server, Application, AppProject, or
RoleBinding. No live operation is claimed by this source change.

The exact mutation closure contains three existing objects only, applied in this
order: `cristexhub-prod/argocd-application-controller-cristexhub-prod` Role,
`argocd/argocd-cm` ConfigMap, and `argocd/argocd-application-controller`
StatefulSet. The operation may add the exact `resource.inclusions` value to
`argocd-cm`, add only read verbs for `serviceaccounts` to the PROD controller
Role, and replace only the controller pod-template annotations. It has no delete,
prune, or broad apply path.

## Resource inclusion contract

The canonical `argocd-cm` allowlist uses only the exact registered API-server URL
`https://kubernetes.default.svc`; a wildcard cluster is forbidden. The complete
managed target union is exactly:

- core: `ConfigMap`, `Service`, `ServiceAccount`;
- `apps`: `Deployment`;
- `networking.k8s.io`: `Ingress`, `NetworkPolicy`.

This is a cache/discovery filter, not RBAC. The PROD AppProject continues to omit
ServiceAccount from its namespaced whitelist and the PROD Role grants only
`get`, `list`, and `watch` for ServiceAccounts. It grants no ServiceAccount
create, patch, update, or delete verb. The filter does not include Secret,
StatefulSet, Job, CRD, Role, RoleBinding, Application, or AppProject. Foundation
Argo objects remain Ansible-owned and outside this target-cache lane.

## Execution gate

The only entrypoint is
`ansible/bin/bootstrap-argocd-target-cache-repair check|apply`. It rejects
passthrough arguments and task selection. The wrapper changes to the canonical
`ansible/` directory and runs the dedicated playbook with a clean environment,
fixed repository/inventory/config/kubeconfig, exact controller and Python
(`/usr/bin/python3.13`, regular root-owned `0755`) digests, a single-run
PID-bound attestation, and the canonical non-symlink action plugin. Direct
`ansible-playbook` and action-plugin invocation are rejected. The trusted
controller-UID boundary is explicit: a malicious process already running as the
trusted UID can forge same-UID files and inputs and is outside this guarantee.

Check reads exactly the three live mutation objects, the PROD Application and the
server/repo-server peer metadata. It predicts one CAS JSON Patch per legacy
object. Apply requires a separate approval and tests each UID and current
resourceVersion immediately before its patch. A race, foreign UID, resource
source/hash drift, incomplete preflight binding, unsafe kubeconfig, or partial
state fails closed. StatefulSet final state is accepted only when its full
normalized `spec` and target annotations match; annotations alone never classify
a final state. Post-validation checks every object identity/UID/RV/labels and
full ConfigMap data, Role rules, or StatefulSet spec.

The StatefulSet patch changes only
`spec.template.metadata.annotations`, including the ConfigMap and PROD Role
checksums plus `cristex.io/target-cache-repair: v1`. It rolls only
`argocd-application-controller`; neither `argocd-server` nor
`argocd-repo-server` is patched or restarted. Rollout validation requires
`observedGeneration == metadata.generation`, `currentRevision == updateRevision`,
Available/Ready/updated counts of one, and one Ready Pod owned by the exact
StatefulSet UID with the matching controller-revision hash. The final Application
check requires a fresh resourceVersion, unchanged UID, exact direct-server
(destination name empty) and pinned revision, and `Synced/Healthy` status. No
Secret values are requested, decoded, printed, or persisted.

## Safe partial states and recovery

| State | Safe interpretation | Recovery |
|---|---|---|
| all three legacy | no mutation | rerun `check`, then separately approved `apply` |
| one or two target, remaining legacy | bounded partial apply | rerun `check`; apply only the remaining exact CAS patches |
| all three target, controller not fresh | data repair completed, rollout unaccepted | do not revert blindly; rerun `check`, inspect exact controller state, then use a separately reviewed rollout repair |
| CAS conflict, UID/RV/source drift, or postcondition failure | fail-closed stop | preserve the observed state, rerun read-only `check`, and obtain fresh approval if any mutation remains |
| controller rollout or Application health failure | no automatic rollback | do not delete or destroy; retain deny-safe state, inspect only, and use a reviewed forward repair |

There is no unsafe automatic rollback, delete, prune, or broad apply path. A
source revert is itself reviewed and must be followed by a fresh exact check;
rollback never assumes that reverting an inclusion restores cache state atomically.
The ConfigMap, Role, and controller StatefulSet are owned by the existing Ansible
bootstrap closure; this lane is a bounded one-time exception and must not be
reused as a general reconciler.

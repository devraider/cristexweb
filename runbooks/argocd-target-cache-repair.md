# Guarded Argo target-cache repair

## Scope and status

This is a one-time, source-only guarded repair for the already-running private Argo
application-controller. It is not the 32-object Argo bootstrap and it does not own
any Secret, Deployment, server, repo-server, Application, AppProject, or
RoleBinding. No live operation is claimed by this source change.

The exact closure contains three existing objects only: `argocd/argocd-cm`,
`cristexhub-prod/argocd-application-controller-cristexhub-prod`, and
`argocd/argocd-application-controller`. The operation may add the exact
`resource.inclusions` value to `argocd-cm`, add only read verbs for
`serviceaccounts` to the PROD controller Role, and replace only the controller
pod-template annotations. It has no delete, prune, replace, or broad apply path.

## Resource inclusion contract

The canonical `argocd-cm` allowlist uses only the exact registered API-server URL
`https://kubernetes.default.svc`; a wildcard cluster is forbidden. The complete
managed target union is exactly:

- core: `ConfigMap`, `Service`, `ServiceAccount`;
- `apps`: `Deployment`;
- `networking.k8s.io`: `Ingress`, `NetworkPolicy`.

This is a cache/discovery filter, not RBAC. The PROD AppProject continues to omit
ServiceAccount from its namespaced whitelist and the PROD Role grants only
`get`, `list`, and `watch` for ServiceAccounts. It grants no ServiceAccount create,
patch, update, or delete verb. The filter does not include Secret, StatefulSet,
Job, CRD, Role, RoleBinding, Application, or AppProject.

## Execution gate

The only entrypoint is
`ansible/bin/bootstrap-argocd-target-cache-repair check|apply`. It rejects
passthrough arguments and task selection. The wrapper runs the dedicated playbook
with a clean environment, fixed repository/inventory/config/kubeconfig, exact
controller and Python digests, a single-run PID-bound attestation, and the
repository's canonical action plugin. Direct `ansible-playbook` and action-plugin
invocation are rejected.

Check reads exactly the three live objects and predicts one CAS JSON Patch per
legacy object. Apply requires a separate approval and tests each UID and current
resourceVersion immediately before its patch. A race, foreign UID, resource drift,
source/hash drift, or partial state fails closed. Post-validation checks all three
UIDs, resourceVersions, labels, desired data/rules/annotations, and the exact
three-object count.

The StatefulSet patch changes only
`spec.template.metadata.annotations`, including the ConfigMap and PROD Role
checksums plus `cristex.io/target-cache-repair: v1`. This rolls only
`argocd-application-controller`; neither `argocd-server` nor `argocd-repo-server`
is patched or restarted. The apply wait checks the controller StatefulSet
Available/Ready/updated counts and its Pod Ready condition, then requires
`cristexhub-prod` to be `Synced/Healthy` with the direct in-cluster destination.
No Secret values are requested, decoded, printed, or persisted.

## Rollback and residual risk

Rollback is a reviewed source revert followed by a new exact check; no blind delete
or destroy is allowed. Removing an inclusion can temporarily hide resources from
Argo cache until the controller refreshes, so the post-wait and application health
checks are mandatory. The global URL filter applies to every namespace on this
single registered server, while per-Application authorization remains the
AppProject and Role boundary. The operation remains pending its separately
approved check/apply/idempotence evidence.

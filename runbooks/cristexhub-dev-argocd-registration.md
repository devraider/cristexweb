# CristexHub DEV Argo registration

The guarded registration closure creates only a value-free `AppProject`,
`Application`, bounded controller RBAC, and a read-only private-repository
credential target owned by Infisical. The application source is pinned to
`ssh://git@ssh.github.com:443/devraider/cristexhub.git`, commit
`a74b8ec920171587a1423b3946951b0f258a55d7`, path
`infra/kubernetes/cristexhub-dev`.

The AppProject permits only ConfigMaps, Services, Deployments, and
NetworkPolicies in the existing `cristexhub-dev` namespace. It permits no
cluster-scoped application resource, Secret, Ingress, Namespace, PVC, Role, or
RoleBinding. Namespace writes are bounded by a Role without delete. Because
Argo's cluster cache lists managed kinds cluster-wide, a distinct ClusterRole
provides only `get`, `list`, and `watch` for those four resource kinds; it has no
Secret or mutation permission.

The repository deploy key is read-only, usable only through GitHub SSH on port
443, and its private value exists only at Infisical `prod:/argocd`. Infisical
materializes `argocd/argocd-repository-cristexhub`; no credential value is in
Git or evidence. The controller copy used for initial verification was securely
removed after materialization.

`ansible/bin/bootstrap-cristexhub-dev-registration check|apply` is the only
entrypoint. Registration is manual-sync, `Prune=false`,
`CreateNamespace=false`, has no resource finalizer, and does not deploy the
application. Runtime comparison passed with 18 rendered objects after bounded
RBAC and external DNS recovery.

Automatic or first manual synchronization remains blocked until all three
application image references have verified nonzero promotion digests, the exact
seven-key Infisical-owned `cristexhub-dev-runtime` Secret is reconciled, and the
approved OIDC egress path is implemented and validated. Enabling automated sync
before those gates would intentionally deploy a broken revision.

# CristexHub DEV Argo registration

The guarded registration closure creates only a value-free `AppProject`,
`Application`, bounded controller RBAC, and a read-only private-repository
credential target owned by Infisical. The application source is pinned to
`ssh://git@ssh.github.com:443/devraider/cristexhub.git`, commit
`57fffab4585fed12161144de7114c8ad05f3ba94`, path
`infra/kubernetes/cristexhub-dev`.

The AppProject permits only ConfigMaps, Services, Deployments, and
NetworkPolicies in the existing `cristexhub-dev` namespace. It permits no
cluster-scoped application resource, Secret, Ingress, Namespace, PVC, Role, or
RoleBinding. Namespace writes are bounded by a Role without delete. A non-sensitive Argo
cluster-registration Secret selects only `cristexhub-dev`, sets
`clusterResources=false`, and uses the controller's in-cluster identity. This
keeps cache reads namespace-scoped; no ClusterRole or ClusterRoleBinding is
created.

The repository deploy key is read-only, usable only through GitHub SSH on port
443, and its private value exists only at Infisical `prod:/argocd`. Infisical
materializes `argocd/argocd-repository-cristexhub`; no credential value is in
Git or evidence. The controller copy used for initial verification was securely
removed after materialization.

`ansible/bin/bootstrap-cristexhub-dev-registration check|apply` is the only
entrypoint. Registration is manual-sync, `Prune=false`,
`CreateNamespace=false`, has no resource finalizer, and does not deploy the
application. An always-active deny sync window blocks both manual and automated
synchronization until a later gate-removal source revision. Runtime comparison
passed with 18 rendered objects after namespace-scoped cluster registration and
external DNS recovery.

Automatic or first manual synchronization remains blocked until all three
application image references have verified nonzero promotion digests, the exact
eight-key Infisical-owned `cristexhub-dev-runtime` Secret is reconciled, and the
approved OIDC egress path is implemented and validated. Enabling automated sync
before those gates would intentionally deploy a broken revision.

## Guarded automated-sync transition (source-only)

`ansible/bin/bootstrap-cristexhub-dev-sync-transition check|apply` is a separate,
source-only transition. It is not part of registration and has not been run. The
active registration manifest remains manual-sync with its deny window. The
transition candidate removes that deny window only while replacing the
Application with `automated.prune=false`, `automated.selfHeal=true`,
`automated.allowEmpty=false`, and `Prune=false`.

The guarded role refuses the transition unless every gate is observed in the
private API: every DEV Deployment and init container uses a digest-qualified
image and is Available; the orphaned Infisical-owned runtime Secret has exactly
its seven keys and metadata closure; the Argo cluster Secret has
`clusterResources=false` and only the `cristexhub-dev` namespace; the
namespace-scoped controller Role exists; the OIDC proxy Deployment is Available;
and every declared PostgreSQL, MongoDB, RabbitMQ, and Redis dependency has a
Service and ready Endpoints. It also requires the current Application to remain
manual and the current AppProject deny window to be exact before writing either
candidate object. No Secret value is read into output, and no prune, namespace
creation, resource replacement, or finalizer is enabled.

This source transition does not assert that any gate passed and does not
activate live. A separately reviewed check/apply/idempotence run and private
runtime validation remain required.

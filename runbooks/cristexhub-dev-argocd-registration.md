# CristexHub DEV Argo registration

This is a source-only, guarded registration closure. It creates no runtime
workloads, Secrets, routes, or namespace. The application repository is pinned
to `https://github.com/devraider/cristexhub.git` at commit
`147bbbf7042e4bbca4bdd026494a855437238654` and path
`infra/kubernetes/cristexhub-dev`.

The AppProject permits only namespaced ConfigMaps, Services, ServiceAccounts,
Deployments, NetworkPolicies, Roles, and RoleBindings in the existing
`cristexhub-dev` namespace. Cluster resources, Ingress, and Secrets are not
allowed. The controller receives only a namespaced Role/RoleBinding.

The wrapper supports `check` only while image digests remain zero placeholders
or `cristexhub-dev-runtime` is absent. `apply` exits before Ansible and is not
an approved operation. First sync remains a separate human approval with no
automated sync, no pruning, no namespace creation, no finalizer, and no
server-side replacement. The namespace remains infrastructure-owned.

Prerequisites before any future apply: verified nonzero image digests and
attestation, Infisical-owned runtime Secret with exact key closure, Argo repo
access, target namespace adoption evidence, and explicit manual-sync approval.

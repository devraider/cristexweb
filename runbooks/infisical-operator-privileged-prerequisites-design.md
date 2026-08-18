# Infisical Operator privileged-prerequisites inventory

## Status and boundary

**DESIGN ONLY — NOT DEPLOYABLE — NOT RUN/BLOCKED.**

This record inventories privileged prerequisite observations from the hash-bound
Infisical Kubernetes Operator `v0.11.7` chart selected for offline source authoring.
It does not promote any chart object, approve a permission, prove compatibility, or
add executable infrastructure. The machine-readable companion is the inert
[`infisical-operator-privileged-prerequisites.yml`](../ansible/files/policies/infisical-operator-privileged-prerequisites.yml)
promotion contract. The later
[implementation profile](infisical-operator-implementation-profile.md) binds the
official controller source and closes only the completed-foundation, exact-watch-
profile, and source-audit gates; every deployable source, trust, compatibility,
recovery, proxy, and
runtime gate below remains blocked.

There is no CustomResourceDefinition, ClusterRole, ClusterRoleBinding, Helm values,
rendered Kubernetes document, controller object, Secret, Ansible wrapper, playbook,
role, provider resource, workflow, or runtime operation in this increment. Committed
Kubernetes source remains exactly the four existing Namespace manifests. No server,
inventory host, kubeconfig, Kubernetes API, registry, Infisical account, provider,
secret store, or network endpoint was contacted.

## Bound source observation

The sole chart source is the vendored archive
`ansible/files/vendor/infisical-operator/0.11.7/secrets-operator-0.11.7.tgz`, whose
SHA-256 is
`7f8846c4f6b1cdca2cea23cf00a29d12a38f42eb8da8e125dc196a1e5683aea8`.
The archive has the safe `secrets-operator` root and 23 members. The
[release selection](infisical-operator-release-selection.md) remains authoritative:
`v0.11.7` is selected for offline source authoring only. The
[candidate record](infisical-operator-candidate-provenance.md) remains authoritative
for unclosed trust, image, compatibility, RBAC, authentication, recovery, traffic,
and runtime gates.

Hash binding supports deterministic inspection of the public input. It does not
cryptographically verify the provenance signature or establish Infisical's current
authorization of the captured key. At this checkpoint no pinned local GPG verifier or
Helm renderer is available, so signature replay and deterministic rendering remain
**NOT RUN** rather than inferred from raw template inspection.

## Exact CRD template inventory

The archive contains seven CRD templates. Each observes
`apiextensions.k8s.io/v1`, group `secrets.infisical.com`, one served storage version,
and no accepted deployment status.

| Definition name | Resource kind | Scope | Served/storage version | Archive template |
|---|---|---|---|---|
| `clustergenerators.secrets.infisical.com` | `ClusterGenerator` | Cluster | `v1alpha1` | `secrets-operator/templates/clustergenerator-crd.yaml` |
| `infisicalauths.secrets.infisical.com` | `InfisicalAuth` | Namespaced | `v1beta1` | `secrets-operator/templates/infisicalauth-crd.yaml` |
| `infisicalconnections.secrets.infisical.com` | `InfisicalConnection` | Namespaced | `v1beta1` | `secrets-operator/templates/infisicalconnection-crd.yaml` |
| `infisicaldynamicsecrets.secrets.infisical.com` | `InfisicalDynamicSecret` | Namespaced | `v1alpha1` | `secrets-operator/templates/infisicaldynamicsecret-crd.yaml` |
| `infisicalpushsecrets.secrets.infisical.com` | `InfisicalPushSecret` | Namespaced | `v1alpha1` | `secrets-operator/templates/infisicalpushsecret-crd.yaml` |
| `infisicalsecrets.secrets.infisical.com` | `InfisicalSecret` | Namespaced | `v1alpha1` | `secrets-operator/templates/infisicalsecret-crd.yaml` |
| `infisicalstaticsecrets.secrets.infisical.com` | `InfisicalStaticSecret` | Namespaced | `v1beta1` | `secrets-operator/templates/infisicalstaticsecret-crd.yaml` |

This is an inventory of raw chart templates, not a rendered object closure, API
server admission result, storage-migration plan, or permission to install the
cluster-scoped generator. Before promotion, every schema, served/storage transition,
conversion behavior, finalizer interaction, upgrade order, backup dependency, and
non-deletion rollback path requires separate review. CRD deletion is not routine
rollback.

## Observed RBAC seams, not approved permissions

The chart's manager helper understands plural scoped Namespaces. With non-empty
scope and scoped RBAC enabled, it emits a Role and RoleBinding for each target
Namespace. The shared manager rule body nevertheless includes creation of
cluster-scoped TokenReview objects and permissions for the cluster-scoped
`ClusterGenerator` resource; putting either rule into a Role cannot authorize it.
The unscoped default instead emits a broad manager ClusterRole and
ClusterRoleBinding and is not accepted for this platform.

The metrics authorization and metrics reader templates test only the deprecated
singular scope value. A plural scoped configuration can therefore retain metrics
ClusterRoles and a ClusterRoleBinding. Conversely, deprecated singular scoped mode
emits a namespaced metrics Role containing cluster-scoped TokenReview and
SubjectAccessReview creation rules, which cannot authorize those requests. Optional
user RBAC can also emit aggregate ClusterRoles carrying the exact
`aggregate-to-admin`, `aggregate-to-edit`, `aggregate-to-view`, and
`aggregate-to-cluster-reader` labels. None of these observed permissions is approved
by being listed here.

A future privileged closure must replace upstream ambiguity with an exact object and
rule inventory. Ansible remains lifecycle owner of accepted CRDs and any narrowly
justified cluster RBAC. Aggregate user roles, a cluster-wide manager, and unused
metrics permissions remain forbidden. Namespaced references can move to Argo only
after Ansible stops reconciling the exact objects and registration, adoption,
successful sync, and managed-field evidence pass. Dual reconciliation is forbidden.

## Authentication and Secret ownership boundary

Universal Auth remains the selected direction, not an implemented bootstrap. The
exact infrastructure machine identity, credential custody, initial write path,
rotation, revocation, compromise response, and independently recoverable off-node
copy are unresolved. Therefore this design does not decide whether TokenReview,
SubjectAccessReview, projected service-account tokens, or `serviceaccounts/token`
permissions are needed.

Infisical Cloud owns generated Secret values. Ansible initially owns privileged
prerequisites and any pre-handoff namespaced reference objects. Argo may later own
committed reference objects after evidenced handoff. No bootstrap credential, secret
value, encoding, identifier, or low-entropy derivative belongs in Git, OpenTofu
state or plans, command arguments, examples, CI output, or review artifacts.

## Promotion gates

Valid Kubernetes or operational Ansible source remains blocked until all of the
following are independently accepted:

1. cryptographic chart-signature replay with a pinned verifier;
2. Infisical signer authorization, revocation status, and current-authority decision;
3. exact schema and Kubernetes `1.36` compatibility review for all seven CRDs;
4. CRD install, upgrade, storage, backup, non-deletion rollback, and ownership policy;
5. deterministic render with a pinned offline renderer and immutable child digest;
6. the selected initial watch Namespaces plus a least-privilege positive/negative
   RBAC matrix;
7. explicit disposition of manager review rules, metrics cluster rules, and aggregate roles;
8. Universal Auth bootstrap, rotation, revocation, compromise, and recovery proof;
9. image signature or attestation identity, SBOM and vulnerability disposition,
   encrypted off-node OCI recovery, and target-node availability;
10. generated Secret lifecycle, one-writer handoff, exact traffic policy, and
    single-node soak acceptance;
11. separately approved foundation Namespace runtime; and
12. separate component check, first apply, idempotence, functional proof, and later
    handoff approvals.

## Stop and rollback

Stop if a later change copies raw templates into valid Kubernetes source, treats a
fingerprint match as signer trust, guesses a Namespace or permission, introduces a
credential or Secret, weakens any blocked gate, or represents static inspection as
render, admission, runtime, or recovery proof.

Rollback for this design-only increment is Git revert. There is no runtime rollback
because no cluster object or external resource was created.

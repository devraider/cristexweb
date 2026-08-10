# Infisical Operator implementation profile

## Status and boundary

**TECHNICAL PROFILE SELECTED — DEPLOYABLE SOURCE BLOCKED.**

This increment binds the official Infisical Kubernetes Operator `v0.11.7` controller
source and records the selected platform profile. It does not deploy or authorize the
Operator. No promoted or repository-operational Kubernetes object or Ansible source
is added. Existing Namespaces, workloads, credentials, Secrets, routes, policies, and
external resources are unchanged.

The machine-readable contract is
[`infisical-operator-implementation-profile.yml`](../ansible/files/policies/infisical-operator-implementation-profile.yml).
The earlier candidate, release-selection, and privileged-prerequisite records remain
authoritative for unclosed chart-signature, signer, image, CRD compatibility,
recovery, rendering, proxy, and runtime gates.

## Commit-bound controller source

The clean-clone evidence closure now includes the official source archive for commit
`64d2d81da3707d81dc271410da6fd88254b6c9b3`. Its SHA-256 is
`a08141c750404c653d23b35ecb29ab33e788845c3f666f0984fa156b9c468415`, and its 307
members have one safe root with no absolute path, parent traversal, symlink, device,
or other non-file/non-directory member. The full upstream archive intentionally
contains its own install manifest, Helm templates, configuration YAML, Dockerfile,
and workflows. Those embedded files are quarantined evidence only: no wrapper,
playbook, role, renderer, workflow, or runtime source may consume them. Their presence
is not a promoted repository object closure or deployment authorization.

The source audit establishes facts that raw chart RBAC could not:

- namespace scoping configures controller-runtime's namespace cache but does not
  select controllers;
- the stock binary unconditionally registers all six namespaced reconcilers;
- ClusterGenerator has no reconciler or eager watch; a PushSecret that explicitly
  references one performs an on-demand cache-backed read that may create a lazy
  informer, so generator references are unsupported under the selected no-CRD/no-
  permission profile;
- Universal Auth reads client references from Kubernetes Secrets and calls Universal
  Auth login; it does not create service-account tokens or TokenReview objects; and
- `--metrics-bind-address=0` disables metrics, while the chart overrides that safer
  binary default.

The implementation profile therefore preserves startup list/watch rights for all six
namespaced custom-resource APIs, omits ClusterGenerator permissions, TokenReview,
SubjectAccessReview, service-account token creation, aggregate roles, manager
ClusterRoles, and metrics authorization RBAC. This is a source-derived future RBAC
profile, not permission to create it.

## Namespace and secret-scope model

The controller will run in `shared-services` and its exact initial namespace cache is
`shared-services`, `argocd`, and `cristexhub-dev`. `cristexhub-prod` remains absent and
unwatched. An empty, wildcard, cluster-wide, or silently expanded cache is forbidden.

Every watched Namespace has a separate identity and credential scope:

- platform shared services use only the `shared-services` logical scope;
- Argo CD uses only the `argocd` logical scope; and
- the DEV application uses only the `cristexhub-dev` logical scope.

The selected intent is that credentials are never shared between these scopes. The
stock APIs permit explicit Namespace fields, while one controller ServiceAccount can
read all three watched Namespaces; namespaced Roles alone therefore cannot prevent a
CR author from referencing another watched Namespace's auth, connection, credential,
source, or target. Promotion requires same-Namespace reference enforcement through a
reviewed admission/source-validation control, restricted CR authorship, and negative
cross-Namespace tests. Until that gate closes, logical identity names are design intent,
not proven isolation. Future components inside `shared-services` still require
separate reviewed sub-scopes and permissions; the Namespace-level identity is not
wildcard admission for databases, Keycloak, RabbitMQ, or any later consumer. PROD requires a new exact identity, source change, isolation
proof, and technical review before it can be watched.

## Controller and CRD direction

The future controller remains one replica on the single node, pinned to the selected
linux/amd64 image reference, with explicit requests and limits. Metrics and its
Service/ServiceMonitor remain absent by selecting `--metrics-bind-address=0`.
Leader election remains enabled in `shared-services` with exact namespaced Lease and
event permissions.

Ansible remains lifecycle owner of accepted CRDs and privileged prerequisites. The
chart will never install CRDs. Six namespaced CRDs are selected for future exact
source because the stock binary registers all six corresponding controllers.
ClusterGenerator has no reconciler or eager watch and is not required for startup.
Its cluster CRD, permissions, and all generator references are excluded; an explicit
reference could trigger a cache-backed lazy informer and must fail source/admission
validation before runtime. CRD deletion is never routine rollback. Kubernetes
`1.36` admission, storage, upgrade, backup, and non-deletion recovery remain blocked
before valid CRD source.

## Egress profile

Standard NetworkPolicy cannot authorize an FQDN. The selected design uses a separate
authenticated Squid proxy in `shared-services`, not a sidecar. Operator policy will
allow DNS, the exact Kubernetes API path, and the proxy only; it will never allow
direct public TCP 443. Proxy ingress will allow only the Operator and require a
TLS-protected authenticated client. The proxy will allow only CONNECT to
`app.infisical.com:443`, reject IP literals and private/special resolved destinations,
and deny everything else without TLS interception.

A CONNECT proxy enforces host and port, not the encrypted `/api` path. A selected
immutable Squid image, publisher/source evidence, TLS/auth compatibility, exact ACL
syntax, NetworkPolicy behavior on k3s, DNS-rebinding negatives, and rollback remain
required. No proxy source is authorized by this profile.

## Secret-zero and first proof

Universal Auth remains the selected mechanism. Bootstrap input will be interactive
and protected by no-log/no-diff handling. The unavoidable Kubernetes credential
Secret is runtime-created only after its exact writer, RBAC, encryption-at-rest
exposure, rotation, revocation, and compromise handling are reviewed. Git contains
neither the credential nor a recoverable derivative.

Recovery uses an age-encrypted off-node copy in Google Drive, with the age key held
separately. Exact custodians, folders, retention, restoration, overlap rotation, and
revocation evidence remain unresolved and therefore block a bootstrap write.

The first functional proof will use a dedicated read-only DEV identity and one fixed
public marker. A v1beta1 static-secret reference will target a non-sensitive ConfigMap
in `cristexhub-dev` with orphan creation policy and no workload reload. This later
proof will validate authentication and reconciliation only; it will not prove Secret
confidentiality or authorize application values.

## Ownership and ordering

Ansible owns CRDs, privileged RBAC, and the controller until an object-specific Argo
handoff is evidenced. Infisical Cloud owns generated values. Argo may later own
value-free namespaced references only after Ansible stops reconciling them and exact
registration, successful sync, managed fields, rollback, and soak evidence pass.
Dual reconciliation and Git-authored generated Secrets are forbidden.

The required order remains: close trust/render/compatibility/recovery gates; author
and validate exact prerequisite source; author an idle controller and proxy closure;
run their guarded check/apply/idempotence sequences; prove negative RBAC and network
access; establish secret-zero recovery; then perform one non-sensitive ConfigMap
sync. Failure never widens RBAC, egress, watch scope, or credential sharing.

## Remaining blockers

Promoted Kubernetes and operational Ansible source remain blocked by chart signer
authorization, cryptographic verification, deterministic rendering, CRD admission and
storage recovery, image SBOM/vulnerability disposition and off-node recovery, exact
same-Namespace reference enforcement, Squid image/config selection, proxy
compatibility, exact k3s traffic proof, secret-zero custody/recovery,
rotation/revocation, and single-node soak.

Rollback for this source-readiness increment is Git revert. There is no runtime
rollback because it creates no cluster object, credential, Secret, provider resource,
or external change.

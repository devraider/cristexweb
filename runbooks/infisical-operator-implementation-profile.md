# Infisical Operator implementation profile

## Status and boundary

**GUARDED IDLE SOURCE READY — RUNTIME NOT RUN/BLOCKED.**

The repository now promotes an exact value-free Infisical Kubernetes Operator
`v0.11.7` idle closure. It contains 40 hash-bound objects under
`ansible/files/components/infisical-operator`, a dedicated present-only guarded
Ansible entrypoint, six native same-Namespace admission policies, and an authenticated
TLS Squid proxy. It does not deploy Infisical Cloud itself. No credential value,
Infisical custom resource, PROD scope, route, or external resource is added. Runtime
still requires the separately created proxy bootstrap Secrets and guarded check,
first apply, and idempotence evidence.

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

The promoted manager Roles preserve startup list/watch rights for all six namespaced
custom-resource APIs and omit ClusterGenerator permissions, TokenReview,
SubjectAccessReview, service-account token creation, aggregate roles, manager
ClusterRoles, and metrics authorization RBAC. Runtime proof remains required; a
permission error stops the bootstrap instead of authorizing wildcard widening.

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
source, or target. Six `admissionregistration.k8s.io/v1` ValidatingAdmissionPolicies and bindings now
enforce Universal Auth, exact Infisical Cloud API use, same-Namespace auth,
connection, credential, source, target, and TLS references, and no generator
references with `failurePolicy: Fail` and `Deny`. Restricted CR authorship remains
mandatory. Kubernetes 1.36 admission and negative cross-Namespace runtime tests are
still required before logical identity names become proven isolation. Future components inside `shared-services` still require
separate reviewed sub-scopes and permissions; the Namespace-level identity is not
wildcard admission for databases, Keycloak, RabbitMQ, or any later consumer. PROD requires a new exact identity, source change, isolation
proof, and technical review before it can be watched.

## Controller and CRD direction

The promoted controller is one replica on the single node, pinned to the selected
linux/amd64 image reference, with explicit requests and limits. Metrics and its
Service/ServiceMonitor remain absent by selecting `--metrics-bind-address=0`.
Leader election remains enabled in `shared-services` with exact namespaced Lease and
event permissions.

Ansible remains lifecycle owner of accepted CRDs and privileged prerequisites. The
chart is never installed at runtime. Six complete namespaced CRDs are promoted from
the hash-bound chart with a template-to-file SHA-256 mapping because the stock binary
registers all six corresponding controllers.
ClusterGenerator has no reconciler or eager watch and is not required for startup.
Its cluster CRD, permissions, and all generator references are excluded; an explicit
reference could trigger a cache-backed lazy informer and must fail source/admission
validation before runtime. CRD deletion is never routine rollback. Kubernetes
`1.36` admission, storage, upgrade, backup, and non-deletion recovery remain live
acceptance gates; valid CRD source is now present.

## Egress profile

Standard NetworkPolicy cannot authorize an FQDN. The selected design uses a separate
authenticated Squid proxy in `shared-services`, not a sidecar. Operator policy will
allow DNS, the exact Kubernetes API path, and the proxy only; it will never allow
direct public TCP 443. Proxy ingress will allow only the Operator and require a
TLS-protected authenticated client. The proxy will allow only CONNECT to
`app.infisical.com:443`, reject IP literals and private/special resolved destinations,
and deny everything else without TLS interception.

A CONNECT proxy enforces host and port, not the encrypted `/api` path. The proxy is pinned to Canonical's reviewed linux/amd64 child digest. Its selected
configuration uses `https_port`, NCSA Basic authentication, exact CONNECT host/port
ACLs, private/special destination denies, no interception, and deny-all termination.
Three runtime-created Secrets provide proxy TLS, the NCSA file, and the authenticated
proxy URL; their values are never committed. Exact image behavior, TLS/auth
compatibility, NetworkPolicy behavior on k3s, DNS-rebinding negatives, and rollback
remain live gates.

## Secret-zero and first proof

Universal Auth remains the selected mechanism. Bootstrap input will be interactive
and protected by no-log/no-diff handling. The unavoidable Kubernetes credential
Secret is runtime-created only after its exact writer, RBAC, encryption-at-rest
exposure, rotation, revocation, and compromise handling are reviewed. Git contains
neither the credential nor a recoverable derivative.

Recovery uses an age-encrypted off-node copy in Google Drive. Only ciphertext and
checksum move to the k3s host, where pinned host rclone performs immutable transfer;
the age key remains on the controller and needs an independently protected custody
copy. Exact custodians, host OAuth/account recovery, folders, retention, restoration,
overlap rotation, and revocation evidence remain unresolved and therefore block a
bootstrap write.

The first functional proof will use a dedicated read-only DEV identity and one fixed
public marker. The source-only
[Universal Auth/value lane](infisical-universal-auth-value-lane.md) freezes the
protected identity/file/Keychain and recovery boundary for that identity and the
three bootstrap scopes, but does not create identities, projects, or runtime
Secrets; its seed/upload and rotation gates remain **NOT RUN/BLOCKED**. A v1beta1
static-secret reference will target a non-sensitive ConfigMap
in `cristexhub-dev` with orphan creation policy and no workload reload. This later
proof will validate authentication and reconciliation only; it will not prove Secret
confidentiality or authorize application values.

## Ownership and ordering

Ansible owns CRDs, privileged RBAC, and the controller until an object-specific Argo
handoff is evidenced. Infisical Cloud owns generated values. Argo may later own
value-free namespaced references only after Ansible stops reconciling them and exact
registration, successful sync, managed fields, rollback, and soak evidence pass.
Dual reconciliation and Git-authored generated Secrets are forbidden.

The required order is now: install and attest pinned host rclone; complete interactive
non-root host OAuth; transfer/read back and controller-verify the existing encrypted
pending proxy bundle; create and recover the three proxy bootstrap Secrets; run the
dedicated guarded check; review its exact 40-object prediction; run first apply
and idempotence; prove admission, negative RBAC, proxy-only egress, and idle health;
establish separate Infisical Universal Auth recovery; then perform one non-sensitive
ConfigMap sync. Failure never widens RBAC, egress, watch scope, or credential sharing.

## Remaining blockers

Runtime remains blocked until the proxy bootstrap values have independent recovery,
the guarded check predicts only the exact closure, Kubernetes accepts every CRD/CEL
expression, both workloads pull and become Available, proxy-only traffic is proved,
and first apply/idempotence finish without an unexpected object or writer. Image
signer/SBOM/vulnerability and off-node OCI recovery remain explicit private-MVP risk
acceptance items; secret-zero recovery, rotation/revocation, and single-node soak
remain mandatory before application values or PROD.

Before first apply, rollback is Git revert. After apply, rollback preserves CRDs and
bootstrap Secrets and stops only the exact controller/proxy workloads through a
separately reviewed present-state change; it never deletes Namespaces, CRDs, Secrets,
or PVCs.

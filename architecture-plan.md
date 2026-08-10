# Single-node k3s architecture plan

## Status

This target design has the existing bounded Ansible workflows plus an
executed non-destructive storage-discovery increment and temporary CNI/NetworkPolicy
functional probe. Extended storage discovery confirmed the live curated device and
PV/PVC indicators, while the approved probe passed against the Kubernetes API using an
independently verified linux/amd64 digest and temporary Argo CD ownership exception.
The implementation used generated names, exact UID cleanup, dual-label fixed-kind
recovery discovery, selectorless Service plus explicit EndpointSlice, non-cascading
deletion, and no Namespace create/delete; post-run verification found zero residue.
Read-only discovery, the Kubernetes-module dependency
bootstrap, and group-scoped k3s administrator access have been executed under
`ansible/`; effective-user readability, fresh-session cluster listing, and
idempotence passed. The executed user-scoped
kubectl client-defaults playbook also passed warning-free fresh-session queries and
idempotence. The approved one-reboot recovery playbook passed with SSH/Tailscale
return, running services, a new boot ID, a Ready node, and preserved access. They
are not a general host
baseline, hosted runtime, or IaC reconciler.
Python is limited to offline contract tests. No hosted orchestration,
DNS, tunnels, GitOps, secrets, databases, backups, or operational replacement-host
recovery are implemented. The first replacement increment is a secret-free,
decision-first runbook and artifact register only; it does not resolve or automate
the unknown k3s datastore/version/token, storage, RPO/RTO, or off-node recovery
prerequisites. CristexHub local Compose assets remain an external
application-repository concern.

## Known facts

A read-only host inspection observed a Debian 13 single-node k3s server with about
16 GiB RAM, an NVMe system disk, a separate unmounted 1 TB rotational disk with one
partition and filesystem still unverified, and Tailscale installed. k3s is active.
Approved extended elevated discovery has reverified the datastore, node, Traefik,
local-path StorageClass (`Delete`, `WaitForFirstConsumer`, no expansion), zero
current PV/PVC objects, and curated kube-system workload indicators through the
protected group-scoped kubeconfig. That historical live report did not capture a
Kubernetes version and used `shared-data` rather than the current `shared-services`
PVC scope. The separately approved schema-v3 rerun passed at
`ok=17 changed=1 unreachable=0 failed=0 skipped=1`; the change was only the ignored
controller-local report write. Human review confirmed kubelet `v1.36.2+k3s1`, all 15
bounded queries available, and the exact `shared-services` PVC query with count zero.
Argo CD `3.5` officially lists Kubernetes minor `1.36` in its tested matrix and chart
`10.3.0` admits the target through its semver gate. This is target-minor screening,
not k3s-specific runtime or rendered API/CRD compatibility proof. Reboot recovery,
independent fallback access, CNI behavior, and NetworkPolicy enforcement are
verified for the current
single-node cluster; replacement-host recovery still requires separate verification.

The external CristexHub application repository now has SHA-pinned, read-only source
CI for backend, frontend, and code-runner; its previous untrusted GHCR publisher is
disabled until immutable build inputs and digest/SBOM/provenance evidence pass. This
repository also has one SHA-pinned read-only CI workflow as source, but neither
workflow has been pushed or run. This repository implements seven executed bounded
Ansible workflows, including the temporary functional probe. It now has an
offline-validated gated OpenTofu installer and zero-resource Cloudflare-only source
scaffold. The first live run stopped after two bounded directory tasks because the
host had no route to GitHub. The reviewed controller-cache and Ansible-transfer
recovery subsequently passed check, live installation, and a `changed=0` rerun; the
pinned CLI and selector now exist without host egress. Committed Kubernetes desired
state now contains exactly four Namespace manifests: `argocd`, `platform-edge`,
`shared-services`, and source-only `cristexhub-dev`. The closed historical bootstrap owns only `argocd` and
`platform-edge`; the distinct present-only `shared-services` bootstrap passed check
and separately approved first apply/idempotence; the final run converged at
`changed=0`. A dedicated [CristexHub DEV Namespace bootstrap](runbooks/cristexhub-dev-namespace-bootstrap.md)
is exact present-only source with four approved labels; its runtime remains NOT RUN
and `cristexhub-prod` is absent. The superseded `platform-secrets`/`platform-identity` source never
ran, and its removal is not a live rename or deletion. The separately approved
historical first apply created exactly those
two Active Namespaces with the reviewed labels. The separately approved idempotence
checkpoint first stopped before Kubernetes reconciliation on failed local sudo
authentication at `changed=0`; its retry passed at `ok=21 changed=0 failed=0` with
exact post-state and service-health verification. No workload or other persistent
kind exists from this increment. The source-only
[Argo CD candidate provenance record](runbooks/argocd-candidate-provenance.md)
records chart `10.3.0`, application `v3.5.0`, captured signature/hash-binding,
immutable linux/amd64 images, and curated online/static readiness evidence. The
separate release record selects that pair only for offline source authoring; it
remains **NOT DEPLOYABLE**. The exact 44-document
render was reproduced at Kubernetes capability `1.36.2`, stable upstream API
registration screened successfully, and controller-side image closure was reachable.
Exact k3s admission/runtime and node pullability remain unproven. Wildcard/broad
RBAC, ingress-only/unrestricted-egress policy, image trust, Secret recovery, private
Git secret-zero, Namespace adoption, trust/soak acceptance, and runtime approvals
remain blockers. Only hash-bound non-executable public chart inputs are vendored; no
values or Kubernetes object source exists. The
[source-only hardened design](runbooks/argocd-hardened-design.md) accepts a private
ClusterIP and loopback-only port-forward direction, retained quiescent ApplicationSet,
supplemental ingress/egress default-deny with an explicit broad ports-only
`443`/`6443` weakness, phased least-privilege RBAC/AppProjects, one-repository
read-only GitHub App credentials, value-free Infisical custody, and two independent
Namespace-adoption Applications. It accepts the selected offline baseline but adds
no deployable controller source. Ansible is selected as the future bounded bootstrap installer and lifecycle
owner of privileged CRDs/cluster RBAC. The foundation Namespace check/first apply
passed and the separately approved idempotence run converged at `changed=0`; exact
controller bootstrap source and credentials,
resource/GVR/discovery inventory, Infisical Universal Auth recovery, live adoption
apply mode, and activation of selected Keycloak/Argo OIDC policy remain open
architecture decisions. The source-only
[Keycloak OIDC bootstrap design](runbooks/keycloak-oidc-bootstrap-design.md) selects
one future self-hosted Keycloak shared by CristexHub, Reactive Resume, and Argo CD.
Keycloak `26.7.1`, PostgreSQL `17.10`, realm `cristexhub`, and issuer
`https://auth.cristex-soft.com/realms/cristexhub` are selected only for offline source
authoring. No workload, Secret, route, or executable controller source is selected,
and runtime is **NOT RUN/BLOCKED**. The value-free
[Reactive Resume hosted architecture](runbooks/reactive-resume-hosted-architecture.md)
includes private DEV in the MVP, reserves a separate future PROD instance, and binds
each to a dedicated PostgreSQL and OIDC consumer scope. Its upstream image,
callbacks, resources, Secrets, recovery, and runtime remain unselected or blocked.
The separate source-only
[cloudflared candidate provenance record](runbooks/cloudflared-candidate-provenance.md)
records official release `2026.7.3`, its unsigned tag/commit, immutable linux/amd64
image evidence, token-file precedence, connection-aware readiness, and required edge
transport. It is **CANDIDATE — NOT DEPLOYABLE — NOT SELECTED**, runtime is **NOT
RUN**, and publisher trust, image assurance/availability, container hardening,
Infisical token recovery, OpenTofu state/resource gates, Argo handoff, exact
DNS/Traefik/edge policy, route approval, soak, and runtime approvals remain blocked.
It adds no OpenTofu resource, Kubernetes object, secret, route, or deployment source.
The source-only
[Infisical Operator candidate provenance record](runbooks/infisical-operator-candidate-provenance.md)
distinguishes latest source release `v0.11.8`, whose matching public chart archive
and image tag were not observed during the bounded capture, from the version-aligned
`v0.11.7` set. The separate release record selects `v0.11.7` only for offline source
authoring and Universal Auth as direction; it remains not deployable and runtime is
**NOT RUN/BLOCKED**. Actual compatibility, chart/image trust, dedicated Namespace,
scoped RBAC, Argo handoff, secret-zero, network policy, recovery, and runtime
approvals remain blocked. It adds no chart, CRD, Kubernetes object, credential, or
Secret source.
No state file, provider initialization, plan, apply, Helm installation, Kustomize
workload, image publication, or general host baseline exists yet. The committed CI
source has no package-write, Secret, provider, host, cluster, or deployment path;
source-only run `31311995461` passed exact commit
`e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`. Debian plus Ansible is
the selected host-configuration owner.

## Goals

- Teach one infrastructure layer at a time without an enterprise-sized platform.
- Reproduce host intent, external resources, and Kubernetes desired state from Git.
- Keep DEV and all administrative surfaces private.
- Expose only approved PROD application routes through Cloudflare Tunnel.
- Fit DEV and PROD within one resource-constrained node using explicit limits.
- Recover on replacement hardware from Git, secret recovery material, images, and
  verified off-host backups.

## Non-goals

- high availability or zero downtime;
- a second ingress controller, service mesh, Longhorn, or autoscaling platform;
- public databases, brokers, Argo CD, k3s API, SSH, or dashboards;
- self-hosted Infisical, registry, or CI runner during the first implementation;
- automatic PROD promotion or destructive automatic rollback;
- moving privileged code-runner onto the shared node without separate isolation.

## Ownership model

| Layer | Owner | State source |
|---|---|---|
| Debian host and k3s baseline | Ansible | playbooks and inventory under `ansible/` |
| Bounded foundation bootstrap, privileged CRDs/cluster RBAC, and Keycloak realm/client/group reconciliation | Ansible | future component-specific source closures and separate approvals |
| Cloudflare and GitHub resources | OpenTofu | configuration under `opentofu/`; protected host-local single-writer state plus mandatory encrypted off-node recovery |
| Namespaced Kubernetes desired state after evidenced handoff | Argo CD | manifests and Helm values under `kubernetes/` |
| Secret values and rotation | Infisical Cloud initially | separate DEV, PROD, and infrastructure scopes |
| CI and image publication | GitHub Actions | read-only source CI now; future immutable GHCR digests only after separate trust/publication approval |
| Approvals and recovery | Human operator | reviewed evidence and runbooks |

One resource has one owner. OpenTofu must not reconcile Kubernetes resources also
owned by Argo CD. GitHub Actions validates and publishes; it does not deploy.
The bounded `network_policy_probe` Ansible role implements an ephemeral QA
exception but does not authorize its own execution. API-generated names and labels
establish ownership atomically; a private ledger records exact UIDs; cleanup verifies
labels and UID preconditions, uses `Orphan` propagation, and proves zero residue
without deleting a Namespace. Runtime still requires separate human approval of the ownership
exception plus create and delete actions. A separate one-time bootstrap exception
may create or reconcile only the committed `argocd` and `platform-edge` Namespaces,
with no delete path and foreign-existing refusal. The manifests identify Ansible as
bootstrap writer and Argo CD only as future desired owner. Argo ownership remains
pending until Argo CD is installed, the Namespaces are adopted or registered through
an Application, and successful sync evidence exists; the label alone is not a
handoff. The completed exception remains closed and authorizes no future component or
Namespace.

Ansible is selected as the future bounded bootstrap installer for exact foundational
Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, one self-hosted
Keycloak, and privileged cluster-scoped prerequisites. Each component still needs a
dedicated exact source closure plus separate check, apply, and idempotence approvals;
this design authorizes none. Ansible remains lifecycle owner of privileged CRDs,
ClusterRoles, ClusterRoleBindings, and Keycloak realm/client/group reconciliation.
A namespaced specification may hand off to Argo only after Ansible stops reconciling
the exact object set and registration/adoption, successful sync, and managed-field
evidence pass. Dual reconciliation is forbidden. Operational procedures belong under
`runbooks/` when implementation is approved.

## Traffic model

```text
Private administration and DEV
operator device -> Tailscale -> SSH/k3s API or an explicitly private service

Public PROD
Internet -> Cloudflare -> cloudflared -> bundled Traefik -> PROD frontend gateway
```

Bundled k3s Traefik remains the sole ingress controller. The frontend nginx image
in the external CristexHub application repository remains the application gateway
for `auth_request`, API proxying, and WebSockets; it is not the cluster ingress
controller. Application source, local Compose, development Keycloak realm/theme, and Browserless
gateway assets remain in that application repository and are not copied here. One
future self-hosted production Keycloak is the shared identity architecture target,
but its release and deployable source remain unselected.

The first private DEV hostname may use a tailnet name. A custom private
`dev-hub.cristex-soft.com` name requires a later private-DNS and certificate
decision. The intended public PROD host is `hub.cristex-soft.com`.

Cloudflare Tunnel must never route DEV, SSH, k3s API, Argo CD, databases, Redis,
RabbitMQ management, Browserless, code-runner, Keycloak administration, or its
management listener. A future Keycloak browser-authentication route is a separate
public-route decision and does not authorize any administration path. Cloudflare and
Tailscale do not replace application OIDC/JWT enforcement.

## Namespace model

| Namespace | Purpose |
|---|---|
| `argocd` | Argo CD controllers and private UI/API |
| `platform-edge` | Cloudflare Tunnel connector only; no Keycloak, Infisical Operator, database, or route exists; every route remains separately approved |
| `shared-services` | Exact present-only Namespace exists after passed check/first apply/idempotence; future placement for the Infisical Cloud Operator, separate Keycloak, one PostgreSQL, one MongoDB, and one shared RabbitMQ engine remains undeployed |
| `cristexhub-dev` | Exact present-only source exists with approved application/environment/bootstrap/future-owner labels; check/apply/idempotence NOT RUN; future DEV applications and environment-local dependencies remain undeployed |
| `cristexhub-prod` | Absent and without executable Namespace source; blocked until DEV validation, recovery, and soak |
| Optional backup/monitoring namespaces | Added only when their first workload is approved |

Namespace names organize ownership but are not a hard security boundary. Service
accounts, RBAC, NetworkPolicy, database authorization, credentials, and negative
connectivity tests provide the enforceable controls.

## Shared data design

A single PostgreSQL engine and a single MongoDB engine save memory. This is an
explicitly accepted shared failure and contention domain. The value-free
[`shared-database-architecture.yml`](ansible/files/policies/shared-database-architecture.yml)
is the canonical source-only topology and authorization contract; its promotion
gates are all closed and it is not executable workload source.

PostgreSQL requires separate logical databases and owner roles for CristexHub DEV,
CristexHub PROD, Reactive Resume DEV, Reactive Resume PROD, and Keycloak. Keycloak
remains a separate deployment from the one general PostgreSQL instance and receives
its own database, owner role, credential, and backup scope; no consumer receives
another PostgreSQL workload or PVC. CristexHub and Reactive Resume DEV/PROD receive
separate PostgreSQL credentials, migrations, and backups. MongoDB requires
CristexHub DEV/PROD databases and users with privileges limited to their own
database.
DEV and PROD never share an application credential, encryption key, migration target,
or backup prefix. MongoDB repository/version/digest and standalone-versus-replica-set
topology remain unselected.

Application and Keycloak roles must not create roles or databases. The Keycloak role
cannot access application databases, and application roles cannot access the
Keycloak database; those denials require negative grant tests. MongoDB workload users must have no broad any-database or
user/role-administration roles and must fail bidirectional cross-database tests.
The selected ownership direction is idempotent Ansible bootstrap followed by exact
object-by-object Argo handoff. The workflow remains unimplemented and unproved. Its
administrator credential must remain Infisical-owned and unavailable to application
or Keycloak pods.

Redis remains per environment because Redis database numbers are not sufficient
security isolation. One shared RabbitMQ engine belongs in `shared-services`.
CristexHub DEV/PROD receive distinct users, virtual hosts, permissions, limits, and
recovery scopes with negative cross-vhost tests. Future consumers require reviewed
exact policy/test changes; wildcard or dynamic admission is forbidden. A later
capacity decision may separate the engine.

NetworkPolicy must allow each application namespace and the Keycloak workload to
reach only the shared database Services and other exact approved endpoints, while
denying cross-environment application traffic. NetworkPolicy cannot isolate logical
databases on a shared endpoint, so PostgreSQL/MongoDB authorization and negative
tests are mandatory. Database engines remain ClusterIP-only. The general PostgreSQL engine/PVC
is a shared failure domain even though Keycloak has a separate database, role,
credential, backup scope, connection policy, and recovery acceptance.

## Secrets

Infisical Cloud stores values during the initial implementation; self-hosting is
out of scope. Git stores only secret references. DEV, PROD, and infrastructure use
separate scopes and machine identities with least privilege. The bootstrap method
is a decision gate because Argo private-repository access, Infisical
authentication, GHCR pulls, and Cloudflare connector credentials form a secret-zero
sequence. Only the Infisical Cloud Kubernetes Operator is bootstrapped; a self-hosted
Infisical server is not selected. The future Keycloak OIDC client secret and database
credentials are Infisical-owned values with independent bootstrap recovery.

Secret values must not pass through OpenTofu state, saved plans, Argo parameters,
committed manifests, examples, or CI logs. Recovery material, including application
encryption keys, is stored off-node in at least two protected locations.

## Delivery flow

```text
Pull request -> tests and offline IaC validation
merge -> build once -> push SHA-tagged image to GHCR
reviewed Git change -> pin image digest in DEV
Argo CD -> reconcile DEV -> validate and soak
reviewed promotion -> same digest in PROD
Argo CD -> private PROD validation -> approved Cloudflare cutover
```

`latest` may be published for compatibility but must never be deployed. Initial
PROD sync and promotion remain manual and reviewed.

## Storage and backup

Live database PVCs are expected on the NVMe through the discovered local
StorageClass. Approved extended read-only discovery has captured curated
device/partition and direct mount indicators, exact StorageClass behavior, and
bounded PV/PVC placement metadata from the live host and cluster. The separate 1 TB disk
is not usable until its contents, ownership, filesystem choice, mount path, and
destructive formatting approval are confirmed. Storage discovery makes no mount,
repair, write, format, or ownership change; Ansible remains the host/mount owner.
Argo CD becomes the namespaced desired-state reconciler for one exact object set only
after Ansible stops reconciling it and installation, registration/adoption,
successful sync, and managed-field evidence pass. Ansible retains lifecycle ownership
of privileged CRDs and cluster RBAC.

Backups require database-consistent PostgreSQL and MongoDB dumps, protected RabbitMQ
definitions, separate consumer/purpose paths, compression, encryption, integrity
checks, local retention, and an encrypted off-host copy. The intended off-host target
is Google Drive through containerized `rclone copy`, not destructive `sync`.
Operator access uses a private authenticated metadata-only catalog plus a simple
list/retrieve/verify workflow; no public or anonymous link is allowed. RabbitMQ
definitions recovery does not prove queued-message recovery, so application
reconciliation remains mandatory. k3s datastore and recovery token, OpenTofu state,
Infisical recovery credentials, and runbooks require separate recovery coverage.

A successful backup job is not acceptance. An isolated restore and application
verification must meet the declared RPO/RTO before PROD.

## Staged delivery

### Stage 0 — documentation foundation

- Entry: approved technology direction.
- Work: rules, architecture, requirements, tasks, and tests only.
- Gate: offline documentation checks and independent review.
- Stop: any wording claims an implemented hosted environment.
- Rollback: revert documentation changes.

### Stage 1 — read-only discovery

- Entry: the offline Ansible discovery implementation is approved; actual SSH,
  host, cluster, or elevated access still requires its own explicit approval.
- Work: use Ansible built-ins for bounded host facts and
  `kubernetes.core.k8s_info` for exact Kubernetes kinds. Project only curated OS,
  capacity, service, filesystem, datastore-presence, object-name/count fields, and
  the existing Node name/cluster scope plus exact kubelet version string into one
  controller-local report.
- Safety: the play requires check/diff mode, an explicit one-host limit, default
  non-elevation, and two explicit flags before narrowly scoped become tasks. It
  never uses shell/command automation or queries Secret, ConfigMap, Events, or a
  broad `all` resource set.
- Limit: object listings are configuration/capability indicators only. CNI behavior
  and NetworkPolicy enforcement require later approved functional probes and are
  not proven by discovery.
- Current evidence: the locked local environment, syntax, lint, and non-elevated
  one-host report pass. A temporary generated-name functional probe is implemented
  and validated offline. Exact-UID cleanup, an interruption ledger, no Namespace
  create/delete, and baseline/deny/selective/rollback standalone Pods close the earlier design
  blockers. The approved live run used an independently verified official BusyBox
  linux/amd64 manifest, passed baseline/deny/selective/rollback evidence, deleted
  exact objects, and passed a separate zero-residue cleanup check. The approved bootstrap directly requested only
  `python3-kubernetes` and `python3-jsonpatch`; apt installed 37 packages including
  dependencies, and post-install imports pass. The
  elevated report confirms the datastore and nine then-current available exact
  Kubernetes queries. The later schema-v3 elevated rerun confirms kubelet
  `v1.36.2+k3s1`, all 15 bounded queries available, and the current
  `shared-services` PVC query with count zero. The first attempt at that rerun omitted
  the ignored local inventory and stopped unreachable before discovery; the corrected
  explicit inventory command succeeded. Reboot recovery and the bounded
  CNI/NetworkPolicy probe passed; replacement-host recovery remains unproven.
- Gate: human-reviewed local report and decision register update.
- Stop: a task needs mutation, secret output, or elevated access beyond the two
  approved dependency packages and discovery scope.
- Rollback: the only approved target-state change is the recorded apt transaction.
  Any package removal requires a separately reviewed apt plan; do not remove
  transitive packages blindly. The discovery play's only write is the explicitly
  requested controller-local report.

### Stage 2 — host safety baseline

- Entry: recovery access, current backup, and reviewed Ansible check/diff.
- Work: bounded SSH, firewall, mount, kubeconfig, and k3s configuration changes.
- Gate: second Ansible run is idempotent; SSH and Tailscale recovery survive reboot.
- Stop: loss of access, unexpected package/network change, or disk ambiguity.
- Rollback: restore preserved host configuration and known-good access path.

### Stage 3 — external-resource preparation

- Entry: protected host-local single-writer state, proven encrypted off-node recovery, least-privilege credentials, reviewed plan.
- Work: Cloudflare/GitHub resources only; no public route yet.
- Gate: plan contains only approved resources and state recovery is tested.
- Stop: secret value in state/plan or destructive replacement.
- Rollback: reviewed reverse plan; never blind destroy.

### Pre-Stage-4 — bounded platform Namespace bootstrap exception

- Entry: freeze and validate the exact reviewed source, then obtain a separate human
  approval for `ansible/bin/bootstrap-platform-namespaces check`.
- Check evidence: the separately approved wrapper check passed at
  `ok=19 changed=1 unreachable=0 failed=0 skipped=2`; all protected preflight
  assertions passed and the single changed loop task predicted exactly `argocd` and
  `platform-edge`. Check mode created nothing and skipped live post-state verification
  by design.
- First-apply evidence: the separately approved wrapper apply passed at
  `ok=21 changed=1 unreachable=0 failed=0 skipped=0`; the single changed loop task
  changed exactly the committed `argocd` and `platform-edge` Namespace manifests
  with `state:
  present`. Protected post-state assertions verified both exact identities, the
  reviewed labels, `Active` phase, and service health. No deletion or other persistent
  Kubernetes kind is authorized; none was changed.
- Idempotence evidence: during the separately approved second wrapper checkpoint, an
  initial invocation stopped before service preflight and Kubernetes reconciliation
  because local sudo authentication failed. It reported
  `ok=10 changed=0 unreachable=0 failed=1 skipped=0`, made no mutation, and proved no
  idempotence. The retry passed at
  `ok=21 changed=0 unreachable=0 failed=0 skipped=0`; both exact reconciliation items
  were `ok`, protected identity/label/`Active` assertions passed, and service health
  remained verified before and after.
- Gate result: the exact check, first apply, and idempotence checkpoints are complete;
  the exception is closed and authorizes no further Namespace bootstrap execution.
- Stop: foreign ownership, an unexpected object or change, source drift, failed
  verification, or nonzero change would have stopped the checkpoint.
- Ownership: Ansible remains the bootstrap writer. Argo CD is only the future desired
  owner until installation, adoption or Application registration, and successful
  sync evidence; a label alone is not a handoff.
- Boundary: this exception does not waive the Stage 4 entry gates and does not
  authorize Argo CD, Infisical, cloudflared, or any other persistent Kubernetes
  object.

### Pre-Stage-4B — bounded foundation Namespace source

- Source: one exact manifest and a distinct guarded Ansible bootstrap are implemented
  for only `shared-services`; the superseded two-Namespace source never ran and was
  removed without contacting the cluster; see the
  [foundation Namespace bootstrap runbook](runbooks/foundation-namespace-bootstrap.md).
- Separation: the historical wrapper, role, manifests, and evidence remain unchanged
  and closed. The new wrapper has its own playbook, role, environment namespace, and
  ephemeral single-run attestation.
- Runtime: wrapper check, separately approved first apply, and separately approved
  idempotence passed; the final run converged at `changed=0`. No component was deployed.
- Boundary: state is present-only; no delete path, Secret, ServiceAccount, workload,
  Service, policy, PVC, chart, values, route, or other persistent kind exists in this
  increment. Check mode predicts but makes no live post-state claim.
- Ownership: Ansible is bootstrap writer and the Argo label is future intent only;
  handoff requires later registration/adoption, successful sync, managed-field
  evidence, and cessation of Ansible reconciliation.

### Stage 4 — minimal GitOps and secrets bootstrap

- Current source-only evidence: the
  [Argo CD candidate provenance record](runbooks/argocd-candidate-provenance.md)
  binds public chart, captured signature/hash-binding, image metadata, and curated
  online/static readiness evidence. The candidate retains ApplicationSet because
  chart `10.3.0` has no effective parent disable gate. Its 44-document render is
  reproducible at Kubernetes capability `1.36.2`, every rendered built-in kind is
  registered in upstream Kubernetes `v1.36.2`, and the controller reached both exact
  image closures. This is not version selection, deployable desired state, exact k3s
  admission/runtime, or node pullability proof; wildcard/broad RBAC,
  ingress-only/unrestricted-egress policy, image trust, Secret recovery, private Git,
  and adoption decisions remain blocked.
- Current source-only hardened design: the
  [Argo CD hardened design](runbooks/argocd-hardened-design.md) keeps all Services
  ClusterIP and administration behind Tailscale, authenticated k3s access, and a
  loopback-only port-forward, with no route. It retains ApplicationSet quiescent;
  its webhook listener and TCP `7000` ClusterIP Service remain present while exposure
  and use are denied. It disables future chart policies in favor of one complete
  supplemental ingress/egress default-deny set, explicitly accepting broad ports-only
  TCP `443`/`6443` rather than claiming endpoint/FQDN/TLS-identity isolation. It also
  selects the one-repository read-only GitHub App credential shape, value-free
  Infisical custody, Redis initializer removal, phased least-privilege direction, and
  two independent adoption Applications. This is **DESIGN ONLY**: chart `10.3.0` and
  app `v3.5.0` are selected only for offline source authoring and remain **NOT
  DEPLOYABLE**; runtime is **NOT RUN/BLOCKED**, and no RBAC, AppProject, policy,
  Secret, Application, values, or manifest source exists from this design.
- Updated hardened-design ownership: Ansible is selected as bounded bootstrap
  installer and lifecycle owner of privileged CRDs/cluster RBAC. Five decisions remain:
  (1) exact component Ansible source/object/credential closure and approvals, (2)
  exact resource/GVR/discovery inventory, (3) Infisical authentication and independent
  recovery, (4) first-sync apply mode after live Namespace field evidence, and (5)
  stable Keycloak issuer/callback/TLS plus direct OIDC/RBAC acceptance. Completed
  `shared-services` check/first apply/idempotence is retained as prerequisite evidence. The completed
  historical Namespace exception remains closed and none of these items is runtime
  approval.
- Current source-only identity design: the
  [Keycloak OIDC bootstrap design](runbooks/keycloak-oidc-bootstrap-design.md) selects
  one future self-hosted Keycloak shared by CristexHub, Reactive Resume, and Argo CD
  as the identity architecture target. Keycloak authenticates and emits groups; Argo
  RBAC authorizes Argo actions; Kubernetes RBAC independently constrains controller
  ServiceAccounts. Direct Argo OIDC is selected and Dex remains absent. The issuer,
  `argocd` client ID, `argocd-admin`/`argocd-readonly` groups, and deny-default
  mapping are fixed by value-free policy. Exact private callback/origin, TLS,
  materialized value, workload/PVC, route, database recovery, and runtime remain
  blocked.
- Current source-only cloudflared evidence: the
  [candidate provenance record](runbooks/cloudflared-candidate-provenance.md) binds
  release, unsigned source, architecture-specific image, token-file, health, and
  edge-transport facts while leaving trust, hardening, secret-zero, external-resource
  state/recovery, component policy, route selection, and runtime blocked. It is not
  deployable source or a version selection.
- Current source-only Infisical evidence: the
  [candidate provenance record](runbooks/infisical-operator-candidate-provenance.md)
  records the incomplete observed `v0.11.8` public distribution and version-aligned
  `v0.11.7` set. The latter is selected only for offline source authoring and remains
  not deployable, with runtime **NOT RUN/BLOCKED**. The inert
  [privileged-prerequisites inventory](runbooks/infisical-operator-privileged-prerequisites-design.md)
  binds the seven raw CRD templates and known manager/metrics/user-RBAC seams to the
  vendored archive while approving no object or permission and keeping every
  promotion gate closed. It adds no CRD, RBAC, values, rendered object, or Ansible
  execution source. The actual target kubelet is now captured, but chart/CRD/API
  compatibility, trust, Namespace, scoped-RBAC, Argo handoff, secret-zero, traffic,
  recovery, and runtime gates remain blocked.
- Entry: pinned component versions, human-reviewed target kubelet-version evidence,
  verified Kubernetes compatibility, and an approved secret-zero procedure.
- Work sequence: a new bounded Ansible Namespace exception; selected Infisical Cloud
  Kubernetes Operator plus separate secret-zero and non-sensitive sync/rotation/
  revocation/recovery proof; Infisical-materialized precreated Argo Secrets; then the
  separately approved hardened Ansible Argo bootstrap and private one-time local
  break-glass readiness, only after every Stage 4 entry gate passes. Keycloak follows
  only after Stage 5 stateful recovery gates.
- Gate: Argo is private, reconciles a demo workload after explicit handoff, and secret
  values remain absent from Git/logs.
- Stop: admin endpoint becomes public or bootstrap credentials cannot be recovered.
- Rollback: uninstall only newly bootstrapped stateless controllers after evidence
  capture; preserve data and access.

### Stage 5 — isolation and shared data

- Entry: StorageClass, capacity, backup, and resource-limit decisions approved.
- Work: namespaces, service accounts, RBAC, NetworkPolicy, PostgreSQL, MongoDB,
  principals, environment-local Redis, and the stateful Keycloak prerequisites.
  Keycloak requires a selected immutable `linux/amd64` image, production startup, a
  dedicated logical database and owner role on the one general PostgreSQL instance,
  stable issuer/callback/TLS/proxy design, private administration/management, exact
  policies/probes/resources, and independently recoverable secret-zero. It remains a
  separate deployment and receives no separate PostgreSQL workload or PVC.
- Gate: before the first private Keycloak bootstrap, approve the image, shared-engine
  storage plus dedicated database/role, backup tooling/destination/key custody, restore procedure,
  provisional RPO/RTO, stable issuer, and private exposure. That separately approved
  bootstrap is non-authoritative and creates only controlled test identity state.
  Encrypted application-consistent `pg_dump`, non-destructive off-node copy, integrity
  check, isolated restore, and measured RPO/RTO must then pass before authoritative
  identity state is accepted or OIDC is enabled. Direct Argo OIDC additionally
  requires administrator/read-only positive cases, ungrouped and mutation denial,
  invalid/expired-token denial, logout, and local break-glass recovery before routine
  local authentication is disabled.
- Stop: cross-access succeeds, backup cannot restore, issuer/callback is unstable,
  administration becomes public, authorization fails closed incorrectly, or node
  pressure is unsafe.
- Rollback: restore verified data/config; never delete PVCs, re-import a realm, or
  downgrade Keycloak as routine rollback.

### Stage 6 — DEV

- Entry: shared-services gate passes.
- Work: deploy the minimum CristexHub DEV slice privately, measure capacity, then add
  the MVP's environment-local Reactive Resume and Browserless/gateway under the same
  private, digest-pinned, resource-bounded acceptance sequence.
- Gate: authentication, API, workers, migrations, resource headroom, and rollback to
  a prior digest pass during soak.
- Stop: migration ambiguity, excessive pressure, or any public DEV route.
- Rollback: Git revert to verified digest/config and restore data if required.

### Stage 7 — backup and recovery rehearsal

- Entry: stable DEV and declared RPO/RTO.
- Work: scheduled dumps, encryption, local retention, off-host copy, clean-host
  reconstruction steps, and restore rehearsal.
- Gate: recovery evidence proves secrets, desired state, mutable data, and access can
  be restored independently.
- Stop: backup exists only on the node or recovery depends on unavailable secrets.
- Rollback: disable the new schedule without removing retained backups.

### Stage 8 — private PROD

- Entry: DEV soak and recovery gates pass; explicit operator approval.
- Work: separate PROD credentials/data and the same verified image digest, reachable
  privately only.
- Gate: PROD isolation, auth, smoke, resource, backup, restore, and rollback pass.
- Stop: DEV can reach PROD or any PROD admin/data endpoint is public.
- Rollback: Git revert and verified data recovery procedure.

### Stage 9 — public PROD cutover

- Entry: private PROD accepted and external exposure review approved.
- Work: Cloudflare Tunnel route for the explicit PROD application hostname.
- Gate: external tests show PROD works while DEV/admin/data endpoints remain
  unreachable; direct WAN ports remain closed.
- Stop: unintended route, auth bypass, or direct-origin exposure.
- Rollback: remove/disable only the reviewed route and verify private PROD remains.

## Decision register

Implementation is blocked until each relevant item is resolved:

- Infisical Cloud bootstrap authentication, export/recovery, and machine-identity rotation;
- Argo CD private-repository bootstrap and recovery;
- OpenTofu host-local single-writer state encryption, Google Drive copy, key custody, integrity, and isolated recovery;
- cloudflared publisher/version trust, image assurance and off-node availability,
  hardening compatibility, fixed metrics surface, connector ownership, token-file
  secret-zero/recovery/rotation, and exact DNS/Traefik/edge policy;
- current k3s datastore, CNI indicators, NetworkPolicy objects and later enforcement
  probes, DNS, Traefik, StorageClass, and firewall;
- live PVC placement and approved use of the 1 TB disk;
- backup retention, encryption, Google Drive identity, RPO, and RTO;
- private GHCR pull authentication and image retention;
- selected Keycloak release/image/package, shared PostgreSQL storage plus dedicated
  Keycloak database/role/backup and isolated restore, stable private-first
  issuer/callback/TLS/proxy design, the `shared-services` Namespace, direct Argo OIDC
  groups/RBAC, and later separately
  approved browser-auth route;
- exact initial CristexHub service slice and code-runner disposition;
- private DEV naming: tailnet name or custom private DNS.

## Recovery order

The documentation-only
[`replacement-host-recovery` runbook](runbooks/replacement-host-recovery.md) first
requires truthful reboot-versus-replacement classification, independently verified
old-host fencing/storage exclusivity, and an approved preserve-existing-identity or
create-new-cluster decision. These split-brain gates precede every item below. The
current artifact register marks datastore, exact version, token custody, storage,
RPO/RTO, and off-node prerequisites `UNKNOWN — STOP`; therefore this order is a
target sequence, not an executable or proven procedure.

After those gates and a separately approved concrete plan, a replacement host is
recovered in this order:

1. restore documented host access and prerequisites;
2. install the pinned k3s version/configuration;
3. restore or reconstruct external state safely;
4. bootstrap the Infisical Cloud Kubernetes Operator and independently recover its
   access;
5. materialize precreated Argo Secrets and bootstrap Argo CD private access through
   the bounded Ansible path;
6. restore GHCR/Cloudflare access references;
7. restore Keycloak PostgreSQL and identity recovery material before activating OIDC;
8. reconcile namespaces, policies, and stateful services object by object without
   dual Ansible/Argo ownership;
9. restore application databases and encryption keys;
10. reconcile DEV/PROD workloads by immutable digest;
11. validate privately;
12. re-enable only separately approved public routes after acceptance.

Git and Argo reconstruct desired state. They do not restore mutable data, secret
values, or external state by themselves.

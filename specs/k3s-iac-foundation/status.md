# Status — k3s-iac-foundation (G1)

state: agent:in-progress
phase: implementing
build: guarded Infisical and 32-object private Argo CD source closures pass offline contracts, syntax, production lint, fixtures, hashes/render/docs/diff; both runtimes remain blocked/unrun
date: 2026-08-10
deploy_required_after_acceptance: yes

note: |
  Operational implementation is limited to read-only Ansible discovery, the
  executed two-package dependency bootstrap, executed group-scoped k3s administrator
  access, executed user-scoped kubectl client defaults, and the executed one-reboot
  recovery verifier. Python is limited to offline tests plus five reviewed
  exact-scope Ansible action plugins (four mutation guards and one no-log Argo Secret
  cryptographic validator); no general operational Python
  or collector exists. One
  explicitly approved SSH ping and
  non-elevated one-host check/diff run passed and generated the ignored mode-0600
  host-only report. The approved bootstrap directly requested only
  `python3-kubernetes` and `python3-jsonpatch`; apt installed 37 packages including
  dependencies, and package/import verification passes.
  Guarded deployable source now also exists for the exact private Argo CD core: three
  Ansible-owned CRDs and 29 namespaced objects, no ApplicationSet runtime, Secret,
  cluster RBAC, or public exposure. The wrapper fails closed until three exact,
  cryptographically valid Infisical-owned Secret contracts exist and
  `argocd-initial-admin-secret` is absent. Offline defaults reach the intentional host
  prerequisite; empty-API check defers only the unresolved default-project GVK, and
  apply waits for all three CRDs to become Established before runtime objects.
  No live Argo check/apply/idempotence, workload, login, TLS, traffic, recovery, or
  Git reconciliation evidence exists.
  The reviewed elevated report confirms the datastore and all nine exact Kubernetes
  queries as available. The approved admin-access check and mutation both passed,
  and the kubeconfig is root:k3s-admin mode 0640. A genuinely fresh session includes
  k3s-admin, `kubectl get nodes` reports the single Ready control-plane node, Ansible
  verifies readability while running as the selected account, and the second run is
  idempotent at ok=28/changed=0/failed=0. The initial all-namespace listing succeeded
  but the k3s multicall client emitted root-only server-config warnings. The approved
  user-scoped client-defaults check and execution passed; a fresh session inherits
  the expected client-only defaults, node/all-namespace queries emit no warning, and
  the second run reports changed=0/failed=0. The reboot check predicted exactly one
  reboot at ok=19/changed=1/unreachable=0/failed=0/skipped=7; execution returned with a new boot ID at
  ok=26/changed=1/unreachable=0/failed=0/skipped=0. The operator manually confirmed
  fallback access, both services active, and warning-free node/all-namespace queries.
  Read-only discovery is now extended offline with curated device/partition size,
  mounted-filesystem-type, and direct mount-state indicators; exact StorageClass
  behavior fields; bounded PV metadata; PVC metadata from five fixed namespaces;
  and a schema-v3 exact Node branch limited to curated name, cluster scope, and
  `status.nodeInfo.kubeletVersion`. The projection emits no raw `nodeInfo`, other
  Node status, device serial, generated PV identifier, address, backing path,
  filesystem content, Secret, ConfigMap, new API kind, or broad PVC result. The
  approved extended check/diff run passed at ok=17/changed=1/failed=0; the only write was the
  ignored mode-`0600` controller report. Human review confirmed an unmounted 1 TB
  rotational disk with one partition, NVMe/root capacity, local-path StorageClass
  behavior, and zero current PV/PVC objects. That historical live report's fifth PVC
  scope was `shared-data` and it did not capture a Kubernetes version. The separately
  approved schema-v3 elevated rerun generated the ignored report at
  `2026-08-07T08:09:31Z` and passed at ok=17/changed=1/unreachable=0/failed=0/skipped=1;
  the sole change was the controller-local report write and target discovery remained
  read-only. Human review confirmed kubelet `v1.36.2+k3s1`, four existing Namespaces,
  all 15 bounded Kubernetes queries available, and the exact `shared-services` PVC
  query available with count zero. At that discovery checkpoint, `argocd`,
  `platform-edge`, `shared-services`, `cristexhub-dev`, and `cristexhub-prod` were
  absent. After the historical first Namespace apply, `argocd` and `platform-edge`
  existed while `shared-services`, `cristexhub-dev`, and `cristexhub-prod` remained
  absent. The later separately approved foundation apply created `shared-services`;
  at that checkpoint `cristexhub-dev` and `cristexhub-prod` were still absent. The
  later DEV Namespace checkpoint documented below created `cristexhub-dev`, while
  `cristexhub-prod` remains absent. The first attempt omitted
  `-i .ansible/inventory.local.yml`, stopped at ok=3/changed=0/unreachable=1 before
  discovery, and made no host or report change; every operational command now
  explicitly loads the ignored local inventory. The
  source-only
  [Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
  binds chart `10.3.0`, application `v3.5.0`, captured signature/hash-binding,
  immutable linux/amd64 images, and curated online/static readiness evidence. It
  retains historical candidate evidence. The release record selects chart `10.3.0`
  / app `v3.5.0`, and the separate
  [guarded Argo CD bootstrap](../../runbooks/argocd-hardened-design.md) now promotes
  an exact 32-object committed-manifest closure. It contains three Ansible-owned CRDs
  and 29 namespaced objects, including a deny-all default AppProject, for the private controller/repo-server/server/standalone-
  Redis core. ApplicationSet runtime, Dex, notifications, commit server, cluster
  RBAC, public exposure, PVCs, hooks, metrics Services, Application/ApplicationSet,
  and Secret objects are absent. Exact precreated Infisical-owned Secret metadata and
  cryptographic values are a fail-closed prerequisite. Offline render/hash/security/
  policy/RBAC/wrapper/action/
  syntax/lint contracts pass. Argo runtime remains **NOT RUN/BLOCKED** pending Secret
  materialization and recovery, reviewed check/apply/idempotence, node pulls,
  readiness, TLS/login, private traffic positives/negatives, and Git reconciliation.
  Ansible is lifecycle owner of the three CRDs and bootstrap owner of namespaced
  objects until an explicit evidence-backed handoff. Exact present-only
  [foundation Namespace source and guarded wrapper](../../runbooks/foundation-namespace-bootstrap.md)
  now exist for `shared-services`. The first non-interactive check attempt stopped
  before service preflight/reconciliation for missing sudo
  (`ok=10 changed=0 unreachable=0 failed=1 skipped=0`). The interactive retry passed
  at `ok=20 changed=1 unreachable=0 failed=0 skipped=2`; exact source closure proves
  the single changed prediction was the one `shared-services` Namespace. Check mode
  made no mutation. The separately approved first apply then passed at
  `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created exactly that Namespace,
  verified exact identity/labels/`Active`, and preserved k3s/Tailscale health.
  The separately approved idempotence apply passed at
  `ok=22 changed=0 unreachable=0 failed=0 skipped=0`; exact identity/labels/`Active`
  and k3s/Tailscale health remained valid. The Namespace checkpoint is complete. A
  dedicated exact present-only
  [CristexHub DEV Namespace bootstrap](../../runbooks/cristexhub-dev-namespace-bootstrap.md)
  now contains only `cristexhub-dev` with the four approved labels and a distinct
  guarded wrapper/action; the action reads controller CLI task-selection context and
  rejects argument drift before the Kubernetes module. Its separately approved check
  passed at `ok=20 changed=1 unreachable=0 failed=0 skipped=2`, predicting only the
  exact Namespace without mutation. Its first apply passed at
  `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created/verified all four labels
  and `Active`, and preserved k3s/Tailscale health. Idempotence passed at
  `ok=22 changed=0 unreachable=0 failed=0 skipped=0`; exact post-state/service health
  remained valid and the Namespace checkpoint is complete. No policy/workload/Secret/
  PVC/route exists, and `cristexhub-prod` remains absent. The superseded
  `platform-secrets`/`platform-identity` source never ran, and this offline correction
  performs no live rename or deletion. Component source/credentials,
  resource/GVR/discovery inventory, Infisical Universal Auth recovery, live
  Namespace-adoption apply mode, and activation of the selected Keycloak/Argo OIDC
  policy remain five open architecture decisions; foundation Namespace runtime is
  completed evidence. The completed historical Namespace exception stays closed. The source-only
  [Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md)
  selects one future self-hosted Keycloak shared by CristexHub, Reactive Resume, and
  Argo CD as the identity architecture target only. It distinguishes Keycloak
  authentication/groups, Argo RBAC, and Kubernetes RBAC; retains direct OIDC with
  Dex absent, local break-glass, private administration, Infisical-owned client
  secrets, and a dedicated logical Keycloak database/owner role on the one general
  PostgreSQL instance in `shared-services`. Keycloak remains a separate deployment;
  it receives no separate PostgreSQL workload/PVC. Encrypted off-node backup,
  isolated restore, negative cross-database tests, and object-by-object handoff
  remain required. The release record selects Keycloak `26.7.1`, PostgreSQL
  `17.10`, realm `cristexhub`, stable issuer, and default theme only for offline
  source authoring; exact callbacks, trust/recovery, executable source, routes,
  credentials, and runtime remain **NOT RUN/BLOCKED**. The separate value-free
  [shared database architecture](../../runbooks/shared-database-architecture.md)
  freezes exactly one PostgreSQL and one MongoDB engine in `shared-services`.
  CristexHub DEV/PROD have isolated scopes on both engines; Reactive Resume DEV/PROD
  and Keycloak have dedicated PostgreSQL scopes. Authorization is deny-first,
  Infisical owns credential values, exposure is private-only, and all promotion gates
  remain closed. It adds no
  database image beyond the existing PostgreSQL baseline, no executable object, and
  no runtime claim. The approved database source profile fixes NVMe `local-path`,
  40/80 GiB PVCs, per-engine 500m/1 GiB requests and 2 CPU/3 GiB limits, private
  standard Services, mandatory TLS, Ansible-bootstrap→Argo-handoff direction, daily
  archives, 14-day retention, RPO 24h, and RTO 4h. MongoDB source/topology, exact
  paths/reclaim/probes/connection limits, implementation, backup/restore proof, and
  all runtime approvals remain unselected or blocked. The separate value-free
  [shared RabbitMQ architecture](../../runbooks/shared-rabbitmq-architecture.md)
  fixes one future engine in `shared-services`, exact isolated DEV/PROD vhost/user/
  permission/limit/recovery scopes, deny-first future consumer admission, and private
  management. The [shared backup architecture](../../runbooks/shared-stateful-backup-architecture.md)
  requires private authenticated metadata/list/retrieve/verify access, encrypted
  timestamped non-destructive off-node copies, integrity and isolated restore, and
  distinguishes RabbitMQ definitions from queued-message recovery. RabbitMQ image,
  topology, storage, Service/ports, limits, backup image/identities/staging path,
  schedule implementation, retention/RPO/RTO proof, restore, and all runtime gates
  remain unselected or blocked.
  The value-free
  [Reactive Resume hosted architecture](../../runbooks/reactive-resume-hosted-architecture.md)
  includes private DEV in the MVP with separate future PROD, OIDC clients, and
  dedicated shared-PostgreSQL consumer scopes. Upstream image selection, callbacks,
  resources, Secrets, recovery, handoff, and runtime remain blocked. One SHA-pinned,
  read-only GitHub-hosted CI workflow now exists and the application publisher is
  disabled. Commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1` was pushed to
  `develop`; GitHub Actions run `31311995461` completed successfully with the sole
  `validate` job successful. No image was built or published. The separate source-only
  [cloudflared candidate provenance record](../../runbooks/cloudflared-candidate-provenance.md)
  binds official release `2026.7.3`, its unsigned tag/commit, immutable linux/amd64
  image, token-file, health, and edge-transport evidence. It is **CANDIDATE — NOT
  DEPLOYABLE — NOT SELECTED**, runtime is **NOT RUN**, and adds no OpenTofu resource,
  Kubernetes object, secret, route, or deployment source. Publisher trust, image
  assurance/off-node availability, container hardening, Infisical token recovery,
  OpenTofu state/resource gates, Argo handoff, exact DNS/Traefik/edge policy and
  negative tests, route approval, single-node risk, soak, and runtime approvals
  remain blockers. The source-only
  [Infisical Operator candidate provenance record](../../runbooks/infisical-operator-candidate-provenance.md)
  distinguishes latest source release `v0.11.8`, whose matching public chart archive
  and image tag were not observed during the bounded capture, from the version-aligned
  `v0.11.7` chart/source/image set. The release and inert
  [privileged-prerequisites inventory](../../runbooks/infisical-operator-privileged-prerequisites-design.md)
  remain historical evidence. The
  [implementation profile](../../runbooks/infisical-operator-implementation-profile.md)
  binds the official controller source and selected three-Namespace, Universal Auth,
  metrics-off, no-ClusterGenerator, proxy, recovery, and ConfigMap-proof profile.
  The quarantined source archive remains forbidden as an operational input.
  The separate guarded
  [bootstrap closure](../../runbooks/infisical-operator-bootstrap.md) now contains six
  hash-mapped namespaced CRDs, six fail-closed admission policies and bindings,
  exact three-Namespace RBAC, one metrics-off digest-pinned controller, authenticated
  TLS Squid, eight NetworkPolicies, and a 40-object action guard. No Secret or
  Infisical CR is committed. The first local secret-zero run generated private
  recovery material and reached Google Drive OAuth, then stopped before Ansible/
  Kubernetes on `invalid_grant`. The discovered plaintext temp residue and unused
  encrypted artifact were removed without reading values. The corrected writer now
  cleans plaintext on every exit, retains/resumes one encrypted pending bundle,
  verifies the retrieved checksum/decrypt and TLS/key/auth relationships, stores the
  separate age identity in both a private file and login Keychain, and refuses
  implicit rotation. An unused age identity exposed during local debug tracing was
  revoked/regenerated before upload or Kubernetes, and the trace was removed. A
  hardened retry proved zero plaintext-temp residue, retained one encrypted pending
  bundle/checksum and Keychain copy, and zero Kubernetes Secrets, then stopped on the
  same expired Drive OAuth. Runtime remains unrun pending Drive reauthorization,
  exact proxy Secret recovery/write, check/apply/idempotence, and live admission/
  RBAC/traffic proof.
  The unmounted filesystem, disk health, contents, reuse decision, and off-node backup
  design remain unresolved; no disk mutation occurred.
  A bounded CNI/NetworkPolicy functional probe is implemented offline with separate
  plan, run, and cleanup paths. It uses an existing namespace, API-generated names,
  two fixed ownership labels, private exact-UID ledger recovery, fixed-kind
  interruption rediscovery, selectorless Service plus explicit EndpointSlice, UID
  delete preconditions, non-cascading `Orphan` propagation,
  `always` cleanup, and zero-residue assertions; it has no remote exec
  and never creates or deletes a Namespace. The approved live run used independently
  verified official BusyBox 1.37.0 linux/amd64 manifest
  `sha256:7a3ebe5bfd1a4a19797d20b0c0bb39d44393e9a03fd852c0865b0f540d868df0`.
  Run check passed at ok=18/changed=0/failed=0; all eight functional phases passed;
  execution completed at ok=225/changed=43/failed=0; exact cleanup removed 12 live
  identities after both policies were already UID-deleted. A separate cleanup check
  passed at ok=20/changed=0 with exact_identity_count=0. No Namespace or public
  exposure was created.
  The first replacement-host recovery increment is documentation-only. Its
  secret-free runbook/register truthfully separates the verified same-host reboot
  from replacement, requires independently verified old-host fencing and storage
  exclusivity, stops on split-brain risk, and requires exactly one approved
  preserve-existing-identity or create-new-cluster model. Datastore type, exact k3s
  version/config, token custody, storage mapping, RPO/RTO, off-node artifacts, and
  isolated restore remain `UNKNOWN — STOP`; no recovery command or automation was
  guessed. Replacement execution and later platform work therefore remain pending.
  The checksum-pinned OpenTofu 1.12.5 installer, protected host-local directory
  contract, and exact Cloudflare provider 5.23.0 zero-resource scaffold are
  implemented. The original check passed at ok=27/changed=6/failed=0. The first live
  attempt stopped at ok=21/changed=2/failed=1 when remote `get_url` reported
  `[Errno 113] No route to host`; only exact parent directories and the empty
  operator-owned state directory were created. The reviewed controller-transfer
  check then passed at ok=33/changed=6/failed=0, live recovery installed and verified
  the pinned CLI at ok=39/changed=6/failed=0, and the second run converged at
  ok=30/changed=0/failed=0. k3s and Tailscale remained running. The state directory
  remains empty; provider initialization/lockfile, state creation/encryption, Google
  Drive copy and restore, plan, apply, and every external resource remain NOT
  RUN/BLOCKED.
  Global committed Kubernetes source now defines exactly four Namespace manifests:
  `argocd`, `platform-edge`, `shared-services`, and source-only `cristexhub-dev`.
  The closed historical bounded Ansible bootstrap defines and loads only `argocd`
  and `platform-edge`, requires state present and
  exact bootstrap/future-owner labels, refuses forged internal results and foreign
  existing Namespaces, and has no delete path. Its non-passthrough wrapper rejects
  task-skipping controls, launches the repository `.venv` controller in an allowlisted
  clean environment, and creates a private random single-run attestation. The mutating
  task independently requires that attestation, reloads only the two literal manifest
  paths, and rejects extra top-level or metadata keys. The labels identify Ansible as
  bootstrap writer and Argo CD only as future desired owner. Argo ownership remains
  pending installation, Namespace adoption or Application registration, and
  successful sync evidence; the label alone is not a handoff. The separately approved
  wrapper check passed at `ok=19 changed=1 unreachable=0 failed=0 skipped=2` after all
  protected preflight assertions. The manifest contract displayed exactly `argocd`
  and `platform-edge` with the reviewed three labels, and the single loop task
  predicted `changed` for both items. Check mode created nothing and skipped live
  post-state verification by design. The separately approved first wrapper apply
  passed at `ok=21 changed=1 unreachable=0 failed=0 skipped=0`; the single changed
  loop task changed exactly `argocd` and `platform-edge`. Protected post-state
  queries and assertions verified both exact identities, all three reviewed labels,
  `Active` phase, and k3s/Tailscale service health. No other kind was authorized or
  changed. During the separately approved idempotence checkpoint, an initial
  invocation stopped before service preflight and Kubernetes reconciliation because
  local sudo authentication failed; it reported
  `ok=10 changed=0 unreachable=0 failed=1 skipped=0`, made no mutation, and did not
  prove idempotence. The retry passed at
  `ok=21 changed=0 unreachable=0 failed=0 skipped=0`; both exact reconciliation items
  were `ok`, protected identity/label/`Active` assertions passed, and k3s/Tailscale
  remained running before and after. Argo CD, cloudflared, Infisical Operator,
  Keycloak, PostgreSQL, MongoDB, `shared-services`, DEV/PROD, Secrets, workloads,
  Services, policies, PVCs, and routes do not exist from that historical increment. Exact present-only
  source now targets only `shared-services`. Its wrapper check and separately
  approved first apply/idempotence passed, so exact Namespace runtime existence and
  convergence at `changed=0` are claimed. The two superseded Namespace source files were
  never applied by their wrapper. `platform-edge` is reserved for cloudflared;
  Infisical Operator, separate Keycloak, one general PostgreSQL engine, and one
  shared MongoDB engine belong in `shared-services`.
  No external infrastructure resource, Kubernetes Secret/data, image publication,
  or component deployment operation was completed. In addition to historical public
  source/Actions reads, the recorded proxy secret-zero attempt generated local
  private material and made one failed Google Drive OAuth refresh request; it stopped
  before upload or Kubernetes mutation and its plaintext residue was removed. The hosted runner validated repository
  source only. Object listings and source/hosted CI do not prove replacement
  recovery.

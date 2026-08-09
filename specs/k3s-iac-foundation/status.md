# Status — k3s-iac-foundation (G1)

state: agent:in-progress
phase: implementing
build: shared-services check/first apply/idempotence complete; final ok=22 changed=0 failed=0 with exact labels/Active and k3s/Tailscale verified; current evidence/source contracts pass 153 full tests
date: 2026-08-09
deploy_required_after_acceptance: yes

note: |
  Operational implementation is limited to read-only Ansible discovery, the
  executed two-package dependency bootstrap, executed group-scoped k3s administrator
  access, executed user-scoped kubectl client defaults, and the executed one-reboot
  recovery verifier; Python is limited to offline contract tests. One
  explicitly approved SSH ping and
  non-elevated one-host check/diff run passed and generated the ignored mode-0600
  host-only report. The approved bootstrap directly requested only
  `python3-kubernetes` and `python3-jsonpatch`; apt installed 37 packages including
  dependencies, and package/import verification passes.
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
  `cristexhub-dev` and `cristexhub-prod` remain absent. The first attempt omitted
  `-i .ansible/inventory.local.yml`, stopped at ok=3/changed=0/unreachable=1 before
  discovery, and made no host or report change; every operational command now
  explicitly loads the ignored local inventory. The
  source-only
  [Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
  binds chart `10.3.0`, application `v3.5.0`, captured signature/hash-binding,
  immutable linux/amd64 images, and curated online/static readiness evidence. It is
  retains historical candidate evidence. The release record selects chart `10.3.0`
  / app `v3.5.0` only for offline source authoring; it remains **NOT DEPLOYABLE**,
  adds no values/Kubernetes source, and has no live API or Argo runtime evidence. The exact 44-document render
  reproduced at Kubernetes capability `1.36.2`, stable upstream API registration
  screened successfully, and controller-side image closure was reachable. Exact k3s
  admission/runtime and node pullability remain unproven. Signing/index-to-child and
  Redis trust, vulnerability policy, wildcard/broad RBAC,
  ingress-only/unrestricted-egress policy, generated/internal Secret recovery,
  private Git secret-zero, Namespace adoption, trust/soak acceptance, and runtime
  approvals remain blockers. The separate
  [source-only Argo CD hardened design](../../runbooks/argocd-hardened-design.md)
  accepts ClusterIP/loopback-only private administration, retained quiescent
  ApplicationSet, supplemental default-deny with an explicit broad ports-only
  `443`/`6443` weakness, phased least privilege, one-repository read-only GitHub App
  credentials, value-free Infisical custody, disabled Redis initialization, and two
  adoption Applications. It remains design-only: chart `10.3.0` and application
  `v3.5.0` are selected only for offline source authoring, runtime remains **NOT
  RUN/BLOCKED**, and no values, policy, RBAC, AppProject, Secret, Application, or
  route source was added. Ansible is selected as the future bounded bootstrap
  installer and lifecycle owner of privileged CRDs/cluster RBAC. Exact present-only
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
  and k3s/Tailscale health remained valid. The Namespace checkpoint is complete. The superseded
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
  `v0.11.7` chart/source/image set. The release record selects `v0.11.7` only for
  offline source authoring and Universal Auth as direction; it remains **NOT
  DEPLOYABLE**, runtime is **NOT RUN/BLOCKED**, and no CRD, Kubernetes object,
  credential, or Secret source was added. The inert
  [privileged-prerequisites inventory](../../runbooks/infisical-operator-privileged-prerequisites-design.md)
  binds the seven raw CRD templates, ownership boundaries, and known
  manager/metrics/user-RBAC defects to the vendored archive while approving no
  object or permission and keeping all promotion gates closed. The actual target is
  now captured, but chart/CRD/API compatibility, signer/build trust,
  `shared-services` placement with separate ServiceAccount/scoped RBAC, Argo handoff,
  secret-zero/recovery, traffic policy,
  single-node acceptance, and runtime approvals remain blockers.
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
  Global committed Kubernetes source now defines exactly three Namespace manifests:
  `argocd`, `platform-edge`, and `shared-services`.
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
  No external-resource, secret, data, image-publication, or deployment operation was
  performed. Network access in this increment was bounded to public action-tag
  resolution, the approved Git push, and read-only public GitHub Actions API
  observation of exact run `31311995461`. The hosted runner validated repository
  source only. Object listings and source/hosted CI do not prove replacement
  recovery.

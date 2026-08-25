# Tasks — k3s IaC foundation

## Documentation foundation

- [x] Document infrastructure-specific ownership and safety rules (`KIF-001`–`KIF-006`).
- [x] Document the target architecture, accepted shared-services trade-off, stages,
  stop conditions, and rollback (`KIF-009`–`KIF-030`).
- [x] Define the requirements, test contract, manual QA, and truthful backlog status
  without adding executable IaC (`KIF-030`).
- [x] Add the protective root `.gitignore` while keeping `.terraform.lock.hcl`
  trackable (`KIF-006`).
- [x] Record the documentation-only validation in this milestone's testcases
  (`KIF-004`, `KIF-030`).

## Stage 1 — read-only discovery

- [x] Replace the operational Python command allowlist with minimal Ansible-first
  discovery using built-in fact/stat modules and exact
  `kubernetes.core.k8s_info` queries (`KIF-001`, `KIF-004`, `KIF-008`).
- [x] Enforce check/diff, explicit one-host limit, default non-elevation, dual
  elevated-approval flags, no-log raw results, memory-only facts, curated local JSON
  output, mode `0600`, and symlink refusal (`KIF-001`, `KIF-006`, `KIF-030`).
- [x] Add standard-library offline contract tests; keep Python out of operational
  automation (`KIF-001`, `KIF-030`).
- [x] Create the locked project-local `uv` controller environment and local Galaxy
  collection path; syntax and production-profile lint pass without inventory-host
  access (`KIF-006`, `KIF-007`).
- [x] Obtain explicit approval for one non-elevated SSH inventory run; verify
  Ansible ping and one-host check/diff, then human-review the ignored host-only
  report (`KIF-001`, `KIF-007`).
- [x] Obtain separate explicit approval and attempt read-only elevated k3s
  inventory; confirm datastore access and record nine unavailable Kubernetes
  queries without exposing raw errors (`KIF-001`, `KIF-008`).
- [x] Diagnose the unavailable queries with one bounded read-only import probe;
  confirm `kubernetes`, `yaml`, and `jsonpatch` are absent (`KIF-008`, `KIF-030`).
- [x] Obtain explicit approval and implement a two-package Ansible bootstrap for
  `python3-kubernetes` and the non-transitive `python3-jsonpatch` requirement;
  syntax, lint, and offline safety tests pass (`KIF-002`, `KIF-007`).
- [x] Run the revised dependency bootstrap in check/diff mode; review 37 new, zero
  upgraded/removed packages; install the approved dependencies and verify package
  plus import availability (`KIF-002`, `KIF-007`).
- [x] Rerun elevated Ansible discovery against exactly one approved host and
  human-review its curated host, datastore, NetworkPolicy-object, platform-object,
  StorageClass, and resource indicator report (`KIF-008`).
- [x] Extend read-only discovery offline with curated block-device, partition,
  mounted-filesystem-type, and direct mount-state indicators; exact StorageClass
  behavior fields; bounded PV metadata; and PVC metadata from five fixed namespaces,
  without device serials, generated PV identifiers, addresses, backing paths,
  filesystem contents, sensitive
  Kubernetes kinds, or broad PVC queries (`KIF-001`, `KIF-003`, `KIF-008`, `KIF-030`).
- [x] Separately approve and run the extended one-host elevated discovery, then
  human-review the mode-`0600` storage projection: unmounted 1 TB rotational disk,
  NVMe capacity, local-path behavior, and zero current PV/PVC objects confirmed;
  unmounted filesystem/content/health remain unknown (`KIF-001`, `KIF-008`, `KIF-030`).
- [x] Bump the curated report to schema v3 and offline-validate an exact Node branch
  that emits only name, cluster scope, and `status.nodeInfo.kubeletVersion`, while
  retaining the current `shared-services` PVC scope and adding no query kind
  (`KIF-001`, `KIF-008`, `KIF-030`).
- [x] Separately approve and run one schema-v3 elevated read-only discovery; human
  review confirmed kubelet `v1.36.2+k3s1`, all 15 bounded queries available, and the
  exact `shared-services` PVC query with count zero. Correct the initially omitted
  local inventory argument and require it in every operational discovery command
  (`KIF-001`, `KIF-002`, `KIF-008`, `KIF-030`).
- [x] Add and offline-validate the source-only check-only k3s datastore/encryption
  preflight: canonical non-passthrough wrapper and attestation, exact
  one-host/check/diff/elevation gates, fixed read-only argv under `no_log`, bounded
  private config slurp and official encryption JSON projection, strict duplicate,
  type, mapping, malformed-content, and hashmatch fail-closed parsers, deterministic
  mode-`0600` controller artifact, raw-fact cleanup, and synthetic disclosure/parser
  fixtures. No host, backup, restore, encryption, cluster, or Secret mutation is
  authorized or run (`KIF-001`, `KIF-002`, `KIF-007`, `KIF-008`, `KIF-013`,
  `KIF-015`, `KIF-028`, `KIF-030`). Official K3s source pin is
  `v1.36.2+k3s1` / `01b6f04aaa69e8b09303f0393d4b4f1811da23aa`; a separately approved
  live read-only run passed `ok=45 changed=1 unreachable=0 failed=0` and retained
  sanitized unknown datastore/encryption/rotation evidence.
- [x] Implement and offline-validate CNI/NetworkPolicy `plan`, `run`, and `cleanup`
  actions with check/diff and one-host gates, a Ready linux/amd64 node, readable
  policy API, generated names, run labels, exact-UID cleanup, and no Namespace
  create/delete (`KIF-002`, `KIF-003`, `KIF-008`, `KIF-021`, `KIF-030`).
- [x] Close the offline ownership and cleanup design: persist a private mode-`0600`
  exact-identity ledger, dual-label fixed-kind interruption recovery, a selectorless
  Service plus explicit EndpointSlice, UID delete preconditions, `Orphan`
  propagation, `always` cleanup, and rejection of
  selector/Namespace deletion (`KIF-003`, `KIF-006`,
  `KIF-023`).
- [x] Independently verify the official BusyBox digest and linux/amd64
  `httpd`/`wget` capability, approve the ephemeral-QA ownership exception and
  separate create/delete gates, then pass baseline/deny/selective/rollback, exact
  cleanup, and an independent zero-residue check (`KIF-005`, `KIF-008`, `KIF-021`).
- [x] Confirm independent recovery access and the protected current configuration
  rollback baseline (`KIF-007`, `KIF-028`).
- [x] Implement and offline-validate the first replacement-host recovery increment:
  a truthful reboot boundary, secret-free runbook/register, old-host fencing and
  split-brain stop gates, and an explicit preserve-existing-identity versus
  create-new-cluster decision gate, with no guessed recovery automation (`KIF-002`,
  `KIF-003`, `KIF-013`, `KIF-028`, `KIF-030`).
- [ ] Resolve the register's `UNKNOWN — STOP` datastore, exact k3s version/config,
  token custody, storage mapping, RPO/RTO, off-node artifact, and isolated-restore
  prerequisites; approve exactly one identity model and only then review a concrete
  operational recovery plan (`KIF-002`, `KIF-015`, `KIF-026`–`KIF-030`).
- [ ] Resolve the remaining storage and replacement-recovery decisions; permit no
  mutation beyond the explicitly approved bounded Ansible changes (`KIF-002`,
  `KIF-003`).

Approval gate: operator approves the human-reviewed inventory and first general
host-baseline/next-stage mutation plan.

## Stage 2 — host safety baseline

- [x] Verify the protective ignore rules before adding the admin-access Ansible
  artifact (`KIF-006`).
- [x] Implement the bounded group-scoped k3s administrator access playbook: fixed
  dedicated group, existing nonzero-UID user, rejection of unexpected members,
  GID 0, and numeric aliases, root-owned kubeconfig mode `0640`, hidden config diff,
  root-only rollback baseline,
  conditional k3s restart, and post-run assertions (`KIF-004`, `KIF-005`, `KIF-007`).
- [x] Run syntax, production-profile lint, and offline contract tests for the
  admin-access playbook (`KIF-002`, `KIF-007`).
- [x] Obtain explicit approval for granting the selected user cluster-admin
  kubeconfig access and restarting k3s (`KIF-002`, `KIF-007`).
- [x] Run the admin-access playbook in check/diff mode and review the predicted
  rollback, group, membership, config, and restart changes (`KIF-002`, `KIF-007`).
- [x] Run the approved mutation and verify root/group `0640` kubeconfig metadata
  (`KIF-007`).
- [x] Verify effective kubeconfig readability through Ansible as the selected user,
  reconnect without a stale SSH multiplexed session, verify group membership, and
  run `kubectl get nodes` successfully (`KIF-007`).
- [x] Prove second-run Ansible idempotence with `changed=0` (`KIF-007`).
- [x] Verify `kubectl get all -A` through the persistent group-scoped access
  (`KIF-007`).
- [x] Implement and offline-validate approved user-scoped k3s kubectl client defaults
  without exposing the root-only server configuration or restarting k3s (`KIF-007`).
- [x] Run the client-defaults playbook in check/diff mode, execute the accepted plan,
  reconnect, prove warning-free node/all-namespace queries, and require second-run
  `changed=0` (`KIF-007`).
- [x] Implement and offline-validate the approved one-host reboot recovery playbook
  with pre/post service, boot-ID, Ready-node, rollback-baseline, and effective-user
  kubeconfig assertions (`KIF-007`).
- [x] Confirm independent console or LAN recovery access, run check/diff, review the
  single-reboot prediction, then execute and verify SSH/Tailscale/k3s recovery
  (`KIF-007`).

Stop gate: stop on access loss, unexpected network/package changes, or ambiguous
disk state. Restore preserved configuration before continuing.

## Stage 3 — external resources

- [x] Verify the root ignore policy and offline-implement the checksum-pinned
  OpenTofu CLI installer plus protected host-local state-directory contract
  (`KIF-006`, `KIF-028`).
- [x] Add the exact-version Cloudflare-only zero-resource scaffold; do not use
  Kubernetes, Helm, or GitHub providers (`KIF-005`, `KIF-013`).
- [x] Run the separately approved one-host CLI installation check/diff, recover the
  bounded host-egress failure through reviewed controller transfer, execute it, and
  prove idempotence without provider or state operations (`KIF-002`).
- [ ] Generate and review the provider lockfile through separately approved
  initialization, then run OpenTofu format/validate (`KIF-006`, `KIF-030`).
- [ ] Implement encrypted timestamped Google Drive state copies, independent key
  custody, integrity verification, and isolated restore before any apply
  (`KIF-013`, `KIF-028`).
- [x] Add the separate source-only GitHub-root state backup/readback/isolated-restore
  lane with fixed `github.tfstate`, dedicated archive/lock/systemd/wrapper/playbook
  closure, and no foundation timer/state path (`KIF-005`, `KIF-013`, `KIF-028`,
  `KIF-030`). No provider, host, Drive, Infisical, or state operation ran.
- [ ] Implement only explicitly approved external resources and review a sanitized
  plan with no destroy/replacement or public route (`KIF-002`, `KIF-005`, `KIF-013`).
- [ ] Obtain explicit approval for the first exact reviewed OpenTofu apply (`KIF-002`).
- [ ] Create no public application route in this stage (`KIF-010`, `KIF-011`).

Stop gate: stop on secret-bearing state/plan, replacement/destroy outside scope, or
missing state recovery. Reverse changes only through another reviewed plan.

## Pre-Stage-4 — bounded platform Namespace bootstrap exception

- [x] Commit exact `argocd` and `platform-edge` Namespace source plus the bounded
  `state: present`, no-delete Ansible bootstrap exception (`KIF-002`, `KIF-005`).
- [x] Obtain separate human approval for only
  `ansible/bin/bootstrap-platform-namespaces check` and inspect its complete result;
  it passed at `ok=19 changed=1 unreachable=0 failed=0 skipped=2`, predicted exactly
  `argocd` and `platform-edge`, and made no mutation (`KIF-002`, `KIF-005`).
- [x] After accepting the check result, obtain separate human approval for the first
  `ansible/bin/bootstrap-platform-namespaces apply`; it passed at
  `ok=21 changed=1 unreachable=0 failed=0 skipped=0` and reconciled exactly the two
  reviewed Namespaces (`KIF-002`, `KIF-005`).
- [x] Verify exact identity, labels, Active phase, and k3s/Tailscale service health
  after the first apply (`KIF-002`, `KIF-005`).
- [x] Obtain separate human approval for a second
  `ansible/bin/bootstrap-platform-namespaces apply` and require `changed=0`; the
  initial invocation stopped before service preflight and Kubernetes reconciliation
  on failed local sudo authentication at
  `ok=10 changed=0 unreachable=0 failed=1 skipped=0`, then the retry passed at
  `ok=21 changed=0 unreachable=0 failed=0 skipped=0` with exact post-state and service
  health verified (`KIF-002`, `KIF-005`).

Stop gate: foreign ownership, source drift, any unexpected object or change, failed
verification, or nonzero change would have stopped the second apply. Check mode,
first apply, and idempotence passed; the bounded exception is complete and closed.
These checklist entries authorize no further bootstrap run and waive no Stage 4
entry gate.

## Stage 4 — GitOps and secret bootstrap

- [x] Record public Argo CD chart, captured signature/hash-binding, image, and ignored
  minimal-render research in a source-only
  [candidate provenance record](../../runbooks/argocd-candidate-provenance.md),
  explicitly without version selection, chart/values/Kubernetes source, secret,
  runtime, or deployment (`KIF-005`, `KIF-013`, `KIF-023`, `KIF-030`).
- [x] Record the online/static Argo CD readiness refresh covering deterministic render,
  upstream API registration, RBAC/network posture, controller-side image closure,
  image trust/vulnerability limits, private Git, and Namespace adoption without live
  API contact, version selection, deployable source, Secret, or runtime (`KIF-005`,
  `KIF-008`, `KIF-010`, `KIF-013`, `KIF-015`, `KIF-021`, `KIF-023`, `KIF-030`).
- [x] Record the historical source-only Argo design checkpoint covering private
  access, a then-retained quiescent ApplicationSet, supplemental default-deny,
  phased RBAC/AppProjects, private Git, value-free secret custody, Namespace
  adoption, and stop/rollback. That superseded checkpoint added no deployable source,
  Secret, or cluster contact; the current
  [guarded Argo CD bootstrap](../../runbooks/argocd-hardened-design.md) removes the
  ApplicationSet runtime and implements the exact private source while preserving
  component-specific approvals (`KIF-002`, `KIF-003`, `KIF-005`,
  `KIF-008`, `KIF-010`, `KIF-013`–`KIF-015`, `KIF-021`, `KIF-030`).
- [x] Record the
  [source-only Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md):
  one future shared self-hosted identity architecture target, Ansible bootstrap,
  the then-proposed `platform-secrets`/`platform-identity` names, direct Argo OIDC with Dex
  absent, independent Keycloak/Argo/Kubernetes authorization layers, dedicated
  PostgreSQL and recovery gates, private administration, Infisical-owned client
  secrets, and object-by-object handoff. At that historical checkpoint it selected
  no release/image/package, database version, hostname, route, credential, manifest,
  or deployable source and authorized no runtime (`KIF-002`, `KIF-003`, `KIF-005`,
  `KIF-010`, `KIF-012`–`KIF-016`,
  `KIF-021`, `KIF-023`, `KIF-026`–`KIF-030`).
- [x] Record official cloudflared release/source/image, token-file,
  readiness/health, and edge-transport research in a source-only
  [candidate provenance record](../../runbooks/cloudflared-candidate-provenance.md),
  explicitly without trust/version selection, OpenTofu resource, Kubernetes source,
  secret, route, runtime, or deployment (`KIF-005`, `KIF-011`, `KIF-013`, `KIF-021`,
  `KIF-023`, `KIF-030`).
- [ ] Human-select and soak the cloudflared candidate only after publisher trust,
  image signature/SBOM/vulnerability/off-node availability, container hardening,
  Infisical token recovery/rotation, OpenTofu state and external-resource gates, Argo
  handoff, exact DNS/Traefik/edge policy and negative tests, route approval,
  single-node risk, and runtime approvals are resolved; add deployable source only in
  a separate reviewed change (`KIF-002`, `KIF-005`, `KIF-011`, `KIF-013`, `KIF-015`,
  `KIF-021`, `KIF-023`).
- [x] Select Argo CD chart `10.3.0` / app `v3.5.0` only as an offline source
  baseline; vendor the exact public chart/provenance/key inputs with SHA-256 closure
  while adding no values, rendered objects, controller source, Secret, or runtime
  approval (`KIF-005`, `KIF-013`, `KIF-023`, `KIF-030`).
- [ ] Accept Argo signer/index-to-child and Redis trust, vulnerability policy, soak,
  exact k3s admission/runtime, reduced RBAC/default-deny networking,
  generated/internal Secret recovery, private Git secret-zero, node image
  pullability, Namespace adoption, bootstrap closure, and runtime approvals before a
  separate reviewed deployable-source change (`KIF-002`, `KIF-005`, `KIF-013`,
  `KIF-015`, `KIF-021`, `KIF-023`).
- [x] Record the latest Infisical Operator `v0.11.8` public distribution gap and
  last observed version-aligned `v0.11.7` chart/source/image evidence in a
  source-only
  [candidate provenance record](../../runbooks/infisical-operator-candidate-provenance.md),
  explicitly without version/trust selection, chart/CRD/Kubernetes source, secret,
  runtime, or deployment (`KIF-005`, `KIF-013`–`KIF-015`, `KIF-021`, `KIF-023`,
  `KIF-030`).
- [x] Select Infisical Operator `v0.11.7` only as an offline source baseline;
  vendor exact public chart/provenance/key inputs with SHA-256 closure and select
  Universal Auth as a value-free direction without adding a CRD, RBAC object,
  controller source, credential, Secret, or runtime approval (`KIF-005`, `KIF-013`–
  `KIF-015`, `KIF-023`, `KIF-030`).
- [x] Inventory the seven hash-bound raw CRD templates, ownership boundaries, and
  manager/metrics/user-RBAC seams in an inert
  [promotion contract](../../runbooks/infisical-operator-privileged-prerequisites-design.md); at that checkpoint keep every trust,
  compatibility, scope, authentication, recovery, traffic, source-promotion, and
  runtime gate closed and add no valid Kubernetes or operational Ansible source
  (`KIF-005`, `KIF-013`–`KIF-015`, `KIF-021`, `KIF-023`, `KIF-030`).
- [x] Bind the official `v0.11.7` controller commit and record the confirmed
  [implementation profile](../../runbooks/infisical-operator-implementation-profile.md):
  exact `shared-services`/`argocd`/`cristexhub-dev`/`cristexhub-prod`/`platform-edge`
  source-only watch scopes with separate
  identity intent, all-six namespaced-controller startup behavior, no ClusterGenerator
  or review/token permissions, metrics off, authenticated Squid egress direction,
  age/Drive secret-zero recovery direction, and a non-sensitive ConfigMap proof.
  Quarantine the full source archive as evidence; promote no Kubernetes/operational
  Ansible source. Keep same-Namespace reference enforcement and runtime blocked.
- [x] Promote the exact guarded
  [Infisical idle closure](../../runbooks/infisical-operator-bootstrap.md): six
  namespaced CRDs with hash mapping, native same-Namespace admission, five manager
  Roles, metrics-off digest-pinned controller, authenticated TLS Squid, proxy-only
  NetworkPolicy, 44-object action guard, and dedicated check/apply wrapper. Commit no
  Secret value, Infisical CR, PROD value/workload, or self-hosted server (`KIF-005`,
  `KIF-013`–`KIF-016`, `KIF-021`, `KIF-023`, `KIF-030`).
- [x] Add the separate source-only
  [Infisical Argo CD Secret materialization seam](../../runbooks/infisical-argocd-secret-materialization.md): one same-Namespace
  Universal Auth credential reference, fixed project/environment/path identifiers,
  exact Connection/Auth/StaticSecret source closure, orphaned target templates,
  additive exact-name Secret/workload-list RBAC, fail-closed admission, and a
  non-passthrough check/apply wrapper. Runtime, credential/source creation, Secret
  values, sync, and live checks remain **NOT RUN/BLOCKED** (`KIF-INF-06`).
- [x] Add the separate source-only
  [Infisical database Secret materialization seam](../../runbooks/infisical-database-secret-materialization.md): exactly 15 value-free objects for one shared Connection, separate PostgreSQL/MongoDB Auth and Universal Auth identities, two StaticSecrets, eight namespace-scoped fail-closed VAP/bindings, and additive Secret-writer RBAC. Freeze eleven engine/per-consumer target Secret contracts, byte/canonical/identity hashes, and action-only/internal/task-selection negatives. Runtime, credential values, check/apply, sync, rotation, and recovery remain **NOT RUN/BLOCKED** (`KIF-INF-07`).
- [x] Expand and apply the guarded closure for `cristexhub-prod`: add the exact
  manager Role/RoleBinding, extend the controller watch list, admit PROD only for the
  exact reviewed Auth/Connection/StaticSecret identities while keeping Secret/
  PushSecret/DynamicSecret PROD-excluded, and refresh every hash/count guard. Check,
  apply, post-check, and idempotence passed at `ok=30 changed=1`, `ok=35 changed=1`,
  `ok=30 changed=0`, and `ok=35 changed=0`; no value, Secret, Infisical CR,
  application workload, provider resource, PVC, database, or route was created
  (`KIF-INF-04`).
- [ ] Complete broader live admission/RBAC/traffic negatives before Universal Auth.
  Guarded Drive transfer/readback, controller verification, and exact three proxy
  Secrets pass. Historical Operator results for exactly 40 objects were
  `ok=24 changed=2`, `ok=29 changed=2`, and `ok=29 changed=0`; the later 42-object
  source was not separately runtime-applied, while the 44-object expansion is now
  applied/idempotent. Credential-bearing phases remain blocked (`KIF-005`,
  `KIF-013`–`KIF-016`, `KIF-021`, `KIF-023`, `KIF-027`, `KIF-030`).
- [ ] Approve and document the private Git/Infisical/GHCR/Cloudflare/Keycloak
  secret-zero sequence (`KIF-014`, `KIF-015`).
- [x] Historical source checkpoint: implement an exact present-only/no-delete
  foundation bootstrap for `platform-secrets` and `platform-identity`. It never ran
  and was superseded before any cluster contact (`KIF-002`, `KIF-005`, `KIF-016`,
  `KIF-030`).
- [x] Correct the
  [foundation Namespace bootstrap](../../runbooks/foundation-namespace-bootstrap.md)
  to only `shared-services`, remove the two never-run source leaves, preserve the
  completed historical wrapper unchanged, and record this as source migration rather
  than live deletion (`KIF-002`, `KIF-005`, `KIF-016`, `KIF-030`).
- [x] Run `ansible/bin/bootstrap-foundation-namespaces check` and review a prediction
  limited to the one exact `shared-services` Namespace. After a non-interactive
  missing-sudo stop (`ok=10 changed=0 failed=1`), the interactive retry passed at
  `ok=20 changed=1 failed=0`; check mode made no mutation.
- [x] Run the separately approved first apply; it passed at
  `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created only
  `shared-services`, verified exact identity/labels/`Active`, and preserved
  k3s/Tailscale health.
- [x] Run the separately approved idempotence apply; it passed at
  `ok=22 changed=0 unreachable=0 failed=0 skipped=0` and reverified exact
  identity/labels/`Active` plus k3s/Tailscale health (`KIF-002`, `KIF-005`,
  `KIF-016`).
- [x] Implement component-specific exact guarded Ansible source closures for the
  Infisical Operator and hardened private Argo core. Argo promotes exactly three CRDs
  and 29 namespaced objects including a deny-all default AppProject, omits
  ApplicationSet runtime/public exposure/cluster RBAC/Secrets, and requires exact
  precreated, cryptographically valid Infisical-owned Secret contracts. Empty-API
  check and Established-CRD apply ordering are fail-closed; live
  check/apply/idempotence remain separately gated (`KIF-002`, `KIF-005`, `KIF-013`–`KIF-015`).
- [ ] Obtain explicit approval for bounded Argo CD bootstrap (`KIF-002`).
- [ ] Keep Argo CD private and prove Git reconciliation using a demo workload
  (`KIF-010`, `KIF-022`).
- [ ] Prove one non-sensitive Infisical sync, rotation, and revocation without value
  disclosure (`KIF-013`–`KIF-015`).
- [x] Add one SHA-pinned, read-only GitHub-hosted infrastructure CI workflow with
  exact branch/job/permission/tool/test closure and no package-write, Secret,
  registry, provider, host, cluster, or deploy path (`KIF-005`, `KIF-022`, `KIF-030`).
- [x] Push exact infrastructure commit `e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`
  and record successful source-only run `31311995461` separately from publication.
- [ ] Observe and review the private application CI run for exact commit
  `55d3ee403fb573f84d69a303430c1c15643827d7`; unauthenticated API access is denied.

The source-baseline selections satisfy version choice and public-input availability
only. They do not satisfy trust/soak, privileged-component-bootstrap,
private-Git/Infisical, reconciliation, Secret, or runtime tasks above. Foundation
Namespace runtime is complete evidence; the five exact controller-closure,
exact-resource-inventory, Universal-Auth-recovery, live-adoption-apply, and
selected-OIDC-activation decisions remain open. Installer and privileged lifecycle ownership are selected as Ansible,
but no future bootstrap run is approved.

Stop gate: stop if an admin surface becomes public, secret content appears in Git or
logs, or bootstrap cannot be recovered.

## Stage 5 — namespaces, policy, and shared data

- [x] Approve the database source profile: NVMe `local-path`, one `ReadWriteOnce` PVC
  per engine, PostgreSQL 40 GiB, MongoDB 80 GiB, per-engine 500m/1 GiB requests and
  2 CPU/3 GiB limits, private standard Services, and mandatory TLS.
- [ ] Select exact data paths, reclaim behavior, probes, connection limits, TLS
  identities, and any destructive disk preparation separately (`KIF-002`, `KIF-003`,
  `KIF-019`, `KIF-026`).
- [x] Add dedicated exact present-only
  [CristexHub DEV Namespace source](../../runbooks/cristexhub-dev-namespace-bootstrap.md)
  with the four approved labels, a distinct guarded wrapper/exact-scope mutation
  action, and no PROD/policy/workload/Secret/PVC/route source.
- [x] Run the separately approved `cristexhub-dev` check; it passed at
  `ok=20 changed=1 unreachable=0 failed=0 skipped=2`, predicting one exact Namespace
  change without mutation (`KIF-002`, `KIF-005`, `KIF-016`, `KIF-030`).
- [x] Run the first `cristexhub-dev` apply; it passed at
  `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created/verified only the exact
  Namespace, and preserved k3s/Tailscale health.
- [x] Run the separate idempotence apply for only `cristexhub-dev`; it passed at
  `ok=22 changed=0 unreachable=0 failed=0 skipped=0`, with exact post-state and
  k3s/Tailscale health preserved.
- [ ] Select exact DEV service accounts, RBAC, quota, limit, and default-deny/allow
  policy values before adding those object kinds (`KIF-016`, `KIF-019`, `KIF-021`).
- [x] Add the exact present-only, value-free CristexHub PROD Namespace source,
  guarded wrapper/action, literal manifest hash, canonical task-source/attestation/
  preflight gates, and offline action-only/injection negatives; do not run it
  (`KIF-002`, `KIF-005`, `KIF-006`, `KIF-010`, `KIF-016`, `KIF-030`).
- [x] Complete the separately approved present-only `cristexhub-prod` Namespace
  checkpoint; check/first apply/idempotence passed and the Namespace is Active and
  idempotent. Earlier source-only absence evidence remains historical.
- [ ] Keep all later `cristexhub-prod` resources absent until DEV validation, recovery,
  soak, identity recovery, and separate PROD resource approvals satisfy KIF-025.
- [x] Add the source-only, fail-closed CristexHub PROD runtime Infisical seam with
  independent Auth/Universal Auth names, exact `/cristexhub/prod/runtime` source,
  historical nine-key runtime plus GHCR-pull target and the blocked ten-key Browserless source update, PROD-scoped VAP/bindings, least-privilege
  RBAC, hashes, guarded wrapper/role/plugin, policy, runbook, and offline contracts;
  Namespace, identity values, sync, and runtime remain NOT RUN/BLOCKED (`KIF-005`,
  `KIF-013`–`KIF-016`, `KIF-021`, `KIF-025`, `KIF-030`).
- [x] Add the exact five-object source-only CristexHub PROD Argo registration pinned
  to protected-main revision `751885a42798d282e168131db147f13694a0a621`, with
  namespace-only no-delete RBAC, present-only guard, foreign-object refusal,
  `CreateNamespace=false`, `Prune=false`, manual sync, and an always-active deny
  window; do not run check/apply or any sync transition (`KIF-005`, `KIF-006`,
  `KIF-010`, `KIF-016`, `KIF-021`, `KIF-025`, `KIF-030`).
- [ ] Obtain explicit approval before creating stateful services (`KIF-002`).
- [x] Add a canonical value-free shared-database policy and runbook for exactly one
  PostgreSQL and one MongoDB engine in `shared-services`, dedicated consumer scopes,
  deny-first authorization, private-only exposure, Infisical value ownership, and
  closed promotion gates without adding executable objects (`KIF-005`, `KIF-013`,
  `KIF-016`–`KIF-019`, `KIF-021`, `KIF-026`–`KIF-030`).
- [x] Reconcile the Reactive Resume hosted policy/runbook with the live private DEV checkpoint:
  selected immutable DEV GHCR digests, the pinned revision's exact seven Argo manifests
  including default-deny, private Traefik route, materialized CA, runtime Secret
  `reactive-resume-dev-runtime`; current HEAD's additional
  `networkpolicy-allow-backend.yaml` remains source-only and is not claimed live,
  Argo-managed, or applied,
  successor database `reactive_resume_dev_successor`, and explicit remaining image-trust,
  OIDC/database/role, data-only recovery, TLS-renewal, soak, PROD, and public-route gates
  (`KIF-012`–`KIF-017`, `KIF-021`, `KIF-023`, `KIF-026`–`KIF-030`).
- [x] Add the source-only guarded logical provisioning lane for one general
  PostgreSQL instance and standalone MongoDB: exact five PostgreSQL and two MongoDB
  empty reservations, precreated Infisical consumer Secret contracts, no-secret-argv
  scripts, exact drift/idempotence checks, UID-bound temporary helpers with cleanup,
  and no database/user/PVC delete path (`KIF-017`, `KIF-026`, `KIF-030`).
- [ ] Maintain the live DEV successor PostgreSQL scope `reactive_resume_dev_successor`
  with separate NOINHERIT runtime/migrator roles; prove ACL/cross-database negatives
  and keep role/ACL/credential recovery separate from the logical data archive (`KIF-017`). The source lane's check/apply,
  idempotence, authorization, runtime, and recovery evidence remains NOT RUN/BLOCKED.
- [x] Select the MongoDB `8.0.28` linux/amd64 digest offline and add the
  intentionally standalone, non-authoritative source closure with private Service,
  retained `80Gi` PVC template, exact resources/probes, Infisical Secret references,
  and deny-first NetworkPolicy (`KIF-018`, `KIF-021`, `KIF-023`, `KIF-030`). The
  runtime, trust/recovery, separate database/user authorization, plaintext-negative,
  replica-set/transaction/HA, and authoritative-data gates remain open.
- [x] Add value-free source-only policies/runbooks for exactly one shared RabbitMQ
  in `shared-services`, dedicated DEV/PROD vhost/user/permission/limit/recovery
  scopes, reviewed exact future-consumer admission, and private management
  (`KIF-020`, `KIF-021`, `KIF-030`).
- [ ] Select RabbitMQ topology and exact immutable trusted source, storage, TLS,
  limits, NetworkPolicy, definitions restore, and message reconciliation proof before
  adding executable objects; Redis remains per environment (`KIF-020`, `KIF-023`).
- [x] Select Keycloak `26.7.1` and PostgreSQL `17.10` immutable linux/amd64
  children, realm `cristexhub`, stable issuer, default theme, exact client/group
  templates, deny-default Argo mapping, Namespace trust, and Universal Auth direction
  only for value-free offline source authoring (`KIF-005`, `KIF-010`, `KIF-013`–
  `KIF-015`, `KIF-023`, `KIF-030`).
- [ ] Accept Keycloak/PostgreSQL image trust and recovery; accept MongoDB image
  trust/recovery and the standalone-to-replica-set/authoritative-data decision;
  select the remaining Reactive Resume/Argo callbacks/origins, TLS identity/proxy
  policy, private administration, and Infisical-owned runtime material before any
  runtime (`KIF-010`, `KIF-013`–
  `KIF-015`, `KIF-021`, `KIF-023`). The source-only PostgreSQL and standalone
  MongoDB object closures are intentionally implemented before these runtime gates
  and do not waive them.
- [ ] Before the first private Keycloak bootstrap, approve the general PostgreSQL
  storage/failure domain, dedicated Keycloak database/owner role, database-scoped
  backup tooling/destination/key custody, restore procedure, provisional RPO/RTO,
  and a non-authoritative controlled test-state plan (`KIF-002`, `KIF-026`–
  `KIF-028`).
- [ ] Obtain separate Ansible check/apply/idempotence approvals for a private,
  non-authoritative Keycloak bootstrap; create only controlled test identity state,
  then prove `pg_dump`, encrypted off-node copy, integrity, isolated restore, and
  measured RPO/RTO before accepting authoritative identity state or enabling OIDC
  (`KIF-002`, `KIF-005`, `KIF-026`–`KIF-028`).
- [ ] Prove direct Argo OIDC administrator/read-only/ungrouped/invalid-token/logout/
  break-glass cases before disabling routine local authentication (`KIF-002`,
  `KIF-005`, `KIF-010`, `KIF-012`–`KIF-015`).
- [x] Add a value-free shared backup policy/runbook for private authenticated
  metadata catalog/list/retrieve/verify workflows, encrypted timestamped archives,
  non-destructive Google Drive/`rclone copy` direction, exact future archive
  admission, and separate RabbitMQ definitions/message recovery semantics.
- [x] Fix the backup source profile at daily archives, 14-day local/off-node
  retention, RPO 24h, RTO 4h, and independent encryption-key custody.
- [ ] Select the backup image/digest, Google Drive identity/folder, staging path,
  schedule implementation, retention enforcement, credential/key recovery, and prove
  RPO/RTO through isolated restore before accepting application or identity data
  (`KIF-026`–`KIF-028`).

Stop gate: stop on cross-access, public data exposure, failed restore, unsafe node
pressure, or inability to preserve encryption keys. Never delete PVCs as rollback.

## Stage 6 — private DEV

- [ ] Deploy the minimal CristexHub DEV slice by immutable digest (`KIF-023`,
  `KIF-024`).
- [ ] Validate OIDC/auth, API, worker, exactly-one Beat, migration, WebSocket, and
  private routing behavior (`KIF-010`, `KIF-021`, `KIF-025`).
- [ ] The private Reactive Resume DEV Argo checkpoint is complete; next prove the
  remaining full acceptance and soak gates for the selected immutable image and
  exact resource/network limits (`KIF-016`, `KIF-019`, `KIF-021`,
  `KIF-023`, `KIF-029`).
- [ ] Prove Git/digest rollback and complete the approved soak (`KIF-024`, `KIF-025`,
  `KIF-030`).

Stop gate: stop on public DEV exposure, migration ambiguity, unsafe resource
pressure, or rollback failure.

## Stage 7 — scheduled recovery

- [ ] Approve RPO, RTO, retention, encryption, Google Drive identity, and recovery
  custody (`KIF-015`, `KIF-026`–`KIF-028`).
- [ ] Implement non-destructive scheduled dumps and encrypted `rclone copy`
  (`KIF-026`).
- [ ] Rebuild in isolation and record restore timing/data/application validation
  (`KIF-027`, `KIF-028`, `KIF-030`).
- [ ] Add bounded backup/disk/node/tunnel/workload health signals (`KIF-029`).

Stop gate: stop if any required recovery artifact exists only on the node or a
restore needs unavailable credentials.

## Stage 8 — private PROD

- [ ] Obtain explicit approval for the PROD namespace after DEV soak/recovery passes
  (`KIF-002`, `KIF-025`).
- [ ] Create separate PROD identities, databases, credentials, keys, backup paths,
  and policies (`KIF-014`–`KIF-021`).
- [ ] Promote the same verified digest and validate PROD privately (`KIF-024`,
  `KIF-025`).
- [ ] Prove PROD isolation, backup, restore, and rollback (`KIF-017`–`KIF-030`).

Stop gate: stop if DEV can reach PROD, any admin/data surface is public, or recovery
and rollback evidence is incomplete.

## Stage 9 — public identity and PROD

- [ ] Review the stable Keycloak issuer hostname, exact browser-authentication paths,
  tunnel destination, positive login, negative administration/management and
  direct-origin reachability, and rollback (`KIF-011`, `KIF-012`).
- [ ] Obtain separate explicit approval before publishing only that reviewed
  Keycloak browser-authentication route; keep all identity administration and
  management private (`KIF-002`, `KIF-011`, `KIF-012`).
- [ ] Review the exact PROD application hostname, authentication path, tunnel
  destination, origin exposure, negative routes, and rollback (`KIF-011`, `KIF-012`).
- [ ] Obtain separate explicit approval for the PROD DNS/Tunnel cutover (`KIF-002`).
- [ ] Publish only the approved PROD application route (`KIF-011`).
- [ ] Verify public login/PROD and negative public reachability for DEV, Argo,
  identity administration/management, and data services (`KIF-012`).
- [ ] Rehearse each route rollback while private identity and PROD remain healthy
  (`KIF-030`).

## Guarded host rclone and pending proxy transfer

- [x] Add source-only pinned rclone `1.71.1` installer with controller verification,
  host transfer, task-selection/injection guard, check/apply/rollback modes, service
  preservation, and selector-only rollback (`KIF-002`, `KIF-005`, `KIF-007`,
  `KIF-013`, `KIF-030`).
- [x] Add source-only exact encrypted proxy transfer with host-operator getent
  resolution, config-metadata-only handling, immutable upload/readback, guarded
  cleanup, controller decryption checks, and `drive-verified` binding (`KIF-002`,
  `KIF-005`, `KIF-013`–`KIF-015`, `KIF-027`, `KIF-030`).
- [x] Remove controller rclone from proxy Secret bootstrap and require exact transfer
  verification before Secret variables or Kubernetes mutation (`KIF-013`–`KIF-015`,
  `KIF-030`).
- [x] Complete installer apply/idempotence. Earlier applies stopped before host
  mutation on missing nested-module `normal` dispatch and an unrendered operator role
  default. Both fixes pass focused/full offline validation. A fresh check passed at
  `ok=25 changed=1 failed=0`; the separately approved corrected install passed at
  `ok=34 changed=4 failed=0`, selected verified rclone `1.71.1`, and preserved
  k3s/Tailscale health. The separately approved idempotence apply passed at
  `ok=32 changed=0 failed=0` (`KIF-002`, `KIF-007`, `KIF-030`).
- [x] Complete interactive non-root host OAuth through a reviewed private SSH
  callback tunnel; token-bearing config exists only on the host (`KIF-002`,
  `KIF-013`–`KIF-015`).
- [x] Complete transfer apply/readback. After one stopped apply, reviewed fix, exact
  cleanup, and transient host-offline stop, check passed `ok=26 changed=0`; apply
  passed `ok=39 changed=7`, including immutable upload/readback, controller decrypt,
  exact relationship verification, `drive-verified`, and zero host staging residue
  (`KIF-002`, `KIF-027`, `KIF-030`).
- [x] Complete exact proxy Secret bootstrap after marker review at
  `ok=15 changed=1 failed=0`; a later invocation refused implicit credential rotation
  before Ansible/Kubernetes (`KIF-002`, `KIF-013`–`KIF-015`, `KIF-030`).

## Closeout

- [ ] Run independent security, recovery, and documentation review.
- [ ] Disposition every finding and rerun affected gates.
- [ ] Update testcases, manual QA, status, and runbooks with actual, sanitized
  evidence (`KIF-030`).
- [ ] Mark complete only after restore, rollback, exposure, and isolation gates pass.

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
- [ ] Separately approve one elevated read-only discovery rerun and human-review the
  actual kubelet version plus `shared-services` scope before deciding Argo CD
  compatibility; the historical live report captured neither current field
  (`KIF-001`, `KIF-002`, `KIF-008`, `KIF-030`).
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
- [ ] Implement only explicitly approved external resources and review a sanitized
  plan with no destroy/replacement or public route (`KIF-002`, `KIF-005`, `KIF-013`).
- [ ] Obtain explicit approval for the first exact reviewed OpenTofu apply (`KIF-002`).
- [ ] Create no public application route in this stage (`KIF-010`, `KIF-011`).

Stop gate: stop on secret-bearing state/plan, replacement/destroy outside scope, or
missing state recovery. Reverse changes only through another reviewed plan.

## Pre-Stage-4 — bounded platform Namespace bootstrap exception

- [x] Commit exact `argocd` and `platform-edge` Namespace source plus the bounded
  `state: present`, no-delete Ansible bootstrap exception (`KIF-002`, `KIF-005`).
- [ ] Obtain separate human approval for only
  `ansible/bin/bootstrap-platform-namespaces check`, then inspect its complete result
  before any mutation (`KIF-002`, `KIF-005`).
- [ ] After accepting the check result, obtain separate human approval for the first
  `ansible/bin/bootstrap-platform-namespaces apply` and reconcile exactly the two
  reviewed Namespaces (`KIF-002`, `KIF-005`).
- [ ] Verify exact identity, labels, Active phase, and service health, then obtain
  separate human approval for a second
  `ansible/bin/bootstrap-platform-namespaces apply` and require `changed=0`
  (`KIF-002`, `KIF-005`).

Stop gate: stop on foreign ownership, source drift, any unexpected object or change,
failed verification, or nonzero change on the second apply. Runtime remains NOT RUN;
these checklist entries grant no live approval and waive no Stage 4 entry gate.

## Stage 4 — GitOps and secret bootstrap

- [x] Record public Argo CD chart, captured signature/hash-binding, image, and ignored
  minimal-render research in a source-only
  [candidate provenance record](../../runbooks/argocd-candidate-provenance.md),
  explicitly without version selection, chart/values/Kubernetes source, secret,
  runtime, or deployment (`KIF-005`, `KIF-013`, `KIF-023`, `KIF-030`).
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
- [ ] Human-select and soak the Argo CD chart/application candidate only after actual
  target kubelet compatibility, signing-key trust/status, generated/internal Secret
  ownership and recovery, private Git secret-zero/recovery, exact image availability
  plus component flow controls, bootstrap ownership, and runtime approval gates are
  resolved; then add and review deployable source
  separately (`KIF-002`, `KIF-005`, `KIF-013`, `KIF-015`, `KIF-023`).
- [ ] Pin and render a provenance-consistent Infisical operator version
  (`KIF-005`, `KIF-013`, `KIF-023`).
- [ ] Approve and document the private Git/Infisical/GHCR/Cloudflare secret-zero
  sequence (`KIF-014`, `KIF-015`).
- [ ] Obtain explicit approval for bounded Argo CD bootstrap (`KIF-002`).
- [ ] Keep Argo CD private and prove Git reconciliation using a demo workload
  (`KIF-010`, `KIF-022`).
- [ ] Prove one non-sensitive Infisical sync, rotation, and revocation without value
  disclosure (`KIF-013`–`KIF-015`).

Stop gate: stop if an admin surface becomes public, secret content appears in Git or
logs, or bootstrap cannot be recovered.

## Stage 5 — namespaces, policy, and shared data

- [ ] Approve StorageClass, live-data path, backup path, capacity, and any destructive
  disk preparation separately (`KIF-002`, `KIF-003`, `KIF-019`, `KIF-026`).
- [ ] Add DEV, PROD, and shared-services namespaces, service accounts, RBAC, quotas,
  limits, and default-deny policies (`KIF-016`, `KIF-019`, `KIF-021`).
- [ ] Obtain explicit approval before creating stateful services (`KIF-002`).
- [ ] Create shared PostgreSQL with separate databases/roles and negative access
  tests (`KIF-017`).
- [ ] Create shared MongoDB with separate databases/users and negative access tests
  (`KIF-018`).
- [ ] Create per-environment Redis; retain shared RabbitMQ only after separate
  user/vhost/limit tests (`KIF-020`).
- [ ] Complete backup and isolated restore tests before application data is accepted
  (`KIF-026`–`KIF-028`).

Stop gate: stop on cross-access, public data exposure, failed restore, unsafe node
pressure, or inability to preserve encryption keys. Never delete PVCs as rollback.

## Stage 6 — private DEV

- [ ] Deploy the minimal CristexHub DEV slice by immutable digest (`KIF-023`,
  `KIF-024`).
- [ ] Validate OIDC/auth, API, worker, exactly-one Beat, migration, WebSocket, and
  private routing behavior (`KIF-010`, `KIF-021`, `KIF-025`).
- [ ] Measure capacity before adding Reactive Resume, Browserless, or other optional
  components (`KIF-019`, `KIF-029`).
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

## Stage 9 — public PROD

- [ ] Review the exact Cloudflare hostname, authentication path, tunnel destination,
  origin exposure, negative routes, and rollback (`KIF-011`, `KIF-012`).
- [ ] Obtain explicit approval for DNS/Tunnel cutover (`KIF-002`).
- [ ] Publish only the approved PROD application route (`KIF-011`).
- [ ] Verify public PROD and negative public reachability for DEV/admin/data services
  (`KIF-012`).
- [ ] Rehearse route rollback while private PROD remains healthy (`KIF-030`).

## Closeout

- [ ] Run independent security, recovery, and documentation review.
- [ ] Disposition every finding and rerun affected gates.
- [ ] Update testcases, manual QA, status, and runbooks with actual, sanitized
  evidence (`KIF-030`).
- [ ] Mark complete only after restore, rollback, exposure, and isolation gates pass.

# Status — k3s-iac-foundation (G1)

state: agent:in-progress
phase: implementing
build: schema-v3 kubelet-version discovery and Namespace bootstrap pass offline; target version/Argo compatibility and runtime/provider/state/backup/apply pending
date: 2026-08-06
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
  scope was `shared-data` and it did not capture a Kubernetes version. Current source
  now queries `shared-services` and projects the exact kubelet version; both changes
  pass offline only and remain NOT RUN pending one separately approved elevated
  read-only rerun and human review. Argo CD compatibility is not established. The
  unmounted filesystem, disk health, contents, reuse decision, and off-node backup
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
  Exact committed Namespace source now defines only `argocd` and `platform-edge`.
  The bounded Ansible bootstrap loads those manifests, requires state present and
  exact bootstrap/future-owner labels, refuses forged internal results and foreign
  existing Namespaces, and has no delete path. Its non-passthrough wrapper rejects
  task-skipping controls, launches the repository `.venv` controller in an allowlisted
  clean environment, and creates a private random single-run attestation. The mutating
  task independently requires that attestation, reloads only the two literal manifest
  paths, and rejects extra top-level or metadata keys. The labels identify Ansible as
  bootstrap writer and Argo CD only as future desired owner. Argo ownership remains
  pending installation, Namespace adoption or Application registration, and
  successful sync evidence; the label alone is not a handoff. Its cluster
  check/live/idempotence are NOT RUN; Argo CD, cloudflared,
  `shared-services`, DEV/PROD namespaces, Secrets, workloads, Services, and routes do
  not exist from this increment. The future shared service Namespace is named
  `shared-services`, but it is not created.
  No external-resource, secret, data, or deployment operation was performed. Object
  listings and offline tests do not prove replacement recovery.

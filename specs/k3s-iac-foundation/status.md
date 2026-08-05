# Status — k3s-iac-foundation (G1)

state: agent:in-progress
phase: implementing
build: admin/client/reboot recovery pass; CNI probe, storage discovery, and decision-first replacement runbook/register offline-implemented; extended storage run, image digest, runtime probes, and replacement execution pending
date: 2026-08-05
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
  behavior fields; bounded PV metadata; and PVC metadata from five fixed namespaces.
  The projection emits no device serial, generated PV identifier, address, backing
  path, filesystem content, Secret, ConfigMap, or broad PVC result. This increment
  has not contacted the inventory host or Kubernetes API, so the prior nine-query
  elevated report remains the latest runtime storage evidence and unmounted
  filesystem type plus live PV/PVC placement remain unverified.
  A bounded read-only CNI/NetworkPolicy probe planner is implemented offline. It
  cannot create, patch, execute in, or delete Kubernetes objects; Argo CD remains
  the only object writer. The planner has not contacted the inventory host or API.
  Mutating probe code remains NOT IMPLEMENTED/BLOCKED pending a verified image
  digest, atomic namespace ownership, exhaustive foreign-resource-safe cleanup, and
  separate create/delete approvals.
  The first replacement-host recovery increment is documentation-only. Its
  secret-free runbook/register truthfully separates the verified same-host reboot
  from replacement, requires independently verified old-host fencing and storage
  exclusivity, stops on split-brain risk, and requires exactly one approved
  preserve-existing-identity or create-new-cluster model. Datastore type, exact k3s
  version/config, token custody, storage mapping, RPO/RTO, off-node artifacts, and
  isolated restore remain `UNKNOWN — STOP`; no recovery command or automation was
  guessed. CNI behavior, NetworkPolicy enforcement, replacement execution, and
  later platform work therefore remain pending. No external-resource, secret, data,
  or deployment operation was performed. Object listings and offline tests do not
  prove functional enforcement or replacement recovery.

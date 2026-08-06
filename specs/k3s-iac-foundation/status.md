# Status — k3s-iac-foundation (G1)

state: agent:in-progress
phase: implementing
build: admin/client/reboot recovery pass; gated CNI functional probe, storage discovery, and decision-first replacement runbook/register offline-implemented; extended storage run, verified probe image, runtime probes, and replacement execution pending
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
  A bounded CNI/NetworkPolicy functional probe is implemented offline with separate
  plan, run, and cleanup paths. It uses an existing namespace, API-generated names,
  two fixed ownership labels, private exact-UID ledger recovery, fixed-kind
  interruption rediscovery, selectorless Service plus explicit EndpointSlice, UID
  delete preconditions, non-cascading `Orphan` propagation,
  `always` cleanup, and zero-residue assertions; it has no remote exec
  and never creates or deletes a Namespace. The probe has not contacted the inventory
  host or API. Runtime remains NOT RUN/BLOCKED pending an independently verified
  digest-qualified linux/amd64 `httpd`/`wget` image, a reviewed temporary Argo CD
  ownership exception, a unique run ID, and separate create/delete approvals.
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

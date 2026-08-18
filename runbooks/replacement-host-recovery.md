# Replacement-host recovery: decision-first runbook

## Status and boundary

This is the first **offline, documentation-only** replacement-host recovery
increment. It defines evidence, decisions, and stop gates; it does not install k3s,
restore a datastore, recover a token, attach storage, change a route, or automate a
replacement. No replacement recovery has been run or proven.

The executed reboot verifier covers only a reboot of the same host with its existing
installation, datastore, token, storage, and cluster identity intact. Its successful
SSH/Tailscale return, running services, Ready node, and kubeconfig access do **not**
prove recovery after hardware loss, reinstallation, disk loss, datastore restoration,
or creation of another cluster. Use this runbook when the original host or any of
those identity/state assumptions cannot be trusted. Do not relabel a replacement as
a reboot to bypass these gates.

The companion
[`recovery-artifact-register.md`](recovery-artifact-register.md) is the secret-free
working register. Every required unknown remains a blocker until an operator records
sanitized evidence and approves the applicable mutation separately.

## Non-negotiable rules

- An incident commander owns the recovery decision and records operator, UTC time,
  incident reference, approvals, evidence references, and results without secret
  values.
- Discovery remains read-only and separate from mutation. Each host, storage,
  secret, external-resource, restore, or public-route mutation needs its own explicit
  approval under `AGENTS.md`.
- Never copy a kubeconfig, server token, private key, tunnel credential, Infisical
  bootstrap credential, application encryption key, or database credential into
  this repository, the register, a command line, a ticket, or logs. Record only a
  custodian-approved off-node reference and a verification result.
- Never use namespace/PVC deletion, disk formatting, a blind external destroy, or a
  destructive backup mirror as recovery setup or rollback.
- Git and Argo CD can reconstruct reviewed desired state; they cannot reconstruct
  secret values, mutable data, the k3s datastore/token, or external state.
- Keep all application traffic private until replacement acceptance is complete.
  Public PROD reactivation is a later, separately reviewed operation.

## Gate 0 — classify the event

Record one classification before proceeding:

1. **Reboot/same-host recovery** — the same trusted installation, datastore, token,
   storage, and cluster identity remain intact. Use only the bounded reboot verifier;
   this replacement runbook is not evidence for that execution.
2. **Replacement-host recovery** — hardware, operating system, k3s installation,
   datastore, token, storage attachment, or cluster identity must be restored or
   reconstructed. Continue below.
3. **Unknown** — evidence cannot establish either case. Stop and treat it as
   replacement-host recovery; do not start another server.

Stop if the classification depends on an assumption rather than independent,
sanitary evidence.

## Gate 1 — isolate the old host and prevent split brain

Before starting k3s on any replacement or attaching any recovery storage writable,
record independent evidence that the old host is fenced:

- it cannot boot or continue serving the cluster;
- it cannot use Tailscale, tunnel, DNS/origin, or other network paths to receive or
  advertise production traffic;
- it cannot concurrently mount, write, or attach the datastore or application
  storage selected for recovery; and
- it cannot automatically rejoin when power or connectivity returns.

Fencing must be reversible and must not destroy the only recoverable copy. Record
who applied it, when, how it was independently verified, and the rollback owner; do
not record credentials or sensitive endpoint details.

**Split-brain stop gate:** if any old-host reachability, power state, route ownership,
storage exclusivity, or automatic-rejoin condition is unknown, stop. Do not start
k3s on the replacement, attach shared/recovered storage writable, restore the
cluster datastore, reconcile stateful workloads, rotate identity material, or
reactivate a public route. If the old host later reappears, stop both recovery and
traffic changes until exactly one host is fenced and storage ownership is again
exclusive.

## Gate 2 — choose the recovery identity model

An operator must approve exactly one model and record the reason in the artifact
register. There is no automatic default and no hybrid path.

### Preserve the existing cluster identity

Choose this only when all of the following are verified compatible and available
off-node: the actual datastore type and restorable artifact, exact k3s version and
configuration, required server token reference, storage mapping, and the documented
restore method. The old host must already be fenced. Preserve-identity recovery must
follow a version/datastore-specific procedure reviewed later; this runbook does not
invent that procedure.

Stop if compatibility, integrity, backup age, encryption access, token custody, or
storage exclusivity is unknown. Never import an old datastore into a separately
initialized fresh cluster and never combine state from different backup times
without an approved consistency analysis.

### Create a new cluster identity

Choose this when the old identity cannot be safely restored or when a deliberate
new-cluster rebuild is approved. Treat it as reconstruction: establish a newly
approved identity, reconcile reviewed desired state, restore mutable data through
application-aware restore procedures, and explicitly rebind external references.
Do not reuse unverified old datastore files or silently carry forward old node,
certificate, token, tunnel, or external-resource ownership.

A new-cluster decision does not authorize secret creation/rotation, k3s
installation, data restoration, storage mutation, DNS/tunnel changes, or public
cutover. Those remain separate gates. Stop if owners cannot state how stale cluster
access and external bindings will be revoked without breaking the only recovery
path.

## Gate 3 — complete the prerequisite register

All Gate 3 prerequisite rows in the companion register start as `UNKNOWN — STOP`.
Later execution-plan and rehearsal rows are populated only at Gates 4 and 5 and do
not block writing the plan. Before Gate 4, require the following to be known,
reviewed, and supported by off-node evidence:

- actual k3s datastore type, backup format, integrity result, backup time, restore
  compatibility, and recovery procedure;
- exact installed k3s version, architecture, install/configuration inputs, and an
  approved source for the pinned artifact;
- k3s server-token custody and a tested recovery reference, without exposing the
  value;
- physical/logical storage inventory, filesystem and mount design, volume placement,
  required capacity, ownership, encryption access, and exclusive attachment plan;
- declared RPO and RTO, the incident recovery point, expected data loss, and timed
  recovery acceptance method;
- verified off-node availability and independent access for Git desired state,
  immutable images or reproducible builds, OpenTofu state, Infisical bootstrap
  material, application encryption keys, Argo/GHCR access references, external-route
  ownership, and environment-separated mutable-data backups.

A file existing only on the failed node is not a recovery artifact. A backup job
exit code, object listing, or reboot success is not restore evidence.

## Gate 4 — approve a concrete execution plan

Only after Gates 0–3 pass, write and review a separate execution plan for the chosen
identity model. It must use the actual discovered version, datastore, token custody,
storage mapping, owners, and tool-specific restore documentation. The plan must
include:

1. exact mutation approvals and rollback checkpoints;
2. old-host fencing and replacement-host fallback access;
3. Debian and host prerequisites owned by Ansible;
4. pinned k3s installation/configuration and the chosen identity procedure;
5. exclusive storage preparation without implicit format or deletion;
6. external-state ownership recovery without blind apply/destroy;
7. private Argo CD, Infisical, and GHCR bootstrap references;
8. reviewed Kubernetes desired-state reconciliation through Argo CD;
9. environment-separated, application-consistent data and encryption-key restore;
10. private validation, negative cross-access checks, and measured RPO/RTO; and
11. a separate public-route reactivation review only after private acceptance.

This increment deliberately contains no executable k3s, datastore, token, disk,
backup, provider, or Kubernetes recovery command. Do not translate these stages into
a guessed command sequence.

## Gate 5 — acceptance and rollback discipline

Replacement recovery remains **NOT RUN/BLOCKED** until an approved plan is executed
in an isolated rehearsal and its sanitized evidence is reviewed. Acceptance must
show one authoritative cluster, one storage writer, expected private routes only,
Ready control plane, desired-state reconciliation, environment isolation, restored
mutable data and encryption behavior, backup freshness, and measured RPO/RTO.

If recovery fails, keep public routing disabled and preserve evidence. Roll back to
a known checkpoint only after fencing the replacement. Returning to the old host is
not a routine fallback: it requires independent proof that the replacement is
fenced, the old host is authoritative, storage ownership is exclusive, and restored
state will not move backward without explicit data-loss acceptance.

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

The external CristexHub application repository publishes backend, frontend, and
code-runner images to GHCR. This repository implements seven executed bounded
Ansible workflows, including the temporary functional probe. It now has an
offline-validated gated OpenTofu installer and zero-resource Cloudflare-only source
scaffold. The first live run stopped after two bounded directory tasks because the
host had no route to GitHub. The reviewed controller-cache and Ansible-transfer
recovery subsequently passed check, live installation, and a `changed=0` rerun; the
pinned CLI and selector now exist without host egress. Committed Kubernetes desired
state is limited to exact `argocd` and `platform-edge` Namespace manifests plus a
bounded Ansible bootstrap. Its separately approved first apply created exactly those
two Active Namespaces with the reviewed labels; no workload or other persistent kind
exists from this increment. The source-only
[Argo CD candidate provenance record](runbooks/argocd-candidate-provenance.md)
records chart `10.3.0`, application `v3.5.0`, captured signature/hash-binding,
immutable linux/amd64 images, and ignored 44-document render evidence. It is explicitly **CANDIDATE — NOT
DEPLOYABLE — NOT SELECTED**. The target minor screen passes for Kubernetes `1.36`,
but full k3s/rendered API/CRD compatibility, human version selection and soak,
signing-key trust/status, generated/internal Secret ownership and recovery,
private Git secret-zero, exact image availability plus component flow controls,
bootstrap ownership, and runtime approvals remain blockers. It
adds no chart, values, or Kubernetes object source. The separate source-only
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
and image tag were not observed during the bounded capture, from the last observed
version-aligned `v0.11.7` chart/source/image set. Neither is selected or deployable;
runtime is **NOT RUN**. Actual compatibility, chart/image trust, dedicated Namespace,
scoped RBAC, Argo handoff, secret-zero, network policy, recovery, and runtime
approvals remain blocked. It adds no chart, CRD, Kubernetes object, credential, or
Secret source.
No state file, provider initialization, plan, apply, Helm installation, Kustomize
workload, GitHub Actions, or general host baseline exists yet. Debian plus Ansible is
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
- self-hosted secrets, registry, or CI runner during the first implementation;
- automatic PROD promotion or destructive automatic rollback;
- moving privileged code-runner onto the shared node without separate isolation.

## Ownership model

| Layer | Owner | State source |
|---|---|---|
| Debian host and k3s baseline | Ansible | playbooks and inventory under `ansible/` |
| Cloudflare and GitHub resources | OpenTofu | configuration under `opentofu/`; protected host-local single-writer state plus mandatory encrypted off-node recovery |
| Kubernetes objects | Argo CD | manifests and Helm values under `kubernetes/` |
| Secret values and rotation | Infisical Cloud initially | separate DEV, PROD, and infrastructure scopes |
| CI and image publication | GitHub Actions | workflows and immutable GHCR digests |
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
handoff. Argo CD is the intended sole persistent Kubernetes reconciler after that
verified handoff. Operational procedures belong under `runbooks/` when implementation
is approved.

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
controller. Application source, local Compose, Keycloak theme, and Browserless
gateway assets remain in that application repository and are not owned here.

The first private DEV hostname may use a tailnet name. A custom private
`dev-hub.cristex-soft.com` name requires a later private-DNS and certificate
decision. The intended public PROD host is `hub.cristex-soft.com`.

Cloudflare Tunnel must never route DEV, SSH, k3s API, Argo CD, databases, Redis,
RabbitMQ management, Browserless, code-runner, or identity administration.
Cloudflare and Tailscale do not replace application OIDC/JWT enforcement.

## Namespace model

| Namespace | Purpose |
|---|---|
| `argocd` | Argo CD controllers and private UI/API |
| `platform-edge` | Cloudflare Tunnel connector only; no route exists until separately approved |
| Infisical operator namespace | Secret synchronization controller; exact dedicated name is a pending human decision |
| `shared-services` | Shared PostgreSQL, MongoDB, and any retained shared RabbitMQ |
| `cristexhub-dev` | DEV applications and environment-local dependencies |
| `cristexhub-prod` | PROD applications and environment-local dependencies |
| Optional backup/monitoring namespaces | Added only when their first workload is approved |

Namespace names organize ownership but are not a hard security boundary. Service
accounts, RBAC, NetworkPolicy, database authorization, credentials, and negative
connectivity tests provide the enforceable controls.

## Shared data design

A single PostgreSQL engine and a single MongoDB engine save memory. This is an
explicitly accepted shared failure and contention domain.

PostgreSQL requires separate databases and owner roles, including at minimum
`cristexhub_dev` and `cristexhub_prod`. MongoDB requires separate databases and
users with privileges limited to their own database. DEV and PROD never share an
application credential, encryption key, migration target, or backup prefix.

The application role must not create roles or databases. A bounded, idempotent,
Argo-managed provisioning job or a later approved operator creates principals from
Infisical references. Its administrator credential is not available to application
pods.

Redis remains per environment because Redis database numbers are not sufficient
security isolation. A shared RabbitMQ is permitted only with distinct users,
virtual hosts, limits, and negative access tests. A later capacity decision may
separate it.

NetworkPolicy must allow each application namespace to reach only its own approved
database endpoints and deny cross-environment application traffic. Database engines
remain ClusterIP-only.

## Secrets

Infisical Cloud stores values during the initial implementation; self-hosting is
out of scope. Git stores only secret references. DEV, PROD, and infrastructure use
separate scopes and machine identities with least privilege. The bootstrap method
is a decision gate because Argo private-repository access, Infisical
authentication, GHCR pulls, and Cloudflare connector credentials form a secret-zero
sequence.

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
Argo CD becomes the persistent Kubernetes-object reconciler only after its pending
installation, Namespace adoption or Application registration, and successful sync
evidence.

Backups require database-consistent PostgreSQL and MongoDB dumps, separate DEV/PROD
paths, compression, encryption, integrity checks, local retention, and an encrypted
off-host copy. The intended off-host target is Google Drive through containerized
`rclone copy`, not destructive `sync`. k3s datastore and recovery token, OpenTofu
state, Infisical recovery credentials, and runbooks require separate recovery
coverage.

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
- Gate: separately approve a second wrapper `apply` and require `changed=0`; this
  idempotence checkpoint remains unrun.
- Stop: foreign ownership, an unexpected object or change, source drift, failed
  verification, or nonzero change on the second apply.
- Ownership: Ansible remains the bootstrap writer. Argo CD is only the future desired
  owner until installation, adoption or Application registration, and successful
  sync evidence; a label alone is not a handoff.
- Boundary: this exception does not waive the Stage 4 entry gates and does not
  authorize Argo CD, Infisical, cloudflared, or any other persistent Kubernetes
  object.

### Stage 4 — minimal GitOps and secrets bootstrap

- Current source-only evidence: the
  [Argo CD candidate provenance record](runbooks/argocd-candidate-provenance.md)
  binds public chart, captured signature/hash-binding, image metadata, and an ignored
  minimal render. The
  candidate retains ApplicationSet because chart `10.3.0` has no effective
  `applicationSet.enabled` disable gate. The captured target minor `1.36` appears in
  Argo CD `3.5`'s official tested matrix and passes the chart semver gate, but this is
  not version selection, deployable desired state, k3s-specific/runtime, or full
  rendered API/CRD compatibility proof.
- Current source-only cloudflared evidence: the
  [candidate provenance record](runbooks/cloudflared-candidate-provenance.md) binds
  release, unsigned source, architecture-specific image, token-file, health, and
  edge-transport facts while leaving trust, hardening, secret-zero, external-resource
  state/recovery, component policy, route selection, and runtime blocked. It is not
  deployable source or a version selection.
- Current source-only Infisical evidence: the
  [candidate provenance record](runbooks/infisical-operator-candidate-provenance.md)
  records the incomplete observed `v0.11.8` public distribution and last observed
  version-aligned `v0.11.7` set while leaving both **CANDIDATE — NOT DEPLOYABLE — NOT
  SELECTED** with runtime **NOT RUN**. The actual target kubelet is now captured, but
  chart/CRD/API compatibility, trust, Namespace, scoped-RBAC,
  Argo handoff, secret-zero, traffic, recovery, and runtime gates remain blocked.
- Entry: pinned component versions, human-reviewed target kubelet-version evidence,
  verified Kubernetes compatibility, and an approved secret-zero procedure.
- Work: bootstrap Argo CD, private repository access, Infisical operator, and one
  non-sensitive demonstration secret only after every Stage 4 entry gate passes.
- Gate: Argo is private, reconciles a demo workload, and secret values remain absent
  from Git/logs.
- Stop: admin endpoint becomes public or bootstrap credentials cannot be recovered.
- Rollback: uninstall only newly bootstrapped stateless controllers after evidence
  capture; preserve data and access.

### Stage 5 — isolation and shared data

- Entry: StorageClass, capacity, backup, and resource-limit decisions approved.
- Work: namespaces, service accounts, RBAC, NetworkPolicy, PostgreSQL, MongoDB,
  principals, and environment-local Redis.
- Gate: positive own-environment access, negative cross-environment access, backup,
  and isolated restore all pass.
- Stop: cross-access succeeds, backup cannot restore, or node pressure is unsafe.
- Rollback: restore verified data/config; never delete PVCs as routine rollback.

### Stage 6 — DEV

- Entry: shared-services gate passes.
- Work: deploy the minimum CristexHub DEV slice privately and add services only after
  measuring capacity.
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
- identity provider placement and hosted OIDC URLs;
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
4. bootstrap Argo CD private access;
5. restore Infisical/GHCR/Cloudflare access references;
6. reconcile namespaces, policies, and stateful services;
7. restore databases and application encryption keys;
8. reconcile DEV/PROD workloads by immutable digest;
9. validate privately;
10. re-enable the public PROD route only after acceptance.

Git and Argo reconstruct desired state. They do not restore mutable data, secret
values, or external state by themselves.

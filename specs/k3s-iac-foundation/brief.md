# Brief — G1: k3s IaC foundation

## Problem

CristexHub has production-capable service images in its application repository but
no hosted orchestration supported by this infrastructure repository. The target
server already runs single-node k3s, while the desired host, external-resource,
GitOps, secret, data, backup, and operational recovery automation are not yet implemented.

## Outcome

Create a small, educational infrastructure-as-code path at repository-root
`ansible/`, `opentofu/`, `kubernetes/`, and `runbooks/` that can reproduce and
recover DEV and PROD without presenting a single node as highly available.

## Current live checkpoint — 2026-08-21

Private CristexHub PROD activation is live at revision
`751885a42798d282e168131db147f13694a0a621`: Argo is `Synced/Healthy`, all five
PROD Deployments are ready, backend root returns `200`, oauth2-proxy returns the
expected private `302`, and Celery is ready on the PROD RabbitMQ vhost. The OIDC
CONNECT proxy admits the reviewed PROD clients. App-level OIDC smoke (backend `200`,
oauth2-proxy `302`, Celery readiness) passed, but this is not full authenticated
OIDC/CONNECT validation. The source allowlist is exact: `auth.cristex-soft.com:443`
and `api.deepseek.com:443`; arbitrary HTTPS destinations remain denied.

MongoDB `8.0.12` is live as an operator-managed one-member replica set with
TLS/SCRAM, but private acceptance remains blocked: the live `shared-mongodb-0` has
no matching NetworkPolicy and the legacy selectors do not match the live MongoDB or
backend/Celery labels. RabbitMQ is live but its observed PROD principal and broad
permission expressions need least-privilege reconciliation. Engine connectivity and
runtime Secret presence do not prove logical database scope authorization or
cross-access negatives; those remain separate gates. MongoDB/RabbitMQ URL credentials
and the reused GHCR pull credential require verified rotation; the exposed DeepSeek
key remains a separate revoke/replace residual.

OpenTofu current checkpoint: protected host state contains exactly five imported
resource addresses (Tunnel, Tunnel configuration, Keycloak DNS, DEV DNS, and private
Argo DNS). The source defines six resource addresses; only the PROD DNS resource is
absent from state. The pending PROD route still requires one Tunnel-config update
and one proxied `hub.cristex-soft.com` DNS create; no apply has run for those two
changes. The provider lockfile is tracked, the cloudflared token handoff is complete,
and the public route remains unapplied. Reactive Resume DEV has a private
runtime/hostname checkpoint and the shared `cristexhub` client source check passed
without Keycloak/API or Kubernetes mutation. A separate recorded private-runtime
acceptance completed the shared-realm OIDC/session/logout application cycle for
`reactive-resume-dev`; that evidence must not be attributed to the source-only
wrapper. The prior installed backup source
produced the sanitized schema-1 non-empty receipt
`run_id=20260825T065948Z object_count=1 total_object_bytes=50 readback=verified
encrypted=true private_residue=none`; hardened schema-2 installation, fresh
schema-2 backup, isolated restore, measured RPO/RTO, and final scheduler
idempotence remain pending. The Infisical-owned `argocd-repository-cristexweb` credential is materialized;
Reactive Resume Argo revision `dd7d4cedd902e68266d9713d1dbb8e90f0b529b1` is
`Synced/Healthy`, and all seven desired resources carry tracking annotations.
The API omits `metadata.managedFields`, so manager-field evidence is unavailable;
15 out-of-scope resources remain reported as orphans and pruning stays disabled.
PROD and public routing remain inactive. The source-only paragraphs below preserve
historical checkpoint evidence and are not current absence claims.

## Approved direction and historical checkpoint narrative

The architecture bullets below intentionally retain earlier source-only statuses for
traceability; use the current checkpoint above for live state.

- Minimal Ansible owns the Debian host/k3s baseline and is selected as the future bounded bootstrap installer for exact foundational Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, one self-hosted Keycloak, privileged CRDs/cluster RBAC, and Keycloak realm/client/group reconciliation. Each component needs separate source and check/apply/idempotence approvals.
- OpenTofu owns Cloudflare and GitHub resources, not Kubernetes objects.
- Argo CD owns namespaced desired state only after Ansible stops reconciling the exact object set and registration/adoption, successful sync, and managed-field evidence pass; dual reconciliation is forbidden.
- Infisical Cloud initially owns runtime secret values; only its Kubernetes Operator is bootstrapped and self-hosting Infisical is out of scope for the foundation.
- One future self-hosted Keycloak shared by CristexHub, Reactive Resume, and Argo CD is selected as the identity target. Keycloak `26.7.1`, PostgreSQL `17.10`, realm `cristexhub`, the stable issuer, direct Argo OIDC, and value-free authorization policy are selected only for offline source authoring; executable source and runtime remain blocked. Keycloak authenticates/emits groups, Argo RBAC authorizes Argo actions, and Kubernetes RBAC constrains controllers.
- GitHub Actions owns source validation and future immutable private-GHCR publication but never deploys. Current infrastructure/application workflows are SHA-pinned read-only CI only; package publication is disabled pending trusted build inputs and digest evidence.
- Bundled k3s Traefik remains the sole ingress controller.
- DEV and administration remain private through host Tailscale.
- Only approved PROD application routes become public through Cloudflare Tunnel.
- Exact [CristexHub DEV Namespace source](../../runbooks/cristexhub-dev-namespace-bootstrap.md) exists with four approved labels. Its check passed at `ok=20 changed=1 unreachable=0 failed=0 skipped=2` without mutation. The first apply passed at `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created/verified the exact Namespace, and preserved service health. Idempotence passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`; the checkpoint is complete. Separate exact present-only [CristexHub PROD Namespace source](../../runbooks/cristexhub-prod-namespace-bootstrap.md) also exists with four approved labels, and its separately approved checkpoint is now `Active` and idempotent. Earlier source-only live-absence wording is historical pre-checkpoint evidence; later PROD resources and runtime remain NOT RUN/BLOCKED. The source-only PROD runtime Infisical seam is a separate value-free blocked contract. A five-object source-only PROD Argo registration now pins protected-main revision `751885a42798d282e168131db147f13694a0a621` behind manual sync plus an always-active deny window; its check/apply and sync transition are NOT RUN/BLOCKED. Later PROD runtime promotion remains gated on DEV validation, recovery, soak, independent identity values, immutable image promotion, private validation, and separate resource approvals.
- `platform-edge` is reserved for cloudflared. Future `shared-services` placement is the Infisical Cloud Operator, a separate Keycloak deployment, one general PostgreSQL engine, one shared MongoDB engine, and one shared RabbitMQ engine; the exact Namespace now exists after passed check/first apply/idempotence, with final `changed=0`, while every component runtime remains NOT RUN. CristexHub DEV/PROD use dedicated scopes on both shared engines; Keycloak and environment-local Reactive Resume DEV/PROD use dedicated PostgreSQL logical databases, owner roles, credentials, migrations, and backup scopes. The canonical database, RabbitMQ, backup, and Reactive Resume policies remain value-free and runtime-blocked; read-only evidence now records pre-existing unaccepted Reactive Resume DEV/PROD PostgreSQL CRs and credential Secrets from the broad lane. RabbitMQ DEV/PROD consumers have dedicated vhost/user/permission/limit/recovery scopes; future consumers require reviewed exact changes. Backup access is private/authenticated through a metadata-only catalog and non-destructive encrypted off-node copy direction. The database source profile fixes NVMe `local-path`, 40/80 GiB PVCs, bounded resources, standard private Services/TLS, daily archives, 14-day retention, RPO 24h, and RTO 4h. PostgreSQL and standalone non-authoritative MongoDB now have offline-pinned, hash-bound, present-only source closures with exact cryptographic Secret validation. A separate guarded Infisical database Secret seam freezes one shared Connection, separate engine Auth/credential identities, two path-scoped StaticSecrets, four exact target contracts, namespace-scoped VAP/bindings, and additive writer RBAC. Reactive Resume DEV/PROD target Secrets are live but exposed/unaccepted and require rotation/revocation; apply provenance, trust/recovery, and runtime remain blocked. RabbitMQ storage/ports, exact backup destination identities, all live Secret material, trust/recovery, check/apply/idempotence, and runtime proof remain unselected or blocked.
- Redis remains per environment.

## Constraints

- The host has about 16 GiB RAM and is one hardware, control-plane, disk-controller, and maintenance failure domain.
- Downtime is accepted; data loss without a declared RPO is not.
- Logical environment isolation does not make shared engines highly available or eliminate resource contention.
- DEV must pass first. PROD must pass privately before public cutover.
- Every mutation and public exposure requires an explicit operator approval gate.

## Non-goals

- multi-node HA, multi-cluster deployment, or replicated storage;
- service mesh, custom platform operators, policy engines, or autoscaling;
- local image registry or self-hosted CI runner;
- direct GitHub Actions deployment;
- migration of code-runner to the shared node without a separate security decision;
- application source, local Compose, development Keycloak realm/theme, or Browserless gateway ownership;
- hosted runtime, general host-baseline implementation, external-resource IaC, or deployment implementation during the current bounded foundation deliverable.

## Delivery boundary

G1 is agent-in-progress in its discovery stage. Its bounded operational
implementations are Ansible discovery, the executed two-package dependency
bootstrap, the executed group-scoped k3s administrator access playbook, the
executed user-scoped kubectl client-defaults playbook, the executed single-node
reboot recovery playbook, and the executed temporary NetworkPolicy probe under
`ansible/`. Effective-user readability, warning-free
fresh-session cluster listing, both idempotence checks, SSH/Tailscale return, Ready
node, and kubeconfig recovery passed.
Python is used for offline contract tests and forty exact-scope Ansible action
plugins, one backup-only strategy plugin, and two focused library modules. These
reviewed focused guards enforce approved mutation, validation, cryptographic, and
task-selection boundaries; no general-purpose operational Python or infrastructure
collector exists. One
approved non-elevated check/diff run produced
a locally reviewed host report. A separately approved playbook directly requested
only `python3-kubernetes` and `python3-jsonpatch`; apt installed 37 packages including
dependencies, and post-install imports plus all nine then-current exact Kubernetes
queries pass. The extended elevated report confirms the datastore, curated
device/storage indicators, local-path behavior, and zero current PV/PVC objects
without touching the unmounted disk. It did not capture a Kubernetes version and
used `shared-data` as its fifth PVC scope. The separately approved schema-v3 rerun
passed with only the ignored local report changed. Human review confirmed kubelet
`v1.36.2+k3s1`, all 15 bounded queries available, and the exact `shared-services`
PVC query available with count zero. The first attempt omitted the ignored local
inventory and stopped unreachable before discovery; operational commands now require
it explicitly. The separate
generated-name functional probe subsequently passed all live phases and exact-UID
cleanup without Namespace create/delete. The locked local
environment passes syntax and lint. A separate source-only, check-only k3s
datastore/encryption preflight now has a canonical wrapper, exact elevation and
one-host/check/diff gates, fixed read-only argv under `no_log`, strict fail-closed
parsers, a deterministic mode-`0600` controller artifact, and synthetic disclosure
fixtures. A separately approved live read-only run passed at `ok=45 changed=1`,
writing only the ignored sanitized artifact with unknown datastore/encryption stages;
it performed no host, backup, restore, encryption, cluster, or Secret mutation. A gated checksum-pinned OpenTofu CLI installer and Cloudflare-only source are
implemented. The installer’s historical host check passed; the first live run
created only exact managed parent and empty protected state directories before
host-side GitHub retrieval failed. The reviewed controller-transfer recovery then
passed check, live installation, and a `changed=0` rerun without host egress. Later
approved state import, encrypted backup/readback, independent-key restore rehearsal,
and existing-route management supersede that earlier empty-directory checkpoint.
The PROD route remains pending its exact two-change plan and separate provider/
public-cutover approvals. Exact `argocd` and `platform-edge` Namespace
manifests and a bounded present-only Ansible bootstrap are implemented. Its
separately approved non-passthrough wrapper check passed at
`ok=19 changed=1 unreachable=0 failed=0 skipped=2` and predicted changes for exactly
those two items; check mode created nothing and skipped live post-state tasks by
design. The separately approved first apply passed at
`ok=21 changed=1 unreachable=0 failed=0 skipped=0`, changed exactly both Namespace
items, and verified exact identity, reviewed labels, Active phase, and k3s/Tailscale
health. During the separately approved idempotence checkpoint, an initial invocation
stopped before service preflight and Kubernetes reconciliation on failed local sudo
authentication at `ok=10 changed=0 unreachable=0 failed=1 skipped=0`; it made no
mutation and proved no idempotence. The retry passed at
`ok=21 changed=0 unreachable=0 failed=0 skipped=0`, with both exact reconciliation
items `ok`, exact post-state identity/label/Active assertions passing, and
k3s/Tailscale running before and after. A distinct exact present-only
[foundation Namespace bootstrap](../../runbooks/foundation-namespace-bootstrap.md)
is now implemented for `shared-services` without modifying or reopening the
historical wrapper. Its check, separately approved first apply, and separately
approved idempotence passed, with final `changed=0`. A separate guarded
[CristexHub DEV Namespace bootstrap](../../runbooks/cristexhub-dev-namespace-bootstrap.md)
is source-ready for only `cristexhub-dev`; its separately approved check passed with
one exact predicted change and no mutation. Its first apply passed at
`ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created/verified only that exact
Namespace, and preserved service health. Idempotence passed at
`ok=22 changed=0 unreachable=0 failed=0 skipped=0`; the checkpoint is complete. No policy/workload/Secret/PVC/route is included; the `cristexhub-prod` Namespace is Active/idempotent, while later PROD resources remain absent and blocked. The superseded `platform-secrets`/`platform-identity`
source was never run; this source correction does not claim a live rename or
deletion. Guarded Infisical and private Argo CD runtime closures are now applied
and idempotent. The private CristexHub repository credential and value-free DEV
AppProject/Application registration are live without synchronization; Argo renders
18 objects at the pinned revision. PostgreSQL, MongoDB, RabbitMQ, Keycloak,
cloudflared, their bounded Secrets/Services/policies/PVCs, and the approved Keycloak
route are live under their recorded checkpoints. CristexHub application workloads,
its runtime Secret, DEV public route, and every PROD workload remain absent. The source-only
[shared database architecture](../../runbooks/shared-database-architecture.md)
records exact engine/consumer closure, deny-first authorization, private exposure,
and Infisical value ownership. Hash-bound present-only PostgreSQL and standalone
MongoDB object closures now exist, while Secret materialization, check/apply,
provisioning, recovery, and every runtime promotion gate remain blocked. A source-only
[Reactive Resume hosted architecture](../../runbooks/reactive-resume-hosted-architecture.md)
includes private DEV in the MVP and reserves separate DEV/PROD PostgreSQL and OIDC
scopes while image, callback, Secret, object, recovery, and runtime gates remain
false. One SHA-pinned read-only infrastructure CI workflow can neither publish nor
deploy; exact source-only run `31311995461` passed commit
`e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`. A source-only
[Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
retains historical chart, signature/hash-binding, image, and online/static readiness
evidence for chart `10.3.0` and app `v3.5.0`. The release record selects that pair and the
[guarded Argo CD bootstrap](../../runbooks/argocd-hardened-design.md) now promotes an
exact 32-object committed-manifest closure: three Ansible-owned CRDs plus 29 private
namespaced objects—one deny-all default AppProject and 28 objects for controller,
repo-server, server, and standalone Redis.
ApplicationSet runtime, Dex, notifications, commit server, cluster RBAC, public
exposure, PVCs, hooks, metrics Services, and Secret objects are absent. Exact
precreated Infisical-owned Secret metadata is mandatory. Offline hash, render,
security, RBAC, NetworkPolicy, wrapper/action, syntax, and lint contracts pass; no
live check/apply/idempotence, node pull, login/TLS, traffic, recovery, or Git sync
proof is claimed. The
[source-only Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md)
selects the shared self-hosted identity architecture target, direct Argo OIDC with
Dex absent, private administration, a dedicated Keycloak database/role on the shared
PostgreSQL engine, recovery, Infisical-owned client secret, and object-by-object
handoff directions. The release record selects
Keycloak `26.7.1`, PostgreSQL `17.10`, realm, issuer, default theme, clients, and
group policy only for offline source authoring; the exact CristexHub DEV and PROD
browser callbacks/origins are source-selected, while Reactive Resume/Argo
callbacks/origins, trust/recovery, credentials, routes, executable source, and
runtime remain
**NOT RUN/BLOCKED**. A separate source-only
[cloudflared candidate provenance record](../../runbooks/cloudflared-candidate-provenance.md)
records release `2026.7.3`, unsigned source, immutable linux/amd64 image,
token-file, readiness/health, and edge-transport evidence. It is **CANDIDATE — NOT
DEPLOYABLE — NOT SELECTED**, runtime is **NOT RUN**, and adds no OpenTofu resource,
Kubernetes object, secret, route, or deployment source. Publisher trust, image
assurance/availability, container hardening, Infisical token recovery, OpenTofu
state/resource gates, Argo handoff, exact DNS/Traefik/edge policy, route approval,
single-node risk, soak, and runtime approvals remain blocked. A third source-only
[Infisical Operator candidate provenance record](../../runbooks/infisical-operator-candidate-provenance.md)
distinguishes latest source release `v0.11.8`, whose matching public Cloudsmith chart
entry/archive and Docker Hub image tag were not observed during the bounded capture,
from the version-aligned `v0.11.7` set. The inert
[privileged-prerequisites inventory](../../runbooks/infisical-operator-privileged-prerequisites-design.md)
remains historical evidence. The [implementation profile](../../runbooks/infisical-operator-implementation-profile.md)
binds the official source, and the guarded
[idle bootstrap](../../runbooks/infisical-operator-bootstrap.md) promotes exactly 44
value-free objects: six namespaced CRDs, six native admission policies/bindings,
exact namespaced RBAC, one metrics-off controller, authenticated TLS Squid, and eight
NetworkPolicies. The archive remains quarantined and is not a runtime input. The
44-object closure passed guarded check/apply/post-check/idempotence at
`ok=30 changed=1`, `ok=35 changed=1`, `ok=30 changed=0`, and `ok=35 changed=0`.
Broader live admission/RBAC/traffic and every credential-bearing PROD phase remain
**NOT RUN/BLOCKED**. The idle closure contains no Infisical CR, but a separate
source-only
[Argo CD Secret materialization seam](../../runbooks/infisical-argocd-secret-materialization.md)
freezes one same-Namespace Universal Auth reference, one Connection/Auth/StaticSecret
closure, exactly three orphaned targets, additive exact-name Secret/workload-list
RBAC, and fail-closed admission. It adds no credential Secret or value; source
check/apply, sync, target values, and runtime remain **NOT RUN/BLOCKED**. Kubernetes
and application PROD scope plus the self-hosted Infisical server remain absent; the
fixed Infisical Cloud environment slug `prod` is only a licensing-constrained source
identifier and does not activate those scopes.
At the earlier source-only capture, provider initialization, state, plan, and apply
were unrun; that sentence is historical and is superseded by the protected five-
resource state/import and backup/restore checkpoint above. The pending PROD route
still has no provider apply. Beyond the separately recorded protected state and
existing-route checkpoints, no PROD Tunnel-config/DNS mutation or public cutover has
run. CristexHub local runtime assets remain external application-repository concerns
and are not copied here.

A guarded host-transfer boundary pins rclone `1.71.1`: controller cache verification
and transfer install a root-owned host payload, rollback removes only its selector,
and a separate flow permits only the existing encrypted proxy bundle/checksum through
fixed immutable host `copyto` uploads/readbacks. The Mac keeps age identity and
plaintext verification. Secret mutation requires an exact `drive-verified` marker.
Installer check passed twice; two applies stopped before host mutation, with the
second retaining only the exact ignored controller cache. Both discovered source
defects pass offline regressions. A fresh check passed at
`ok=25 changed=1 failed=0`; the separately approved corrected install passed at
`ok=34 changed=4 failed=0`, selected verified rclone `1.71.1`, and preserved
k3s/Tailscale health. The separately approved idempotence apply passed at
`ok=32 changed=0 failed=0`. Host OAuth then completed through a private callback
tunnel with config/token only on the host. Transfer check passed at
`ok=26 changed=0 failed=0`; apply stopped on unsupported `--local-umask` after exact
encrypted staging, and approved cleanup removed it at `ok=26 changed=1 failed=0`.
After one transient host-offline stop, transfer check/apply passed at
`ok=26 changed=0` and `ok=39 changed=7`; exact proxy Secret bootstrap passed at
`ok=15 changed=1`. Infisical Operator check/apply/idempotence then passed. Universal
Auth, Argo, and database-backup/runtime remain **NOT RUN/BLOCKED**; see
[`rclone-host-transfer.md`](../../runbooks/rclone-host-transfer.md).

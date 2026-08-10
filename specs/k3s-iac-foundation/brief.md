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

## Approved direction

- Minimal Ansible owns the Debian host/k3s baseline and is selected as the future bounded bootstrap installer for exact foundational Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, one self-hosted Keycloak, privileged CRDs/cluster RBAC, and Keycloak realm/client/group reconciliation. Each component needs separate source and check/apply/idempotence approvals.
- OpenTofu owns Cloudflare and GitHub resources, not Kubernetes objects.
- Argo CD owns namespaced desired state only after Ansible stops reconciling the exact object set and registration/adoption, successful sync, and managed-field evidence pass; dual reconciliation is forbidden.
- Infisical Cloud initially owns runtime secret values; only its Kubernetes Operator is bootstrapped and self-hosting Infisical is out of scope for the foundation.
- One future self-hosted Keycloak shared by CristexHub, Reactive Resume, and Argo CD is selected as the identity target. Keycloak `26.7.1`, PostgreSQL `17.10`, realm `cristexhub`, the stable issuer, direct Argo OIDC, and value-free authorization policy are selected only for offline source authoring; executable source and runtime remain blocked. Keycloak authenticates/emits groups, Argo RBAC authorizes Argo actions, and Kubernetes RBAC constrains controllers.
- GitHub Actions owns source validation and future immutable private-GHCR publication but never deploys. Current infrastructure/application workflows are SHA-pinned read-only CI only; package publication is disabled pending trusted build inputs and digest evidence.
- Bundled k3s Traefik remains the sole ingress controller.
- DEV and administration remain private through host Tailscale.
- Only approved PROD application routes become public through Cloudflare Tunnel.
- Exact [CristexHub DEV Namespace source](../../runbooks/cristexhub-dev-namespace-bootstrap.md) exists with four approved labels. Its check passed at `ok=20 changed=1 unreachable=0 failed=0 skipped=2` without mutation. The first apply passed at `ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created/verified the exact Namespace, and preserved service health; idempotence is NOT RUN. `cristexhub-prod` remains absent and source-blocked until DEV validation, recovery, and soak.
- `platform-edge` is reserved for cloudflared. Future `shared-services` placement is the Infisical Cloud Operator, a separate Keycloak deployment, one general PostgreSQL engine, one shared MongoDB engine, and one shared RabbitMQ engine; the exact Namespace now exists after passed check/first apply/idempotence, with final `changed=0`, while every component runtime remains NOT RUN. CristexHub DEV/PROD use dedicated scopes on both shared engines; Keycloak and environment-local Reactive Resume DEV/PROD use dedicated PostgreSQL logical databases, owner roles, credentials, migrations, and backup scopes. The canonical database, RabbitMQ, backup, and Reactive Resume policies are value-free and runtime-blocked. RabbitMQ DEV/PROD consumers have dedicated vhost/user/permission/limit/recovery scopes; future consumers require reviewed exact changes. Backup access is private/authenticated through a metadata-only catalog and non-destructive encrypted off-node copy direction. The database source profile fixes NVMe `local-path`, 40/80 GiB PVCs, bounded resources, standard private Services/TLS, daily archives, 14-day retention, RPO 24h, and RTO 4h; images, RabbitMQ storage/ports, exact destination identities, implementation, and recovery proof remain unselected.
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
Python is used only for offline contract tests. One
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
environment passes syntax and lint. A gated checksum-pinned OpenTofu CLI installer
and Cloudflare-only zero-resource source scaffold are implemented. The approved
host check passed; the first live run created only the exact managed parent and
empty protected state directories before host-side GitHub retrieval failed. The
reviewed controller-transfer recovery then passed check, live installation, and a
`changed=0` rerun without host egress. Exact `argocd` and `platform-edge` Namespace
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
Namespace, and preserved service health; idempotence is NOT RUN. No policy/workload/
Secret/PVC/route is included, and PROD remains absent. The superseded `platform-secrets`/`platform-identity`
source was never run; this source correction does not claim a live rename or
deletion. Argo CD, cloudflared, Infisical Operator,
Keycloak, PostgreSQL, MongoDB, Secrets, workloads, Services, policies, PVCs, and
routes remain unrun. The source-only
[shared database architecture](../../runbooks/shared-database-architecture.md)
records exact engine/consumer closure, deny-first authorization, private exposure,
Infisical value ownership, and closed promotion gates without adding executable
objects. A source-only
[Reactive Resume hosted architecture](../../runbooks/reactive-resume-hosted-architecture.md)
includes private DEV in the MVP and reserves separate DEV/PROD PostgreSQL and OIDC
scopes while image, callback, Secret, object, recovery, and runtime gates remain
false. One SHA-pinned read-only infrastructure CI workflow can neither publish nor
deploy; exact source-only run `31311995461` passed commit
`e200efd8f294a04df8d3c5ea84fd90b8a24e01d1`. A source-only
[Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
retains historical chart, signature/hash-binding, image, and online/static readiness
evidence for chart `10.3.0` and app `v3.5.0`. The release record selects that pair
only for offline source authoring; it remains **NOT DEPLOYABLE** and adds no values or
Kubernetes object source. The exact 44-document render reproduced at Kubernetes capability `1.36.2`,
stable upstream API registration screened successfully, and controller-side image
closure was reachable. Exact k3s admission/runtime and node pullability remain
unproven; wildcard/broad RBAC, ingress-only/unrestricted-egress policy, signing and
image trust, generated/internal Secret recovery, private Git secret-zero, Namespace
adoption, trust/soak acceptance, and all runtime approvals remain blocked. The
[source-only Argo CD hardened design](../../runbooks/argocd-hardened-design.md)
accepts only a private ClusterIP/loopback-port-forward direction, retained quiescent
ApplicationSet, supplemental default-deny with an explicit broad ports-only
`443`/`6443` weakness, phased least privilege, an exact one-repository read-only
GitHub App credential shape, value-free Infisical custody, disabled Redis initializer,
and two adoption Applications. It remains design-only, adds no deployable source,
and records Ansible as the selected bounded bootstrap installer and privileged
lifecycle owner while leaving six controller-closure, foundation-Namespace-runtime,
resource-inventory, Universal-Auth-recovery, adoption-apply, and selected-OIDC
activation decisions open. The
[source-only Keycloak OIDC bootstrap design](../../runbooks/keycloak-oidc-bootstrap-design.md)
selects the shared self-hosted identity architecture target, direct Argo OIDC with
Dex absent, private administration, a dedicated Keycloak database/role on the shared
PostgreSQL engine, recovery, Infisical-owned client secret, and object-by-object
handoff directions. The release record selects
Keycloak `26.7.1`, PostgreSQL `17.10`, realm, issuer, default theme, clients, and
group policy only for offline source authoring; executable source, callbacks,
credentials, routes, recovery proof, and runtime remain **NOT RUN/BLOCKED**. A separate source-only
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
from the version-aligned `v0.11.7` set. The release record selects `v0.11.7` only
for offline source authoring and Universal Auth as direction; it remains **NOT
DEPLOYABLE**, runtime is **NOT RUN/BLOCKED**, and no CRD, Kubernetes object,
credential, or Secret source was added. The inert
[privileged-prerequisites inventory](../../runbooks/infisical-operator-privileged-prerequisites-design.md)
now records the seven raw CRD templates and manager/metrics/user-RBAC defects without
promoting a valid object, permission, values file, render, or Ansible entrypoint. The
target kubelet is now captured, but chart/CRD/API compatibility, signer/build trust,
dedicated Namespace, scoped RBAC, Argo handoff, secret-zero/recovery, traffic policy,
single-node risk, and runtime approvals remain blocked.
Provider initialization, state, plan, and apply also remain unrun.
Beyond the bounded public-source evidence reads, this deliverable performs no host
mutation, authenticated Cloudflare/GitHub/Infisical/registry operation, database,
storage, backup, DNS, tunnel, or data operation. CristexHub local runtime assets remain
external application-repository concerns and are not copied here.

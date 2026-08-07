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

- Minimal Ansible owns the Debian host and k3s baseline.
- OpenTofu owns Cloudflare and GitHub resources, not Kubernetes objects.
- Argo CD is the intended persistent Kubernetes reconciler. Its ownership is not effective until installation, Namespace adoption or Application registration, and successful sync evidence; a future-owner label alone is not a handoff.
- Infisical Cloud initially owns runtime secret values; self-hosting is out of scope for the foundation.
- GitHub Actions validates/builds and publishes immutable images to private GHCR.
- Bundled k3s Traefik remains the sole ingress controller.
- DEV and administration remain private through host Tailscale.
- Only approved PROD application routes become public through Cloudflare Tunnel.
- Application namespaces are `cristexhub-dev` and `cristexhub-prod`.
- `shared-services` hosts shared PostgreSQL, MongoDB, and any retained RabbitMQ, with separate databases, principals, credentials, migrations, virtual hosts, limits, and backups per environment.
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
- application source, local Compose, Keycloak theme, or Browserless gateway ownership;
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
k3s/Tailscale running before and after. Argo CD, cloudflared, Infisical, Secrets,
workloads, Services, and routes remain unrun. A source-only
[Argo CD candidate provenance record](../../runbooks/argocd-candidate-provenance.md)
records chart, captured signature/hash-binding, image, and curated online/static
readiness evidence for chart `10.3.0` and app `v3.5.0`, but is explicitly **CANDIDATE
— NOT DEPLOYABLE — NOT SELECTED**. It adds no chart, values, or Kubernetes object
source. The exact 44-document render reproduced at Kubernetes capability `1.36.2`,
stable upstream API registration screened successfully, and controller-side image
closure was reachable. Exact k3s admission/runtime and node pullability remain
unproven; wildcard/broad RBAC, ingress-only/unrestricted-egress policy, signing and
image trust, generated/internal Secret recovery, private Git secret-zero, Namespace
adoption, human selection/soak, and all runtime approvals remain blocked. The
[source-only Argo CD hardened design](../../runbooks/argocd-hardened-design.md)
accepts only a private ClusterIP/loopback-port-forward direction, retained quiescent
ApplicationSet, supplemental default-deny with an explicit broad ports-only
`443`/`6443` weakness, phased least privilege, an exact one-repository read-only
GitHub App credential shape, value-free Infisical custody, disabled Redis initializer,
and two adoption Applications. It is **DESIGN ONLY**, adds no deployable source, and
leaves its exact five installer/ownership, future-Namespace, resource-inventory,
Infisical-recovery, and adoption-apply decisions open. A separate source-only
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
from the last observed version-aligned `v0.11.7` set. Both are **CANDIDATE — NOT
DEPLOYABLE — NOT SELECTED**, runtime is **NOT RUN**, and no chart, CRD, Kubernetes
object, credential, or Secret source was added. The target kubelet is now captured,
but chart/CRD/API compatibility, signer/build trust, dedicated Namespace, scoped
RBAC, Argo handoff, secret-zero/recovery, traffic policy,
single-node risk, and runtime approvals remain blocked.
Provider initialization, state, plan, and apply also remain unrun.
Beyond the bounded public-source evidence reads, this deliverable performs no host
mutation, authenticated Cloudflare/GitHub/Infisical/registry operation, database,
storage, backup, DNS, tunnel, or data operation. CristexHub local runtime assets remain
external application-repository concerns and are not copied here.

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
- Argo CD owns all Kubernetes desired state.
- Infisical Cloud initially owns runtime secret values; self-hosting is out of scope for the foundation.
- GitHub Actions validates/builds and publishes immutable images to private GHCR.
- Bundled k3s Traefik remains the sole ingress controller.
- DEV and administration remain private through host Tailscale.
- Only approved PROD application routes become public through Cloudflare Tunnel.
- Application namespaces are `cristexhub-dev` and `cristexhub-prod`.
- `shared-data` hosts shared PostgreSQL and MongoDB engines with separate databases, principals, credentials, migrations, and backups per environment.
- Redis remains per environment; shared RabbitMQ uses separate users, virtual hosts, and limits if retained after discovery.

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
bootstrap, the executed group-scoped k3s administrator access playbook, and the
executed user-scoped kubectl client-defaults playbook, and executed single-node
reboot recovery playbook under `ansible/`. Effective-user readability, warning-free
fresh-session cluster listing, both idempotence checks, SSH/Tailscale return, Ready
node, and kubeconfig recovery passed.
Python is used only for offline contract tests. One
approved non-elevated check/diff run produced
a locally reviewed host report. A separately approved playbook directly requested
only `python3-kubernetes` and `python3-jsonpatch`; apt installed 37 packages including
dependencies, and post-install imports plus all nine exact
Kubernetes queries pass. The elevated report confirms the datastore and curated
cluster indicators but not CNI behavior or NetworkPolicy enforcement. The locked
local environment passes syntax and lint. This deliverable performs no other host
mutation, Cloudflare, GitHub, Infisical,
registry, database, storage,
backup, DNS, tunnel, or data operation. CristexHub local runtime assets remain
external application-repository concerns and are not copied here.

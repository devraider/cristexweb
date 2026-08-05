# Brief — G1: k3s IaC foundation

## Problem

CristexHub has production-capable service images in its application repository but
no hosted orchestration supported by this infrastructure repository. The target
server already runs single-node k3s, while the desired host, external-resource,
GitOps, secret, data, backup, and recovery contracts are not yet implemented.

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
- hosted runtime, mutating host baseline, external-resource IaC, or deployment implementation during the current read-only discovery deliverable.

## Delivery boundary

G1 is agent-in-progress in its read-only discovery stage. The only operational
implementation is the Ansible discovery playbook under `ansible/`; Python is used
only for offline contract tests. One explicitly approved non-elevated check/diff run
reached the server and produced a locally reviewed curated host report. The pinned,
locked project-local `uv` environment passed syntax and lint. No become or cluster
query occurred. This deliverable performs no Cloudflare, GitHub, Infisical,
registry, database, storage,
backup, DNS, tunnel, or data operation. CristexHub local runtime assets remain
external application-repository concerns and are not copied here.

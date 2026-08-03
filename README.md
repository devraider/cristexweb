# Cristex infrastructure

## Status

This is a documentation-only infrastructure repository. It owns the target design
for future host automation, Cloudflare/GitHub IaC, Kubernetes GitOps, and recovery
runbooks. It has no implemented runtime today and makes no claim that a hosted
environment, deployment, DNS route, tunnel, database, backup, or recovery process
exists.

CristexHub application source, local Compose assets, Keycloak theme, and Browserless
gateway remain in the separate CristexHub application repository. They are not
copied or supported as this repository's runtime.

## Read first

1. [`AGENTS.md`](AGENTS.md) — authoritative ownership and safety rules.
2. [`architecture-plan.md`](architecture-plan.md) — target design, staged delivery, gates, rollback, and unresolved decisions.
3. [`specs/k3s-iac-foundation/brief.md`](specs/k3s-iac-foundation/brief.md) — scoped foundation milestone.
4. [`specs/k3s-iac-foundation/testcases.md`](specs/k3s-iac-foundation/testcases.md) — validation contract and honest current results.

## Selected direction

| Concern | Selected direction |
|---|---|
| Runtime target | Existing single-node k3s host; downtime accepted |
| Private access | Host Tailscale for SSH/k3s administration; explicit private service exposure only when required |
| Public access | Cloudflare Tunnel for approved PROD application routes only |
| Ingress | Bundled k3s Traefik, retained as the sole ingress controller |
| Host configuration | Minimal Ansible |
| External resources | OpenTofu for Cloudflare and GitHub only |
| Cluster reconciliation | Argo CD for all in-cluster desired state |
| Secrets | Infisical Cloud initially; no plaintext values in Git or OpenTofu state |
| CI and images | GitHub Actions and private GHCR images addressed immutably |
| Environments | `cristexhub-dev` and `cristexhub-prod` |
| Shared data | One PostgreSQL engine and one MongoDB engine in `shared-data`, with separate environment databases, principals, credentials, and backups |
| Other data services | Redis per environment; RabbitMQ may be shared only with separate users/vhosts and limits |
| Backups | Application-consistent local dumps plus encrypted off-host copy; restore required before PROD |

## Proposed future layout

The implementation directories below are intentionally not created by this
planning milestone:

```text
ansible/
opentofu/
  cloudflare/
  github/
kubernetes/
  bootstrap/
  clusters/crtxweb/
  platform/
  apps/cristexhub/base/
  apps/cristexhub/overlays/dev/
  apps/cristexhub/overlays/prod/
runbooks/
```

Kustomize is intended for first-party application overlays. Helm is reserved for
selected third-party components. After a bounded bootstrap, Argo CD owns all
in-cluster desired state.

## Repository hygiene

The protective [`.gitignore`](.gitignore) must remain in force before future tools
run. It excludes local OpenTofu/Terraform state and plans, Ansible runtime data,
kubeconfigs, local credentials/keys, and generated secret material. It deliberately
does not ignore `.terraform.lock.hcl`; lock files are reviewed and committed.

## Non-goals for the foundation

- multi-node or high availability;
- Longhorn, service mesh, policy engines, or autoscaling platforms;
- self-hosted registry, Infisical, or GitHub runner;
- a second ingress controller;
- automated production promotion;
- public DEV or public administrative dashboards;
- migration of existing data or any external/platform change.

## Safe validation

This planning milestone permits only offline repository checks such as Markdown
link validation, terminology and traceability checks, forbidden-artifact scans,
and:

```bash
git diff --check
git diff --cached --quiet
```

The exact foundation validation command and actual result are recorded in
[`testcases.md`](specs/k3s-iac-foundation/testcases.md). Provider-backed plans,
server access, and all mutating commands require a later approved task and gate.

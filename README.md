# Cristex infrastructure

## Status

The only implemented code in this repository is a local, read-only Python inventory
collector and its offline unit tests. The collector gathers an allowlisted host and
k3s discovery report; it does not configure or deploy anything.

This repository otherwise owns the target design for future host automation,
Cloudflare/GitHub IaC, Kubernetes GitOps, and recovery runbooks. No hosted runtime,
Ansible playbook, OpenTofu configuration, Kubernetes manifest, Helm chart, workflow,
deployment, DNS route, tunnel, database, backup, or recovery process exists here.
Debian plus Ansible remains the approved owner for future host configuration.

CristexHub application source, local Compose assets, Keycloak theme, and Browserless
gateway remain in the separate CristexHub application repository. They are not
copied or supported as this repository's runtime.

## Read first

1. [`AGENTS.md`](AGENTS.md) — authoritative ownership and safety rules.
2. [`architecture-plan.md`](architecture-plan.md) — target design, staged delivery, gates, rollback, and unresolved decisions.
3. [`specs/k3s-iac-foundation/brief.md`](specs/k3s-iac-foundation/brief.md) — scoped foundation milestone.
4. [`specs/k3s-iac-foundation/testcases.md`](specs/k3s-iac-foundation/testcases.md) — validation contract and honest current results.

## Local inventory collector

List the immutable read-only checks without executing them:

```bash
python3 -m tools.collect_inventory --list-checks
```

After reviewing the allowlist, collect locally to an ignored report name whose
parent directory already exists:

```bash
python3 -m tools.collect_inventory --local --sanitized-output inventory.local.sanitized.json
```

The collector:

- accepts no command string or arbitrary command arguments and never uses a shell;
- executes only static read-only argv tuples with a fixed minimal environment,
  timeouts, and output bounds;
- never invokes `sudo`; no allowlisted command directly displays Kubernetes Secret
  content, kubeconfig content, k3s token/config content, process environments,
  environment secrets, or arbitrary files;
- may implicitly consume the normal k3s/kubectl authentication and kubeconfig needed
  to query the API, but does not intentionally emit that authentication material;
- disables kubectl's on-disk discovery cache with an explicit empty cache directory;
- records unavailable, denied, failed, and timed-out checks rather than treating a
  partial non-root inventory as collector failure;
- captures interface, kube-system, DNS, Traefik, HelmChart, and NetworkPolicy-object
  indicators, but does not prove CNI or NetworkPolicy enforcement;
- sanitizes known host/user, email, IP, MAC, UUID/filesystem/LVM ID,
  credential-assignment, and bearer patterns on a best-effort basis;
- atomically writes only the requested JSON report, with mode `0600`, and refuses a
  symlink destination.

The report includes a prominent warning because sanitization cannot prove that all
sensitive or identifying data was removed. A human must review the complete report
before sharing or committing it. Raw and local report filenames are ignored by
[`.gitignore`](.gitignore); intentionally authored sanitized documentation is not
blanket-ignored.

A normal non-root run is valid and may be partial. Running the collector through
`sudo` would expose additional root-readable metadata, requires separate explicit
operator approval, and **has not occurred**. When separately approved and invoked
through `sudo`, the collector hands the report to the invoking UID/GID after its
secure write. This implementation task did not access the actual server or cluster
and did not capture an inventory report.

## Selected direction

| Concern | Selected direction |
|---|---|
| Runtime target | Existing single-node k3s host; downtime accepted |
| Private access | Host Tailscale for SSH/k3s administration; explicit private service exposure only when required |
| Public access | Cloudflare Tunnel for approved PROD application routes only |
| Ingress | Bundled k3s Traefik, retained as the sole ingress controller |
| Host configuration | Minimal Ansible on Debian |
| External resources | OpenTofu for Cloudflare and GitHub only |
| Cluster reconciliation | Argo CD for all in-cluster desired state |
| Secrets | Infisical Cloud initially; no plaintext values in Git or OpenTofu state |
| CI and images | GitHub Actions and private GHCR images addressed immutably |
| Environments | `cristexhub-dev` and `cristexhub-prod` |
| Shared data | One PostgreSQL engine and one MongoDB engine in `shared-data`, with separate environment databases, principals, credentials, and backups |
| Other data services | Redis per environment; RabbitMQ may be shared only with separate users/vhosts and limits |
| Backups | Application-consistent local dumps plus encrypted off-host copy; restore required before PROD |

## Proposed future layout

The IaC and runtime directories below are intentionally not created by this Stage 1
collector deliverable:

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

The protective [`.gitignore`](.gitignore) excludes local inventory reports,
OpenTofu/Terraform state and plans, Ansible runtime data, kubeconfigs, local
credentials/keys, and generated secret material. It deliberately does not ignore
`.terraform.lock.hcl`; lock files are reviewed and committed.

## Non-goals for the foundation

- multi-node or high availability;
- Longhorn, service mesh, policy engines, or autoscaling platforms;
- self-hosted registry, Infisical, or GitHub runner;
- a second ingress controller;
- automated production promotion;
- public DEV or public administrative dashboards;
- migration of existing data or any external/platform change.

## Safe offline validation

This deliverable permits offline repository and collector checks only:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q tools tests
python3 -m tools.collect_inventory --list-checks
git diff --check
git diff --cached --quiet
```

The exact validation block and actual results are recorded in
[`testcases.md`](specs/k3s-iac-foundation/testcases.md). No collector run, provider
operation, server access, or mutating command is part of this validation.

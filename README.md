# Cristex infrastructure

## Status

The repository's bounded Ansible implementation contains discovery, the executed
two-package module bootstrap, and an executed group-scoped k3s administrator
access playbook under [`ansible/`](ansible/). Effective-user readability,
fresh-session cluster listing, and second-run idempotence have passed. An approved
user-scoped client-defaults playbook will remove k3s multicall warnings without
exposing server configuration; its runtime and recovery verification remain pending.
Discovery gathers
curated host indicators with built-ins and exact Kubernetes kinds with
`kubernetes.core.k8s_info`. No general host baseline or deployment exists. Python
is used only for offline contract tests, not infrastructure automation.

One approved non-elevated check/diff run produced the ignored local report. An
approved elevated attempt identified missing remote Python dependencies. The
bounded two-package Ansible bootstrap was reviewed and installed; post-install
imports and all nine exact Kubernetes queries now pass. The report confirms the
k3s datastore and curated cluster indicators. Hosted runtime,
OpenTofu configuration, Kubernetes manifest, Helm chart, workflow, deployment, DNS
route, tunnel, database, backup, and recovery remain unexecuted. Debian plus
Ansible is the host-management owner.

CristexHub application source, local Compose assets, Keycloak theme, and Browserless
gateway remain in the separate CristexHub application repository.

## Read first

1. [`AGENTS.md`](AGENTS.md) — authoritative ownership and safety rules.
2. [`architecture-plan.md`](architecture-plan.md) — target design, staged delivery, gates, rollback, and unresolved decisions.
3. [`ansible/README.md`](ansible/README.md) — discovery contract and approved command shape.
4. [`specs/k3s-iac-foundation/testcases.md`](specs/k3s-iac-foundation/testcases.md) — validation contract and honest current results.

## Read-only Ansible discovery

The committed inventory contains only the SSH alias `crtxweb`; it contains no IP,
user, key, credential, or become secret. The playbook:

- refuses to run without `--check --diff`, an explicit `--limit`, and exactly one
  selected host;
- defaults to `become: false`;
- requires two explicit approval variables before narrowly scoped elevated k3s
  queries;
- uses `setup`, `service_facts`, and `stat` for host facts and
  `kubernetes.core.k8s_info` for exact resource kinds;
- never uses shell, raw, script, command, an embedded command allowlist, or automatic
  dependency installation;
- never queries Secret, ConfigMap, Events, or a broad `all` resource set;
- marks raw facts and Kubernetes results `no_log`, disables persistent fact caching,
  and projects only curated fields;
- lets `k8s_info` load the normal root-only k3s kubeconfig for authentication, but
  never separately slurps, copies, registers, logs, or renders its content;
- writes one ignored controller-local JSON report, mode `0600`, with diff disabled
  and symlink refusal.

Listing NetworkPolicy and platform objects supplies configuration indicators only.
It does not prove CNI behavior or NetworkPolicy enforcement; those require later,
separately approved functional probes.

The approved non-elevated discovery run passed and its curated host report was
reviewed locally. It did not use become or query Kubernetes. Syntax and lint also
passed. Any further or elevated run still requires separate approval; command shapes
are documented in [`ansible/README.md`](ansible/README.md).

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

## Repository layout

```text
ansible/                 # discovery + two narrowly approved host changes
  inventory/
  playbooks/
  roles/read_only_discovery/
opentofu/                # future
kubernetes/              # future
runbooks/                # future
tests/                   # offline contract tests only
```

Only `ansible/` and `tests/` currently exist. Kustomize remains intended for
first-party application overlays; Helm is reserved for selected third-party
components. After a bounded bootstrap, Argo CD owns all in-cluster desired state.

## Repository hygiene

The protective [`.gitignore`](.gitignore) excludes local inventory reports,
OpenTofu/Terraform state and plans, Ansible runtime data, kubeconfigs, local
credentials/keys, and generated secret material. It deliberately tracks provider
lock files.

## Non-goals for the foundation

- multi-node or high availability;
- Longhorn, service mesh, policy engines, or autoscaling platforms;
- self-hosted registry, Infisical, or GitHub runner;
- a second ingress controller;
- automated production promotion;
- public DEV or public administrative dashboards;
- migration of existing data or any external/platform change.

## Project-local tool environment and validation

`uv sync --locked` creates the ignored `.venv/` from the committed `pyproject.toml`
and `uv.lock`. The pinned `kubernetes.core` collection is installed into the
ignored `ansible/.ansible/collections/` path. Nothing is installed on the inventory
host by this setup.

```bash
uv sync --locked
cd ansible
uv run ansible-galaxy collection install \
  -r requirements.yml \
  -p .ansible/collections
uv run ansible-playbook playbooks/discover.yml --syntax-check
uv run ansible-lint playbooks/discover.yml roles/read_only_discovery
cd ..
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
git diff --check
git diff --cached --quiet
```

The complete reproducible commands and actual results are recorded in
[`testcases.md`](specs/k3s-iac-foundation/testcases.md).

# Cristex infrastructure

## Status

The repository's bounded Ansible implementation contains discovery, the executed
two-package module bootstrap, an executed group-scoped k3s administrator access
playbook, an executed non-destructive storage-discovery increment, and an
executed temporary CNI/NetworkPolicy functional probe under
[`ansible/`](ansible/). The separately approved extended storage discovery and
functional probe both passed against the live host/cluster. The probe ran
with an independently verified digest-qualified linux/amd64 image and temporary Argo
ownership exception. The probe never creates or deletes a Namespace; generated names, two fixed ownership
labels, private mode-`0600` ledger recovery, fixed-kind read-only rediscovery, exact
UID preconditions, non-cascading `Orphan` deletion, and an `always` cleanup path
bound every temporary object. Effective-user readability,
fresh-session cluster listing, and second-run idempotence have passed. The executed
user-scoped client-defaults playbook removes k3s multicall warnings without exposing
server configuration. The separately approved one-reboot recovery playbook passed
with SSH/Tailscale return, running services, a Ready node, and preserved access.
Discovery gathers curated host indicators with built-ins and exact Kubernetes
kinds with `kubernetes.core.k8s_info`. The separately approved schema-v3 elevated
read-only rerun passed and projects only the existing curated Node name/cluster
scope and kubelet `v1.36.2+k3s1`; all 15 bounded queries were available and the exact
`shared-services` PVC query returned zero objects. A gated Ansible
playbook pins the OpenTofu CLI. Its
approved host check passed at `ok=27 changed=6 failed=0`; the first live attempt
stopped at `ok=21 changed=2 failed=1` because the host had no route to GitHub, after
creating only exact parent directories and the empty protected state directory. The
reviewed controller-transfer check then passed at `ok=33 changed=6 failed=0`, the
live recovery installed the verified CLI at `ok=39 changed=6 failed=0`, and the
second run converged at `ok=30 changed=0 failed=0` without requiring host egress.
The protected directory still contains no state file, and no provider operation or
external resource exists. The root `opentofu/` source is Cloudflare-only and has zero
resources. Committed Kubernetes source now contains only the `argocd` and
`platform-edge` Namespace manifests plus a gated Ansible bootstrap; runtime remains
NOT RUN and no Argo CD, cloudflared, Infisical, Secret, workload, Service, or route
exists. A [source-only Argo CD candidate provenance record](runbooks/argocd-candidate-provenance.md)
binds public chart, captured signature/hash-binding, image, ignored-render, and
bounded target-minor evidence while remaining explicitly **CANDIDATE — NOT
DEPLOYABLE — NOT SELECTED**. Kubernetes minor `1.36` passes Argo CD `3.5`'s official
tested-matrix and chart-semver screen, but exact k3s/runtime and rendered API/CRD
compatibility remain unproven. It adds no chart, values, or Kubernetes object source. A separate
[source-only cloudflared candidate provenance record](runbooks/cloudflared-candidate-provenance.md)
binds official release, unsigned source, immutable linux/amd64 image, token-file,
health, and edge-transport evidence. It is also **CANDIDATE — NOT DEPLOYABLE — NOT
SELECTED**, with runtime **NOT RUN**, and adds no OpenTofu resource, Kubernetes
object, secret, route, or deployment source. A third
[source-only Infisical Operator candidate provenance record](runbooks/infisical-operator-candidate-provenance.md)
distinguishes the incomplete public `v0.11.8` distribution observation from the last
observed version-aligned `v0.11.7` chart/source/image set. Both remain **CANDIDATE —
NOT DEPLOYABLE — NOT SELECTED**, runtime is **NOT RUN**, and no chart, CRD,
Kubernetes object, credential, or Secret source was added. The actual target is now
captured, but Infisical chart/CRD/API compatibility remains unproven. No general host
baseline or deployment exists. Python is used only for offline contract tests, not
infrastructure automation.

Approved non-elevated and extended elevated check/diff runs produced the ignored
local report. The extended report confirms the unmounted 1 TB rotational disk,
NVMe/root capacity, local-path behavior, and zero current PV/PVC objects without
identifying the unmounted filesystem or touching disk contents. That historical
live report queried `shared-data` as its fifth PVC scope and did not capture a
Kubernetes version. The approved schema-v3 rerun instead queried `shared-services`
and projected `status.nodeInfo.kubeletVersion` from the existing exact Node query.
Human review confirmed Kubernetes minor `1.36`; Argo CD `3.5` lists that minor in
its official tested matrix and chart `10.3.0` admits the exact target through its
semver gate. This is only target-minor screening, not k3s-specific runtime, rendered
API/CRD, trust, selection, or deployment evidence. An earlier
approved elevated attempt identified missing remote Python dependencies. The
bounded two-package Ansible bootstrap was reviewed and installed; post-install
imports and the prior nine exact Kubernetes queries pass. That report confirms the
k3s datastore and curated cluster indicators; it predates the extended StorageClass,
PV, and namespace-bounded PVC projection. Hosted runtime, OpenTofu provider initialization/state/plan/apply, persistent
Namespace runtime, Helm chart, workflow, deployment, DNS route, tunnel, database,
backup, and replacement recovery remain unexecuted. The
first replacement-host increment is documentation-only: it adds a secret-free
runbook and artifact register with fail-closed decision gates, not recovery
automation or runtime proof. Debian plus Ansible is the host-management owner.

CristexHub application source, local Compose assets, Keycloak theme, and Browserless
gateway remain in the separate CristexHub application repository.

## Read first

1. [`AGENTS.md`](AGENTS.md) — authoritative ownership and safety rules.
2. [`architecture-plan.md`](architecture-plan.md) — target design, staged delivery, gates, rollback, and unresolved decisions.
3. [`ansible/README.md`](ansible/README.md) — discovery contract and approved command shape.
4. [`runbooks/replacement-host-recovery.md`](runbooks/replacement-host-recovery.md) — replacement boundary, isolation gates, and decision-first recovery contract.
5. [`runbooks/argocd-candidate-provenance.md`](runbooks/argocd-candidate-provenance.md) — source-only, non-deployable Argo CD candidate evidence and blockers.
6. [`runbooks/cloudflared-candidate-provenance.md`](runbooks/cloudflared-candidate-provenance.md) — source-only, non-deployable cloudflared candidate evidence and blockers.
7. [`runbooks/infisical-operator-candidate-provenance.md`](runbooks/infisical-operator-candidate-provenance.md) — source-only, non-deployable Infisical Operator candidate evidence and blockers.
8. [`specs/k3s-iac-foundation/testcases.md`](specs/k3s-iac-foundation/testcases.md) — validation contract and honest current results.

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
- projects device/partition size and state without serials, UUIDs, addresses, mount
  sources/paths, or contents, plus exact StorageClass behavior fields and bounded
  PV/PVC placement metadata from five fixed PVC namespaces;
- lets `k8s_info` load the normal root-only k3s kubeconfig for authentication, but
  never separately slurps, copies, registers, logs, or renders its content;
- writes one ignored controller-local JSON report, mode `0600`, with diff disabled
  and symlink refusal.

Listing NetworkPolicy and platform objects supplies configuration indicators only;
the listings themselves do not prove enforcement. The separately gated functional
probe has now established bounded live evidence for current CNI behavior,
NetworkPolicy deny/selective-allow semantics, rollback, and cleanup.

The probe uses one existing fixed namespace, a selectorless ClusterIP service with
an explicit EndpointSlice, a hardened server Pod, and short-lived standalone client
Pods to prove baseline success, deny failure, selective
allow/deny, rollback success, and zero labeled residue. It uses no remote exec and
never creates or deletes a Namespace. Argo CD is the intended persistent Kubernetes
reconciler, with one separately gated Ansible exception limited to creating or
reconciling the committed `argocd` and `platform-edge` Namespaces with state present.
That exception has no delete path and remains NOT RUN. The completed temporary probe
exception used the verified image and explicit approvals documented in
[`ansible/README.md`](ansible/README.md); every future run requires fresh approvals
and a unique Run ID.

The approved non-elevated discovery run passed and its curated host report was
reviewed locally. It did not use become or query Kubernetes. Syntax and lint also
passed. The approved schema-v3 elevated rerun refreshed the ignored mode-`0600`
report without target mutation. Operational discovery must explicitly load the
ignored local inventory because the default inventory contains only the neutral
alias. Use this one-line zsh shape only after the required approval:

```zsh
cd /Users/paul/Projects/cristexweb/ansible && uv run ansible-playbook -i .ansible/inventory.local.yml playbooks/discover.yml --check --diff --limit crtxweb -e read_only_discovery_enable_elevated=true -e read_only_discovery_elevated_approved=true --ask-become-pass
```

Any further or elevated run still requires separate approval; complete command
contracts are documented in [`ansible/README.md`](ansible/README.md).

## Selected direction

| Concern | Selected direction |
|---|---|
| Runtime target | Existing single-node k3s host; downtime accepted |
| Private access | Host Tailscale for SSH/k3s administration; explicit private service exposure only when required |
| Public access | Cloudflare Tunnel for approved PROD application routes only |
| Ingress | Bundled k3s Traefik, retained as the sole ingress controller |
| Host configuration | Minimal Ansible on Debian |
| External resources | OpenTofu for Cloudflare and GitHub only |
| Cluster reconciliation | Bounded Ansible bootstrap for only `argocd`/`platform-edge`; Argo CD after evidenced installation and handoff |
| Secrets | Infisical Cloud initially; no plaintext values in Git or OpenTofu state |
| CI and images | GitHub Actions and private GHCR images addressed immutably |
| Environments | `cristexhub-dev` and `cristexhub-prod` |
| Shared services | PostgreSQL, MongoDB, and any retained shared RabbitMQ in `shared-services`, with separate environment databases, principals, credentials, vhosts, limits, and backups |
| Other data services | Redis per environment; RabbitMQ may be shared only with separate users/vhosts and limits |
| Backups | Application-consistent local dumps plus encrypted off-host copy; restore required before PROD |

## Repository layout

```text
ansible/                 # discovery + bounded host changes + gated temporary QA probe
  inventory/
  playbooks/
  roles/read_only_discovery/
  roles/network_policy_probe/
  roles/opentofu_install/
  roles/platform_namespace_bootstrap/
opentofu/                # zero-resource Cloudflare-only scaffold
kubernetes/              # exact platform Namespace source; future Argo desired state
runbooks/                # recovery docs plus source-only candidate provenance
  replacement-host-recovery.md
  recovery-artifact-register.md
  argocd-candidate-provenance.md
  cloudflared-candidate-provenance.md
  infisical-operator-candidate-provenance.md
tests/                   # offline contract tests only
```

Only `ansible/`, the zero-resource `opentofu/` scaffold, the two platform Namespace
manifests under `kubernetes/`, documentation-only recovery and candidate-provenance
records under `runbooks/`, and offline `tests/` currently exist. Kustomize remains intended for
first-party application overlays; Helm is reserved for selected third-party
components. Argo ownership remains pending until Argo CD is installed, the two
Namespaces are adopted or registered through an Application, and successful sync
evidence exists; the future-owner label alone is not a handoff.

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

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
resources. Committed Kubernetes source now contains exactly four Namespace manifests.
The historical `argocd`/`platform-edge` wrapper check, first apply, and idempotence
retry completed under separate approvals and that exception remains closed. Exact
present-only source and a new dedicated guarded wrapper now exist for
`platform-secrets` and `platform-identity`, but their check, first apply, and
idempotence are **NOT RUN** and require separate approvals. No Argo CD, cloudflared,
Infisical Operator, Keycloak, PostgreSQL, Secret, workload, Service, policy, PVC, or
route exists from the new increment. A [source-only Argo CD candidate provenance record](runbooks/argocd-candidate-provenance.md)
binds public chart, captured signature/hash-binding, image, and online/static
readiness evidence. The separate [release selection](runbooks/argocd-release-selection.md)
selects chart `10.3.0` / app `v3.5.0` only for offline source authoring; it remains
**NOT DEPLOYABLE**. The exact 44-document render was reproduced at Kubernetes capability
`1.36.2`, stable upstream API registration screened successfully, and both image
closures were reachable from the controller. Exact k3s admission/runtime and node
pullability remain unproven; wildcard/broad RBAC, ineffective network isolation,
image trust, Secret recovery, private Git secret-zero, and Namespace adoption remain
blockers. It adds no chart, values, or Kubernetes object source. The separate
[source-only Argo CD hardened design](runbooks/argocd-hardened-design.md) accepts a
private ClusterIP and loopback-only port-forward direction, a retained quiescent
ApplicationSet, supplemental default-deny policy with an explicit ports-only
`443`/`6443` weakness, phased least-privilege RBAC, one-repository read-only GitHub
App credentials, value-free Infisical custody, and two independent Namespace-adoption
Applications. It adds no deployable source. Ansible is now selected as the future
bounded bootstrap installer and privileged lifecycle owner. The foundation Namespace
source is implemented, while its runtime checkpoints, component source/credentials,
resource inventory, Infisical recovery, Keycloak OIDC, adoption apply mode, candidate
selection, and runtime remain unresolved. The companion
[source-only Keycloak OIDC bootstrap design](runbooks/keycloak-oidc-bootstrap-design.md)
and [release selection](runbooks/keycloak-release-selection.md) select Keycloak
`26.7.1`, PostgreSQL `17.10`, realm `cristexhub`, and issuer
`https://auth.cristex-soft.com/realms/cristexhub` only for offline source authoring.
The value-free hosted policy selects exact client IDs, environment role templates,
Argo groups, deny-default authorization, Namespace trust, and Universal Auth
direction. No workload, Secret, route, or runtime is approved.
A separate
[source-only cloudflared candidate provenance record](runbooks/cloudflared-candidate-provenance.md)
binds official release, unsigned source, immutable linux/amd64 image, token-file,
health, and edge-transport evidence. It is also **CANDIDATE — NOT DEPLOYABLE — NOT
SELECTED**, with runtime **NOT RUN**, and adds no OpenTofu resource, Kubernetes
object, secret, route, or deployment source. A third
[source-only Infisical Operator candidate provenance record](runbooks/infisical-operator-candidate-provenance.md)
distinguishes the incomplete public `v0.11.8` distribution observation from the
version-aligned `v0.11.7` set. The separate
[release selection](runbooks/infisical-operator-release-selection.md) selects
`v0.11.7` only for offline source authoring and Universal Auth as direction. The
[inert privileged-prerequisites inventory](runbooks/infisical-operator-privileged-prerequisites-design.md)
binds the seven raw CRD templates and known RBAC/scoping defects to the vendored
archive while keeping every promotion gate closed. Runtime is **NOT RUN/BLOCKED**,
and no CRD, RBAC, values, rendered Kubernetes object, Ansible entrypoint, credential,
or Secret source was added. The actual target is now captured, but Infisical
chart/CRD/API compatibility remains unproven. No general host baseline or deployment
exists. Python is used only for offline contract tests, not infrastructure
automation.

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
PV, and namespace-bounded PVC projection. Hosted application runtime, OpenTofu
provider initialization/state/plan/apply, Helm chart, workflow, deployment, DNS
route, tunnel, database, backup, and replacement recovery remain unexecuted. The
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
6. [`runbooks/argocd-hardened-design.md`](runbooks/argocd-hardened-design.md) — source-only private-access, RBAC, network, secret-custody, and adoption design; not deployment authorization.
7. [`runbooks/argocd-release-selection.md`](runbooks/argocd-release-selection.md) — source-baseline selection and vendored-input boundary.
8. [`runbooks/foundation-namespace-bootstrap.md`](runbooks/foundation-namespace-bootstrap.md) — deployable-but-not-run exact present-only bootstrap for `platform-secrets` and `platform-identity`.
9. [`runbooks/keycloak-oidc-bootstrap-design.md`](runbooks/keycloak-oidc-bootstrap-design.md) — source-only Ansible-bootstrap, shared-identity, OIDC/RBAC, PostgreSQL, recovery, and private-exposure design.
10. [`runbooks/keycloak-release-selection.md`](runbooks/keycloak-release-selection.md) — immutable Keycloak/PostgreSQL and issuer source selection.
11. [`runbooks/cloudflared-candidate-provenance.md`](runbooks/cloudflared-candidate-provenance.md) — source-only, non-deployable cloudflared candidate evidence and blockers.
12. [`runbooks/infisical-operator-candidate-provenance.md`](runbooks/infisical-operator-candidate-provenance.md) — historical Infisical Operator candidate evidence and blockers.
13. [`runbooks/infisical-operator-release-selection.md`](runbooks/infisical-operator-release-selection.md) — `v0.11.7` source-baseline and Universal Auth boundary.
14. [`runbooks/infisical-operator-privileged-prerequisites-design.md`](runbooks/infisical-operator-privileged-prerequisites-design.md) — inert seven-CRD/RBAC observation and promotion-gate inventory; not deployable source.
15. [`specs/k3s-iac-foundation/testcases.md`](specs/k3s-iac-foundation/testcases.md) — validation contract and honest current results.

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
never creates or deletes a Namespace. Argo CD is the intended namespaced
reconciler only for exact object sets after Ansible stops reconciling them and
handoff evidence passes; Ansible retains privileged lifecycle ownership. The closed
historical exception was limited to creating or reconciling the committed `argocd`
and `platform-edge` Namespaces with state present. Any future component bootstrap
requires its own separately approved exact exception. The separately approved wrapper check passed at
`ok=19 changed=1 unreachable=0 failed=0 skipped=2` and predicted changes for exactly
those two absent Namespace items; the recap counts the single changed loop task.
The separately approved first apply then passed at
`ok=21 changed=1 unreachable=0 failed=0 skipped=0`, changed exactly both Namespace
items, verified both identities, all three labels, Active phase, and service health,
and created no other kind. The exception has no delete path. The separately approved
idempotence checkpoint first stopped before service preflight and Kubernetes
reconciliation on failed local sudo authentication at
`ok=10 changed=0 unreachable=0 failed=1 skipped=0`, so that attempt made no mutation
and proved no idempotence. Its retry passed at
`ok=21 changed=0 unreachable=0 failed=0 skipped=0`; both exact reconciliation items
were `ok`, protected post-state identity/label/Active assertions passed, and
k3s/Tailscale remained running. The completed temporary probe exception used the verified image and explicit approvals documented in
[`ansible/README.md`](ansible/README.md); every future run requires fresh approvals
and a unique Run ID.

The approved non-elevated discovery run passed and its curated host report was
reviewed locally. It did not use become or query Kubernetes. Syntax and lint also
passed. The approved schema-v3 elevated rerun refreshed the ignored mode-`0600`
report without target mutation. Operational discovery must explicitly load the
ignored local inventory because the default inventory contains only the neutral
alias. Use this one-line zsh shape only after the required approval:

```zsh
cd ~/Projects/cristexweb/ansible && uv run ansible-playbook -i .ansible/inventory.local.yml playbooks/discover.yml --check --diff --limit crtxweb -e read_only_discovery_enable_elevated=true -e read_only_discovery_elevated_approved=true --ask-become-pass
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
| Foundation bootstrap | Ansible for exact future Namespaces, Infisical Operator, Argo CD, Keycloak, privileged CRDs/cluster RBAC, and Keycloak realm/client/group lifecycle under component-specific approvals |
| Cluster reconciliation | Argo CD for namespaced desired state only after Ansible stops each exact object set and evidenced adoption/sync completes; no dual reconciliation |
| Identity | One future self-hosted Keycloak shared by CristexHub, Reactive Resume, and Argo CD; architecture target only, with direct Argo OIDC and private administration |
| Secrets | Infisical Cloud plus its Kubernetes Operator initially; no self-hosted Infisical and no plaintext values in Git or OpenTofu state |
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
  roles/foundation_namespace_bootstrap/
  files/vendor/            # hash-bound public chart/provenance/key inputs only
  files/policies/          # value-free hosted identity/authorization policy
opentofu/                # zero-resource Cloudflare-only scaffold
kubernetes/              # exact platform Namespace source; future Argo desired state
runbooks/                # recovery docs plus source-only candidate/design records
  replacement-host-recovery.md
  recovery-artifact-register.md
  argocd-candidate-provenance.md
  argocd-hardened-design.md
  argocd-release-selection.md
  foundation-namespace-bootstrap.md
  keycloak-oidc-bootstrap-design.md
  keycloak-release-selection.md
  cloudflared-candidate-provenance.md
  infisical-operator-candidate-provenance.md
  infisical-operator-release-selection.md
tests/                   # offline contract tests only
```

Only `ansible/`, the zero-resource `opentofu/` scaffold, the four platform Namespace
manifests under `kubernetes/`, documentation-only recovery, candidate-provenance,
hardened-design, and Keycloak/OIDC design records under `runbooks/`, and offline
`tests/` currently exist. Exact manifests and a distinct guarded wrapper now exist
for `platform-secrets` and `platform-identity`; check/apply/idempotence remain NOT RUN
and have no runtime authorization. Kustomize remains intended for
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
- self-hosted registry, Infisical server, or GitHub runner;
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

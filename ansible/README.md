# Guarded Ansible operations and read-only discovery

This directory contains bounded read-only discovery plus separately approved,
non-passthrough host, Namespace, controller, Secret-seam, datastore-preflight, and
database source closures. Most new closures remain source-only and runtime-blocked;
no wrapper grants implicit approval. The discovery playbook gathers bounded host facts with built-in modules
and queries exact Kubernetes kinds with `kubernetes.core.k8s_info`. Its storage
projection includes only the existing curated Node name/cluster scope plus exact
`status.nodeInfo.kubeletVersion`; curated block-device, partition,
mounted-filesystem-type, and mount-state indicators; exact StorageClass fields;
bounded PersistentVolume metadata; and PersistentVolumeClaim metadata from five
fixed namespaces. The separately approved schema-v3 elevated rerun passed with only
the ignored controller-local report changed; it captured kubelet `v1.36.2+k3s1`,
all 15 bounded queries available, and the zero-count `shared-services` PVC query. It
does not configure the host, install dependencies, read filesystem contents, or by
itself prove component compatibility, CNI behavior, or NetworkPolicy enforcement.

## Controller environment

The repository uses `uv` to create a project-local `.venv`. Python controller tools
are pinned in `pyproject.toml` and resolved exactly by `uv.lock`; the Ansible
collection remains pinned separately in `ansible/requirements.yml`.

From the repository root:

```bash
uv sync --locked
cd ansible
uv run ansible-galaxy collection install \
  -r requirements.yml \
  -p .ansible/collections
```

The generated `.venv/` and `ansible/.ansible/collections/` directories are ignored.
The Kubernetes collection also requires its documented Python client dependencies
on the execution host. Missing prerequisites are a failed or unavailable runtime
check, never an instruction for this playbook to install software on the server.

The committed inventory contains only the SSH alias `crtxweb`. Connection address,
user, key, and privilege credentials stay in operator-owned SSH/Ansible
configuration and are never committed here.

## Approved remote dependency bootstrap

The first elevated discovery proved that the remote Python environment lacked the
libraries required by `kubernetes.core.k8s_info`. The reviewed bootstrap has now
been installed successfully and the elevated queries pass. It installs
only Debian's `python3-kubernetes` and `python3-jsonpatch` packages; apt resolves
their declared dependencies.
Run check/diff first and inspect the package plan:

```bash
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/bootstrap_dependencies.yml \
  --check \
  --diff \
  --limit crtxweb \
  -e ansible_dependency_bootstrap_approved=true \
  --ask-become-pass
```

After the check result is accepted, run the approved mutation by removing only
`--check`:

```bash
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/bootstrap_dependencies.yml \
  --diff \
  --limit crtxweb \
  -e ansible_dependency_bootstrap_approved=true \
  --ask-become-pass
```

No directly requested package beyond those two, apt-cache refresh, upgrade, or host
baseline is authorized by this playbook. Apt may install reviewed transitive
dependencies.

## Approved group-scoped k3s administrator access

`configure_k3s_admin_access.yml` grants the selected non-root user access to the
cluster-admin kubeconfig through a dedicated `k3s-admin` group. It requires an
existing account with nonzero UID, fixes the group name, rejects GID 0 or numeric
GID aliases, and refuses unexpected existing supplementary or primary group
members. It preserves the kubeconfig as
root-owned mode `0640`, writes only the two persistent k3s settings, and restarts
k3s only when those settings change. Existing config content is hidden from Ansible
output and diff. A root-only `config.yaml.pre-admin-access` rollback copy is created
without overwriting an earlier baseline. After restart, Ansible verifies both the
metadata and actual readability of the kubeconfig while running as the selected
account. The restart causes a short control-plane interruption on this single node.

Review check/diff first:

```bash
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/configure_k3s_admin_access.yml \
  --check --diff --limit crtxweb \
  -e k3s_admin_access_approved=true \
  -e k3s_admin_user=paul \
  --ask-become-pass
```

After accepting the plan, run the approved mutation by removing only `--check`:

```bash
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/configure_k3s_admin_access.yml \
  --diff --limit crtxweb \
  -e k3s_admin_access_approved=true \
  -e k3s_admin_user=paul \
  --ask-become-pass
```

Existing login processes cannot acquire a newly assigned supplementary group.
Fully reconnect SSH after the run; if SSH multiplexing reuses an old server session,
reconnect with `ssh -o ControlMaster=no -o ControlPath=none crtxweb`. Then verify
`id -nG`, `kubectl get nodes`, and `kubectl get all -A`. Do not change the kubeconfig
to world-readable mode or expose the root-only k3s server configuration merely to
silence its warnings.

If the k3s restart fails, restore the root-only baseline before attempting anything
else:

```bash
sudo install -o root -g root -m 0600 \
  /etc/rancher/k3s/config.yaml.pre-admin-access \
  /etc/rancher/k3s/config.yaml
sudo systemctl restart k3s
```

After k3s recovers, removal of the user membership or dedicated group requires a
separately reviewed Ansible rollback; do not delete groups blindly.

## Warning-free k3s kubectl client

The k3s multicall `kubectl` reads the root-only server configuration before using
its separate kubeconfig, which causes harmless permission warnings for non-root
administrators. `configure_k3s_kubectl_client.yml` persists the proven client-only
defaults in the selected Bash user's active login profile and `.bashrc`:

```text
K3S_CONFIG_FILE=/dev/null
KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

Existing environment overrides remain authoritative. The playbook derives the home
and active login profile from account metadata, rejects unsafe profile paths, never
reads profile content into output, keeps `/etc/rancher/k3s/config.yaml` root-only,
and does not restart k3s.

Review the one-host plan:

```bash
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/configure_k3s_kubectl_client.yml \
  --check --diff --limit crtxweb \
  -e k3s_kubectl_client_approved=true \
  -e k3s_admin_user=paul \
  --ask-become-pass
```

After accepting the plan, remove only `--check`. Reconnect without SSH multiplexing
and confirm `kubectl get nodes` and `kubectl get all -A` succeed with no server-config
warning. A second run must report `changed=0`.

Rollback removes only the Ansible-managed profile blocks:

```bash
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/configure_k3s_kubectl_client.yml \
  --diff --limit crtxweb \
  -e k3s_kubectl_client_approved=true \
  -e k3s_kubectl_client_state=absent \
  -e k3s_admin_user=paul \
  --ask-become-pass
```

## Approved single-node reboot recovery verification

`verify_k3s_reboot_recovery.yml` performs exactly one reboot after requiring explicit
approval, an explicit one-host limit, and operator confirmation of console or LAN
fallback access. Before reboot it verifies k3s/Tailscale services, the root-only
rollback baseline, group-scoped kubeconfig access, and one Ready node. After SSH
returns it requires a new boot ID, running services, a Ready node, and unchanged
effective kubeconfig access. It changes no package or configuration, but the single
node and all workloads are temporarily unavailable.

Review the prediction first:

```bash
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/verify_k3s_reboot_recovery.yml \
  --check --diff --limit crtxweb \
  -e k3s_reboot_recovery_approved=true \
  -e k3s_recovery_access_confirmed=true \
  -e k3s_admin_user=paul \
  --ask-become-pass
```

After accepting the plan, remove only `--check`. Do not set the recovery-access flag
unless a physical console or independent LAN SSH path is genuinely available. If
the Tailscale path does not return, use that confirmed fallback to inspect
`tailscaled` and `k3s`; the reboot playbook itself makes no configuration change to
roll back.

## Temporary CNI and NetworkPolicy functional probe

`probe_k3s_network_policy.yml` implements three fail-closed actions: `plan`, `run`,
and `cleanup`. The first approved runtime passed; offline implementation alone is
still not proof for a future cluster or changed CNI.

The read-only plan verifies protected kubeconfig access, one Ready linux/amd64 node,
NetworkPolicy API readability, and the existing fixed `default` namespace. It
requires an explicit one-host limit plus `--check --diff` and never enters mutation
tasks:

```bash
cd ansible
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --check --diff --limit crtxweb \
  -e k3s_network_probe_action=plan
```

The functional run uses no Namespace create/delete and no remote exec. Kubernetes
assigns every temporary object name. Every object receives two immutable ownership
labels and is added to the ignored mode-`0600`
`ansible/network-policy-probe.local.json` cleanup ledger immediately after the API
returns its exact UID. The Service is selectorless
and uses an explicitly authored, ledgered EndpointSlice, so no controller-generated
endpoint object falls outside the cleanup boundary. Reverse cleanup reads each exact
name, verifies UID and both ownership labels, sends the same UID as a delete
precondition, and uses `Orphan` propagation so deletion cannot cascade to an
uninspected object. Cleanup runs in an Ansible `always` section, independently
rediscovers only the fixed kinds carrying both immutable labels, validates generated
prefixes and exact UIDs, and verifies zero residue. This closes the API-create/ledger
interruption gap without selector-based deletion: recovery check mode may rebuild the
private ledger from those exact identities, then intentionally stops for human
review before any deletion. Never broaden the fixed kinds or delete a Namespace.

Before `run`, independently verify a digest-qualified image that supplies BusyBox-
compatible `httpd` and `wget` entrypoints for linux/amd64. Record only a sanitized
evidence reference, select a unique high-entropy lowercase 20–32 character run ID, review the
separate temporary Argo CD ownership exception, and obtain separate create and
delete approvals. Then run the same request first with `--check --diff`; remove only
`--check` after accepting that plan:

```bash
cd ansible
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --check --diff --limit crtxweb \
  -e k3s_network_probe_action=run \
  -e network_policy_probe_run_id="$PROBE_RUN_ID" \
  -e network_policy_probe_image="$PROBE_IMAGE_DIGEST" \
  -e network_policy_probe_image_architecture=linux/amd64 \
  -e network_policy_probe_image_verification_reference="$PROBE_IMAGE_EVIDENCE" \
  -e network_policy_probe_ownership_exception_approved=true \
  -e network_policy_probe_create_approved=true \
  -e network_policy_probe_delete_approved=true
```

The accepted actual run proves, in order: both allowed- and denied-role baseline
clients succeed, both are blocked by default deny, selective allow admits only the
allowed role, and both roles succeed after policy removal. Client Pods use the
Service ClusterIP directly, require exact terminal exit/reason evidence, and expose
no phase-varying label. Denied evidence additionally requires the exact server to
remain Ready with zero restarts. The run ends with exact cleanup. It creates only a
ClusterIP service on TCP 8080 and no public route.

Cleanup deliberately does not validate or require the image. If a controller hard
stop left no ledger or an incomplete one, first run the following read-only recovery
check with the original high-entropy run ID. It discovers only the fixed generated-
name kinds carrying both ownership labels, rebuilds the mode-`0600` ledger, and
intentionally stops without Kubernetes deletion:

```bash
cd ansible
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --check --diff --limit crtxweb \
  -e k3s_network_probe_action=cleanup \
  -e network_policy_probe_run_id="$PROBE_RUN_ID" \
  -e network_policy_probe_ownership_exception_approved=true \
  -e network_policy_probe_delete_approved=true
```

Review the rebuilt ledger. The fixed file must be a non-symlink regular file owned
by the controller user with mode `0600`. Then run the exact cleanup request with
`--check --diff`; remove only `--check` after that validation succeeds:

```bash
cd ansible
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --check --diff --limit crtxweb \
  -e @network-policy-probe.local.json \
  -e network_policy_probe_ownership_exception_approved=true \
  -e network_policy_probe_delete_approved=true
```

The approved runtime used official BusyBox 1.37.0 linux/amd64 manifest
`sha256:7a3ebe5bfd1a4a19797d20b0c0bb39d44393e9a03fd852c0865b0f540d868df0`.
Registry inspection confirmed platform `linux/amd64`; direct layer inspection
confirmed `bin/httpd` and `bin/wget`. Check mode passed at
`ok=18 changed=0 failed=0`; execution passed all eight expected phases at
`ok=225 changed=43 failed=0`, removed 12 remaining exact identities after the two
policies had already been UID-deleted, and reported zero residue. A separate cleanup
check passed at `ok=20 changed=0` with `exact_identity_count=0`. No Namespace or
public exposure was created. Every future mutation requires fresh ownership,
create, and delete approvals plus a unique Run ID. Argo CD is only the intended
persistent reconciler after its separately evidenced installation and handoff; the
bounded Namespace bootstrap remains the current exception.

## Source-only k3s datastore and encryption preflight

`bin/preflight-k3s-datastore check` is the only entrypoint for the guarded
source-only k3s datastore/encryption preflight. It accepts exactly `check`, always
uses the ignored local inventory, `--check --diff --limit crtxweb`,
`--become --ask-become-pass`, supplies explicit elevation approval, and preserves
`become: false` on controller-local delegated tasks. The wrapper launches
the pinned controller in a clean allowlisted environment with an ephemeral
mode-`0600` attestation; direct playbook/role invocation, passthrough arguments,
task selection, and forged internal variables fail closed before host contact.

The role performs no mutation. Fixed read-only argv for k3s version, systemd
service/ExecStart properties, `secrets-encrypt status --output json`, and a JSON
Node query run under `no_log` use strict parsers. A bounded private slurp reads
only the fixed root-owned mode-`0600` config after its size gate. Fixed private
systemd `Environment` and `EnvironmentFiles` queries must both be empty before a
local/default data-directory source is trusted. Selected top-level `data-dir`,
`datastore-endpoint`, `cluster-init`, and
`secrets-encryption` fields must be unique and correctly typed; only booleans and
enums are projected. Initial `start` and completed `reencrypt_finished` remain
distinct, both require `hashmatch=true` for their stable projections, and only the
latter maps to `finished`; key names, hashes, hash errors, endpoints, paths, and
other raw values are not projected, and private raw facts are cleared before the
report. The ignored controller artifact is
`ansible/.ansible/k3s-datastore-preflight.local.json` with mode `0600` and schema
v2. It contains only validated version/stage values, datastore marker booleans,
encryption status/rotation stage, k3s/Tailscale and bounded Node health, and
disclosure-control booleans. See
[`runbooks/k3s-datastore-preflight.md`](../runbooks/k3s-datastore-preflight.md),
`tests/validate_k3s_datastore_preflight.yml`, and
`tests/validate_k3s_datastore_preflight_parser.yml` for the offline boundary.
The official source pin is K3s `v1.36.2+k3s1` commit
`01b6f04aaa69e8b09303f0393d4b4f1811da23aa`. A separately approved live read-only
run passed `ok=45 changed=1 unreachable=0 failed=0` but recorded only sanitized
unknown datastore/encryption/rotation evidence (`config_status=present_safe`,
`data_dir_source=config_override_unknown`).

## Mandatory invocation contract

Review first; then request separate approval before any host access. The playbook
refuses to proceed without check mode, diff mode, an explicit limit, and exactly one
selected host:

```bash
cd ansible
uv run ansible-playbook -i .ansible/inventory.local.yml playbooks/discover.yml --check --diff --limit crtxweb
```

That default is non-elevated and cannot query the root-only k3s kubeconfig. A
separately approved elevated discovery requires both explicit flags:

```bash
cd ansible
uv run ansible-playbook -i .ansible/inventory.local.yml playbooks/discover.yml --check --diff --limit crtxweb \
  -e read_only_discovery_enable_elevated=true \
  -e read_only_discovery_elevated_approved=true \
  --ask-become-pass
```

Do not put a become password in inventory, variables, files, or shell history. The
playbook points `k8s_info` at `/etc/rancher/k3s/k3s.yaml`, which the module must
load for authentication. The playbook never separately slurps, copies, registers,
logs, or renders kubeconfig content.

## Output and privacy

The inventory argument is mandatory for operational discovery. The default
`ansible.cfg` inventory contains only the neutral `crtxweb` alias and deliberately
has no endpoint or SSH-user data. Omitting `-i .ansible/inventory.local.yml` caused a
censored `UNREACHABLE` result before host discovery; it must not be treated as a host
health result or retried by disabling host-key verification.

The only write is a controller-local schema-v3 report at
`inventory.local.ansible.json` in the repository root. It is ignored by Git,
written mode `0600`, has task diff disabled, and is refused when the destination is
a symlink. Target discovery remains read-only even though the local report task
must run with `check_mode: false`.

Raw facts and Kubernetes objects are marked `no_log` and fact caching is memory-only.
The report projects only selected OS/capacity/service fields; device/partition size,
rotational/removable state, mounted state, and filesystem types observed in mount
facts; the existing curated Node name/cluster scope and one exact
`kubelet_version` string; exact StorageClass behavior fields; and bounded PV/PVC
capacity, binding, claim, backend-type, and placement booleans. The Node branch does
not render raw `nodeInfo`, addresses, identifiers, kernel/container-runtime fields,
labels, or annotations. Current source limits PVC queries to `default`,
`kube-system`, `shared-services`, `cristexhub-dev`, and `cristexhub-prod`; no Secret,
ConfigMap, Event, new API kind, or broad PVC query is made. The prior live extended
report used `shared-data` as its fifth scope and did not capture a Kubernetes
version. The separately approved schema-v3 rerun now confirms kubelet
`v1.36.2+k3s1`, the exact available `shared-services` PVC query with count zero, and
all 15 bounded queries available. That curated result establishes the target minor
for compatibility review but does not prove component runtime compatibility.
Generated PV identifiers and
backing paths are not rendered: placement is reduced to backend, node-affinity
presence, and whether a host path is under the fixed k3s storage root.

The report excludes device serials, addresses, MACs, UUIDs, annotations, labels,
environment fields, mount source/path strings, filesystem contents, Secret data,
chart values, raw specs, command output, and kubeconfig content. Unmounted
filesystem types are not inferred: they remain unknown unless a later separately
approved read-only method can supply them safely. Projection is still not a proof
of anonymity: review the complete report before sharing, and never commit it.

## Bounded persistent platform Namespace bootstrap

`bootstrap_platform_namespaces.yml` is a one-time ownership exception that may
create or reconcile only the committed `argocd` and `platform-edge` Namespace
manifests. Its only authorized entrypoint is the non-passthrough
`bin/bootstrap-platform-namespaces` wrapper. The wrapper accepts exactly `check` or
`apply`, rejects extra arguments including task-skipping controls, launches the
repository `.venv` Ansible executable by absolute path under an `env -i` allowlist,
and creates a mode-`0600` random single-run attestation removed on exit. The role
checks that private attestation during normal preflight and again on the mutating
task itself. The role also requires explicit approval, `--diff`, the exact
one-host limit, running k3s/Tailscale, and the existing root:`k3s-admin` mode-`0640`
kubeconfig. It rejects forged internal results before any register or API task, validates every
controller path ancestor and manifest leaf without following symlinks, loads the
committed definitions controller-side, requires exact top-level/metadata key sets,
queries only those two exact names, and
refuses an existing Namespace unless all reviewed bootstrap/future-owner labels
already match. Service, manifest, kubeconfig, and pre/post query assertions use
protected role results rather than externally forgeable facts. It uses only
`kubernetes.core.k8s` state `present`; no Namespace or other object has a deletion
path.

The manifests add no Pod Security policy before workload compatibility is reviewed
and contain no Secret, ConfigMap, workload, Service, Ingress, Tunnel, hostname, or
route. They identify Ansible as bootstrap writer and Argo CD only as future desired
owner; they do not claim `app.kubernetes.io/managed-by: argocd`. Argo CD and
cloudflared are not installed by this playbook. Argo ownership remains pending until
Argo CD installation, Namespace adoption or Application registration, and successful
sync evidence; a label alone is not a handoff. Rollback preserves the empty or
adopted Namespaces; deletion requires a separate future destructive plan and
approval.

From the repository root, the separately approved exact prediction used only:

```bash
ansible/bin/bootstrap-platform-namespaces check
```

The check passed at `ok=19 changed=1 unreachable=0 failed=0 skipped=2` after all
approval, attestation, canonical-path, manifest, service, kubeconfig, pre-state, and
foreign-existing assertions passed. The exact manifest contract contained only
`argocd` and `platform-edge` with the three reviewed labels, and the single loop task
predicted `changed` for both items. The recap therefore reports one changed task,
not one Namespace. Check mode created no object and skipped the two live post-state
tasks by design.

The separately approved first
`ansible/bin/bootstrap-platform-namespaces apply` passed at
`ok=21 changed=1 unreachable=0 failed=0 skipped=0`. The single changed loop task
changed exactly `argocd` and `platform-edge`; post-state queries and protected
assertions verified both exact identities, all three reviewed labels, `Active` phase,
and k3s/Tailscale health before and after. No other persistent kind was authorized or
changed. During the separately approved idempotence checkpoint, the initial
invocation stopped before service preflight and Kubernetes reconciliation because
local sudo authentication failed; it reported
`ok=10 changed=0 unreachable=0 failed=1 skipped=0` and made no mutation. The retry
passed at `ok=21 changed=0 unreachable=0 failed=0 skipped=0`: both exact Namespace
reconciliation items were `ok`, protected post-state identity/label/Active
assertions passed, and k3s/Tailscale remained running before and after. Never invoke
this playbook directly and never use `--start-at-task`, `--step`, tags, or other task
selection controls. This completed exception remains closed and must not be reused
for any future Namespace or component.

## Bounded Namespace and future component bootstrap direction

Ansible is selected as the future bounded bootstrap installer for exact foundational
Namespaces, the Infisical Cloud Kubernetes Operator, Argo CD, one self-hosted
Keycloak, and privileged CRD/cluster-RBAC prerequisites. Exact executable Namespace
source exists for completed Namespaces. The
[Infisical implementation profile](../runbooks/infisical-operator-implementation-profile.md)
remains canonical policy, and a dedicated guarded [Infisical bootstrap](../runbooks/infisical-operator-bootstrap.md) now promotes the
exact 44-object source-only idle closure: six namespaced CRDs, fail-closed
same-Namespace admission, PROD allowlists only for generic Auth/Connection/StaticSecret,
least-privilege namespaced RBAC, one metrics-off controller, authenticated
TLS Squid, and eight NetworkPolicies. The archive remains quarantined evidence and is
never consumed at runtime. No Secret value or runtime Infisical CR exists. Runtime is
unrun and the wrapper fails before mutation until exact separately recovered proxy
Secret metadata exists. A separate guarded Argo CD source closure now exists but
also remains runtime-unrun; Keycloak, PostgreSQL, MongoDB, and application runtime
remain absent. A separate source-only [Infisical Argo CD Secret materialization
seam](../runbooks/infisical-argocd-secret-materialization.md) freezes one
same-Namespace Universal Auth reference, one Connection/Auth/StaticSecret closure,
exactly three orphaned Argo targets, additive exact-name Secret RBAC, workload
list/watch required by the v0.11.7 reconciler, and fail-closed admission. Its
credential Secret, check/apply, sync, target values, and runtime remain NOT
RUN/BLOCKED. A separate source-only [Infisical database Secret materialization
seam](../runbooks/infisical-database-secret-materialization.md) freezes 15 value-free
objects: one shared Connection, separate PostgreSQL/MongoDB Auth and credential
identities, two path-scoped StaticSecrets, eleven engine/per-consumer target contracts,
eight scoped VAP/binding objects, operator-only validation, additive
no-delete/no-workload-write RBAC, byte/canonical/identity
hashes, and negative fixtures. Its credential values, check/apply, sync, rotation,
recovery, and runtime remain NOT RUN/BLOCKED. A separate source-only [CristexHub
PROD runtime Infisical seam](../runbooks/infisical-cristexhub-prod-runtime-materialization.md)
freezes the exact `/cristexhub/prod/runtime` source for the committed and now
Active/idempotent `cristexhub-prod` Namespace, independent `cristexhub-prod-infisical-auth` and
Universal Auth names, nine runtime keys plus `cristexhub-prod-ghcr-pull`, exact
PROD-scoped VAP/bindings, additive least-privilege RBAC, hash-bound manifests, and
its guarded `bin/bootstrap-infisical-cristexhub-prod-runtime check|apply` source.
The Namespace, Universal Auth values, Infisical sync, target Secret values, and
PROD runtime remain NOT RUN/BLOCKED. The value-free
[shared database policy](../runbooks/shared-database-architecture.md) records one
PostgreSQL and one standalone MongoDB engine in `shared-services`; guarded,
hash-bound, present-only source now exists for both database pods while every live
Secret, check/apply/idempotence, provisioning, recovery, and runtime gate remains
blocked. CristexHub
DEV/PROD have isolated scopes on both engines; Reactive Resume DEV/PROD and Keycloak
have dedicated PostgreSQL scopes. The separate value-free
[shared RabbitMQ policy](../runbooks/shared-rabbitmq-architecture.md) fixes one future
engine, exact DEV/PROD vhost/user/limit scopes, and reviewed future-consumer
admission. The [shared backup policy](../runbooks/shared-stateful-backup-architecture.md)
requires private authenticated operator retrieval, encrypted timestamped archives,
non-destructive off-node copy, integrity checks, and isolated restore. RabbitMQ and
backup remain policy-only; the database closures are source-ready but not runtime
approvals. The separate [Reactive Resume policy](../runbooks/reactive-resume-hosted-architecture.md) includes
private DEV in MVP intent while keeping its image, callbacks, objects, Secrets, and
runtime blocked. GitHub CI may run only syntax/lint and offline contracts from this
source; it supplies no inventory and invokes no operational wrapper. The repository
contains twenty-nine exact-scope action plugins; these focused Python exceptions
are source guards/validators only, not a general operational collector.

Each component requires a dedicated non-passthrough entrypoint and frozen
source/object closure with separate check, apply, and idempotence evidence. For the
Infisical idle closure, first use only
`bin/bootstrap-infisical-proxy-secrets apply` to generate, age-encrypt, copy, restore-
verify, and write the three circular proxy bootstrap values. Then use only
`bin/bootstrap-infisical-operator check` followed by a separately reviewed `apply`;
the same `apply` must later converge at `changed=0`. Both use existing `k3s-admin`
kubeconfig access without sudo and accept no passthrough. The separate
`bin/bootstrap-infisical-argocd-secrets check|apply` wrapper is source-ready but
remains blocked until the human-created same-Namespace Universal Auth Secret and
fixed Infisical source identifiers exist; it never carries values. The separate
`bin/bootstrap-infisical-database-secrets check|apply` wrapper is source-ready but
remains blocked until both human-created same-Namespace Universal Auth Secrets and
fixed project/environment/path identifiers exist; it never carries values. The
separate `bin/bootstrap-infisical-cristexhub-prod-runtime check|apply` wrapper is
also source-ready but remains blocked until the human-created
`cristexhub-prod-infisical-universal-auth` metadata exists; it never reads or carries
values. The Namespace is already Active/idempotent, while all later PROD resources
remain blocked. Exact present-only source and the distinct
`bin/bootstrap-foundation-namespaces` entrypoint
exist for `shared-services`; check, separately approved first apply, and separately
approved idempotence all passed, with the final run converging at `changed=0`. The
superseded `platform-secrets`/`platform-identity` source was never run and its removal
does not delete a live Namespace. The completed wrapper above is neither broadened
nor reopened.
Ansible remains lifecycle owner of privileged CRDs, ClusterRoles/ClusterRoleBindings
and Keycloak realm/client/group reconciliation. Namespaced specifications may hand
off to Argo only after Ansible stops reconciling the exact objects and reviewed
adoption/sync evidence passes. Dual reconciliation is forbidden. The
[foundation Namespace bootstrap runbook](../runbooks/foundation-namespace-bootstrap.md)
records the completed separately approved sequence using these exact one-line commands:

- `ansible/bin/bootstrap-foundation-namespaces check`
- `ansible/bin/bootstrap-foundation-namespaces apply`

The first apply and idempotence invocation used the same apply command under distinct
approvals. No further foundation command is authorized by this documentation.

The dedicated [CristexHub DEV Namespace bootstrap](../runbooks/cristexhub-dev-namespace-bootstrap.md)
owns only `cristexhub-dev` with four approved labels. Its guarded wrapper is distinct,
and its dedicated action rejects controller task-selection context plus any mutation
argument drift before delegating to the pinned Kubernetes module. The separate
[CristexHub PROD Namespace bootstrap](../runbooks/cristexhub-prod-namespace-bootstrap.md)
contains only the exact four-label present-only source and independently rejects
canonical-task-source, wrapper-attestation, approved/state, preflight, and action
argument bypasses. The separately approved `cristexhub-prod` Namespace is Active and
idempotent; its later wrapper/API resources remain NOT RUN/BLOCKED. The DEV separately approved check passed at
`ok=20 changed=1 unreachable=0 failed=0 skipped=2`, with one exact predicted
Namespace change and no mutation. The first apply passed at
`ok=22 changed=1 unreachable=0 failed=0 skipped=0`, created/verified only that
Namespace, and preserved service health. Idempotence passed at
`ok=22 changed=0 unreachable=0 failed=0 skipped=0`; the Namespace checkpoint is
complete.

Hash-bound public chart/provenance/public-key inputs exist under `files/vendor/` for
Argo CD `10.3.0` and Infisical Operator `0.11.7`. Argo runtime never consumes Helm;
`files/components/argocd/` contains the exact 32-object reviewed closure and render
evidence mapping. `bin/bootstrap-argocd check|apply` is the only authorized Argo
entrypoint. It uses existing k3s-admin access without sudo, creates only present
objects, requires the exact three cryptographically valid Infisical-owned Secret
contracts, refuses the initial-admin Secret and foreign objects, and performs no
deletion. Empty-API check mode defers only the unresolved default-project custom
resource; apply waits for all three CRDs to report Established before runtime objects.
`files/policies/hosted-identity-authorization.yml` is a value-free review policy, not
an executable playbook, realm import, Kubernetes object, credential, or permission
to render/install a controller. The separate
[`infisical-operator-privileged-prerequisites.yml`](files/policies/infisical-operator-privileged-prerequisites.yml)
and [design record](../runbooks/infisical-operator-privileged-prerequisites-design.md)
inventory seven raw CRD templates and upstream RBAC seams only. They add no valid
CRD/RBAC source, values, rendered object, wrapper, playbook, role, or permission to
contact a cluster. Release selection does not close signer trust, image
assurance/recovery, scoped RBAC, secret-zero, admission, or runtime gates. The
source-only [Keycloak OIDC bootstrap design](../runbooks/keycloak-oidc-bootstrap-design.md)
records the remaining release, database, secret, network, recovery, and runtime
gates without authorizing cluster contact.

## Approved pinned OpenTofu CLI installation

`install_opentofu.yml` installs only the independently verified OpenTofu `1.12.5`
linux/amd64 release, selects it through `/usr/local/bin/tofu`, and creates the empty
operator-owned mode-`0700` `/var/lib/opentofu/cristexweb` directory outside k3s.
It requires Debian 13 x86_64, running k3s/Tailscale, an existing non-root operator
with no numeric UID alias, exact safe parent/artifact modes, `--diff`, a one-host
limit, and explicit approval. The host does not need outbound GitHub access: when
the root-owned host archive is absent, the controller downloads it into ignored
`ansible/.ansible/cache/opentofu/`, verifies the exact digest, and transfers it over
the existing Ansible connection. The role preflights controller directories and the
cached archive without following symlinks, refuses foreign ownership or mode/digest
drift, and makes no controller-cache write in check mode. It never initializes a
provider, creates or reads a state file, restarts a service, or contacts Kubernetes.

Controller-side release review verified the official
[`tofu_1.12.5_SHA256SUMS`](https://github.com/opentofu/opentofu/releases/download/v1.12.5/tofu_1.12.5_SHA256SUMS)
file (SHA-256
`120345f8a2493375aebbca072106de425b2eb227837f8064440b8d911e36f987`)
against its official
[OpenPGP signature](https://github.com/opentofu/opentofu/releases/download/v1.12.5/tofu_1.12.5_SHA256SUMS.gpgsig)
and signer fingerprint `E3E6E43D84CB852EADB0051D0C0AF313E5FD9F80`. The
signed manifest records archive SHA-256
`a6894d45ae7a17ce83189cce8fe04b5a65f68cefceb62455b5a6a89fa53ab38f`;
the extracted `tofu` binary was independently verified as
`36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4`.
The controller and host enforce the reviewed archive digest, and the host also
enforces the extracted payload digest. Neither downloads the manifest or repeats
OpenPGP verification during installation.

The first approved check passed at `ok=27 changed=6 failed=0`. The first live run
stopped at `ok=21 changed=2 failed=1` when the old host-side download returned
`[Errno 113] No route to host`. Only `/opt/opentofu`, `/var/cache/opentofu`,
`/var/lib/opentofu`, and the empty protected project directory were created with the
reviewed ownership and modes; no archive, binary, selector, or state file existed at
that stop. The reviewed controller-transfer check then passed at
`ok=33 changed=6 failed=0`. The live recovery downloaded the exact archive into the
ignored controller cache, transferred and reverified it, installed the pinned
payload and selector, and preserved running k3s/Tailscale at
`ok=39 changed=6 failed=0`. The second run passed at
`ok=30 changed=0 failed=0`. The project state directory remains empty and no provider
operation or external resource exists.

Review check/diff first. The operator account remains an explicit local input:

```bash
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/install_opentofu.yml \
  --check --diff --limit crtxweb \
  -e opentofu_install_approved=true \
  -e opentofu_install_operator_user=<approved-user> \
  --ask-become-pass
```

After reviewing that only the private controller cache when needed, verified archive
transfer, versioned payload, managed selector, and protected empty directory change,
remove only `--check` for the separately approved live installation. A second approved live run must report
`changed=0`. Verify the exact version in a fresh session; do not add provider or
backend credentials to extra vars or shell history.

Rollback is separately approved and first reviewed in check mode:

```bash
uv run ansible-playbook -i .ansible/inventory.local.yml \
  playbooks/install_opentofu.yml \
  --check --diff --limit crtxweb \
  -e opentofu_install_state=absent \
  -e opentofu_install_rollback_approved=true \
  -e opentofu_install_operator_user=<approved-user> \
  --ask-become-pass
```

Live rollback removes only the exact managed `/usr/local/bin/tofu` selector. It
retains the archive, versioned payload, local state directory, every state/lock
file, and all external resources. Unknown or modified selectors fail closed.

Provider initialization, lockfile generation, validation, planning, apply, import,
state commands, destroy, state encryption, Google Drive copy, and recovery are
separate future gates. No apply is allowed until encrypted timestamped off-node
state recovery and key custody pass an isolated rehearsal.

## Guarded host rclone and proxy recovery transfer

The dedicated entrypoints are:

```text
ansible/bin/install-rclone check|apply|rollback-check|rollback-apply
ansible/bin/transfer-infisical-proxy-recovery check|apply|cleanup-check|cleanup-apply
```

The installer pins rclone `1.71.1`, uses controller-cache verification plus Ansible
host transfer, retains root-owned version/cache artifacts, and rolls back only the
selector. The transfer resolves the existing non-root inventory operator with
getent, never reads rclone config content, runs only four immutable `copyto`
commands on the host, and stages/fetches only ciphertext. See
[`rclone-host-transfer.md`](../runbooks/rclone-host-transfer.md). Installer check
passed twice at `ok=25 changed=1 failed=0`. Two applies stopped before host mutation:
the first at `changed=0` on missing normal-module dispatch, and the second at
`ok=24 changed=2 failed=1` after creating only the exact ignored controller cache,
when the action guard received an unrendered role default for the operator. The
resolved operator is copied into the attested internal binding for both rclone
guards, and focused/full offline validation passes. A fresh check passed at
`ok=25 changed=1 failed=0`; the separately approved corrected install then passed at
`ok=34 changed=4 failed=0`, selected verified rclone `1.71.1`, and preserved
k3s/Tailscale health. The separately approved idempotence apply passed at
`ok=32 changed=0 failed=0`. Host OAuth then completed through a private callback
tunnel; token-bearing rclone config remains only on the host. Transfer check passed
at `ok=26 changed=0 failed=0`. Apply stopped on unsupported `--local-umask` after
only exact encrypted staging; approved cleanup removed staging at
`ok=26 changed=1 failed=0`. The reviewed compatibility fixes pass `258/258`, but its
fresh check initially stopped before facts because the host became transiently
Tailscale-offline. After return, check passed `ok=26 changed=0`; transfer/readback
passed `ok=39 changed=7`; proxy Secret bootstrap passed `ok=15 changed=1`. Infisical
Operator then passed check/apply/idempotence. Universal Auth and database runtime
remain **NOT RUN/BLOCKED**. Apply approvals are separate; installer sudo is
interactive only.

## Guarded shared logical database provisioning

The separate source-only logical lane is documented in
[`shared-database-provisioning.md`](../runbooks/shared-database-provisioning.md).
Its only entrypoints are `bin/provision-shared-postgresql check|apply` and
`bin/provision-shared-mongodb check|apply`; they accept no passthrough, use the
pinned controller and one-run attestation, and require `--diff` plus one host. The
lane requires a Ready engine and exact precreated Infisical-owned consumer Secrets;
Ansible never generates, logs, exports, rotates, or puts values in argv.

Each apply uses hash-bound no-secret-argv database scripts and one temporary
UID-bound helper Pod plus ingress NetworkPolicy. Helpers are non-root, tokenless,
PVC-free, hostPath-free, and cleaned in an `always` block with exact UID
preconditions and `Orphan` propagation. Only missing frozen logical reservations
may be created; foreign ownership, drift, credential mismatch, data-bearing state,
or stale helpers stop. No database, role, user, PVC, or Secret deletion path exists.
PROD is inactive; MongoDB is standalone/non-authoritative; runtime, authorization,
backup, restore, idempotence, and Argo handoff remain **NOT RUN/BLOCKED**.

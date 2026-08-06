# Read-only Ansible discovery

This directory contains the repository's first Ansible implementation: a small,
read-only discovery playbook. It gathers bounded host facts with built-in modules
and queries exact Kubernetes kinds with `kubernetes.core.k8s_info`. Its storage
projection includes only curated block-device, partition, mounted-filesystem-type,
and mount-state indicators; exact StorageClass fields; bounded PersistentVolume
metadata; and PersistentVolumeClaim metadata from five fixed namespaces. It does
not configure the host, install dependencies, read filesystem contents, or prove
CNI behavior or NetworkPolicy enforcement.

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
and `cleanup`. Runtime is still **NOT RUN/BLOCKED**. Offline implementation is not
proof of CNI behavior or NetworkPolicy enforcement.

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

Do not run either mutation command yet: the repository contains no independently
verified image digest or approval record. Argo CD remains the sole owner of
persistent Kubernetes desired state.

## Mandatory invocation contract

Review first; then request separate approval before any host access. The playbook
refuses to proceed without check mode, diff mode, an explicit limit, and exactly one
selected host:

```bash
cd ansible
uv run ansible-playbook playbooks/discover.yml --check --diff --limit crtxweb
```

That default is non-elevated and cannot query the root-only k3s kubeconfig. A
separately approved elevated discovery requires both explicit flags:

```bash
cd ansible
uv run ansible-playbook playbooks/discover.yml --check --diff --limit crtxweb \
  -e read_only_discovery_enable_elevated=true \
  -e read_only_discovery_elevated_approved=true \
  --ask-become-pass
```

Do not put a become password in inventory, variables, files, or shell history. The
playbook points `k8s_info` at `/etc/rancher/k3s/k3s.yaml`, which the module must
load for authentication. The playbook never separately slurps, copies, registers,
logs, or renders kubeconfig content.

## Output and privacy

The only write is a controller-local schema-v2 report at
`inventory.local.ansible.json` in the repository root. It is ignored by Git,
written mode `0600`, has task diff disabled, and is refused when the destination is
a symlink. Target discovery remains read-only even though the local report task
must run with `check_mode: false`.

Raw facts and Kubernetes objects are marked `no_log` and fact caching is memory-only.
The report projects only selected OS/capacity/service fields; device/partition size,
rotational/removable state, mounted state, and filesystem types observed in mount
facts; exact StorageClass behavior fields; and bounded PV/PVC capacity, binding,
claim, backend-type, and placement booleans. PVC queries are limited to `default`,
`kube-system`, `shared-data`, `cristexhub-dev`, and `cristexhub-prod`; no Secret,
ConfigMap, Event, or broad PVC query is made. Generated PV identifiers and backing
paths are not rendered: placement is reduced to backend, node-affinity presence,
and whether a host path is under the fixed k3s storage root.

The report excludes device serials, addresses, MACs, UUIDs, annotations, labels,
environment fields, mount source/path strings, filesystem contents, Secret data,
chart values, raw specs, command output, and kubeconfig content. Unmounted
filesystem types are not inferred: they remain unknown unless a later separately
approved read-only method can supply them safely. Projection is still not a proof
of anonymity: review the complete report before sharing, and never commit it.

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

## Temporary CNI and NetworkPolicy probe design (read-only plan only)

`probe_k3s_network_policy.yml` currently implements only a read-only planning
preflight. It verifies one Ready linux/amd64 node, NetworkPolicy API readability,
protected kubeconfig access, and absence of the proposed fixed namespace. It must
run with `--check --diff` and cannot create, patch, or delete Kubernetes objects.
Argo CD remains the owner of all persistent Kubernetes desired state.

```bash
cd ansible
uv run ansible-playbook \
  -i .ansible/inventory.local.yml \
  playbooks/probe_k3s_network_policy.yml \
  --check --diff --limit crtxweb \
  -e k3s_network_probe_action=plan
```

The intended future probe remains **NOT RUN/BLOCKED**. Before mutating code may be
authorized, independent review must close all of these prerequisites:

- verify and pin the real linux/amd64 digest for the approved probe image;
- replace the fixed-name create race with an atomic namespace-ownership strategy;
- design cleanup that cannot cascade-delete uninspected built-in or custom resources;
- obtain separate create and delete approvals.

The proposed scope remains eight temporary objects, ClusterIP TCP 8080 only, and
baseline → deny → selective allow → policy removal → exact-object cleanup. No run or
cleanup command is implemented or documented until those blockers close.

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

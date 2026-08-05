# Read-only Ansible discovery

This directory contains the repository's first Ansible implementation: a small,
read-only discovery playbook. It gathers bounded host facts with built-in modules
and queries exact Kubernetes kinds with `kubernetes.core.k8s_info`. It does not
configure the host, install dependencies, or prove CNI behavior or NetworkPolicy
enforcement.

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

The only write is a controller-local report at
`inventory.local.ansible.json` in the repository root. It is ignored by Git,
written mode `0600`, has task diff disabled, and is refused when the destination is
a symlink. Target discovery remains read-only even though the local report task
must run with `check_mode: false`.

Raw facts and Kubernetes objects are marked `no_log` and fact caching is memory-only.
The report projects only selected OS/capacity/service/filesystem fields and
Kubernetes object names/counts. It excludes addresses, MACs, UUIDs, annotations,
labels, environment fields, Secret data, chart values, raw specs, command output,
and kubeconfig content. Projection is still not a proof of anonymity: review the
complete report before sharing, and never commit it.

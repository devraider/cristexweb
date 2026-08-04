# Read-only Ansible discovery

This directory contains the repository's first Ansible implementation: a small,
read-only discovery playbook. It gathers bounded host facts with built-in modules
and queries exact Kubernetes kinds with `kubernetes.core.k8s_info`. It does not
configure the host, install dependencies, or prove CNI behavior or NetworkPolicy
enforcement.

## Controller prerequisites

Install Ansible and the pinned collection deliberately on the controller. This
repository does not install them automatically:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

The Kubernetes collection also requires its documented Python client dependencies
on the execution host. Missing prerequisites are a failed or unavailable runtime
check, never an instruction for this playbook to install software.

The committed inventory contains only the SSH alias `crtxweb`. Connection address,
user, key, and privilege credentials stay in operator-owned SSH/Ansible
configuration and are never committed here.

## Mandatory invocation contract

Review first; then request separate approval before any host access. The playbook
refuses to proceed without check mode, diff mode, an explicit limit, and exactly one
selected host:

```bash
cd ansible
ansible-playbook playbooks/discover.yml --check --diff --limit crtxweb
```

That default is non-elevated and cannot query the root-only k3s kubeconfig. A
separately approved elevated discovery requires both explicit flags:

```bash
cd ansible
ansible-playbook playbooks/discover.yml --check --diff --limit crtxweb \
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

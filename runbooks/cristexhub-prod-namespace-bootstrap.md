# CristexHub PROD Namespace bootstrap

## Status and boundary

**SOURCE-ONLY — NOT RUN / BLOCKED.** This increment adds a guarded, present-only
source closure for exactly the `cristexhub-prod` Namespace. The wrapper `check`
and `apply` modes have not been run and remain blocked pending separate human
approval for each stage. No Kubernetes API, kubectl, Ansible operational play,
provider, Secret read, workload, or PROD deployment was performed for this
source increment.

This source does not authorize PROD activation. It does not define or create a
Secret, ServiceAccount, ResourceQuota, LimitRange, NetworkPolicy, workload,
Service, PVC, database, broker, route, ingress, Infisical object, or Argo CD
object. No Secret, workload, Service, PVC, policy, route, or PROD workload is
part of this closure. DEV validation, recovery, and soak evidence remain separate
gates for future PROD work.

## Exact source closure

The dedicated closure owns only:

- `kubernetes/applications/namespaces/cristexhub-prod.yaml`;
- `ansible/bin/bootstrap-cristexhub-prod-namespace`;
- `ansible/playbooks/bootstrap_cristexhub_prod_namespace.yml`;
- `ansible/plugins/action/cristexhub_prod_namespace_guarded_k8s.py`;
- `ansible/roles/cristexhub_prod_namespace_bootstrap/`; and
- the focused offline contracts and negative fixtures under `tests/`.

The manifest is exactly one value-free object:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cristexhub-prod
  labels:
    app.kubernetes.io/part-of: cristexhub
    cristex.io/environment: prod
    cristex.io/bootstrap-writer: ansible
    cristex.io/desired-owner: argocd
```

The committed manifest is hash-pinned in the role defaults with SHA-256
`f029bb06bb698c6ddc3e083985f754bd326de8b18804523d1300eae54e8260d0`. The role
checks the exact regular non-symlink manifest leaf, mode and ownership, canonical
repository ancestors, and matching SHA-256 before any mutation-capable task.

## Guarded execution contract

`ansible/bin/bootstrap-cristexhub-prod-namespace` is the sole entrypoint. It
accepts exactly one argument, `check` or `apply`; it does not pass through task
selection, tags, extra arguments, or alternate playbooks. It uses the ignored
inventory, the exact `crtxweb` limit, `--diff`, `--ask-become-pass`, and the pinned
repository `.venv` Ansible controller under an `env -i` allowlist. It generates a
private random mode-`0600` single-run attestation and removes it on exit.

The role fails closed unless the wrapper attestation is present, regular,
non-symlinked, controller-owned, mode `0600`, and contains the matching token
marker. It requires explicit approval, `state: present`, diff mode, exactly one
selected host, the existing root:`k3s-admin` mode-`0640` kubeconfig, and running
k3s/Tailscale services. The role's internal-variable guard runs first, and the
mutating action independently rejects task-selection controls and any arguments
outside the exact Namespace definition. The in-run preflight binds the
attestation SHA-256, exact manifest SHA-256, manifest identity, pre-state, path
counts, kubeconfig contract, and service contract before the mutation task.

Only `state: present` is implemented. Before a future approved run, the role
queries only `cristexhub-prod`; if it exists with any missing, changed, or extra
identity label, it refuses foreign existing namespaces and refuses silent foreign
adoption rather than silently reconciling it.
There is no `state: absent`, delete, force, or rollback deletion path; this
closure has no deletion path. Source rollback is a Git revert; Namespace deletion
would require a separate destructive design and approval.

## Approval sequence and evidence

No wrapper check or apply has been executed for this source closure. The wrapper
check and apply remain NOT RUN/BLOCKED pending separate human approval for each
stage:

1. Review the offline contract, exact source hash, task-selection negatives, and
   `git diff --check`; separately approve only the wrapper `check`.
2. Inspect the check result and predicted single Namespace scope; separately
   approve only the wrapper `apply` if the result is accepted.
3. Treat any later idempotence or PROD validation as a new approval sequence; no
   such evidence is claimed here.

The focused offline contract verifies the exact manifest, hash ledger, wrapper
allowlist and non-passthrough boundary, attestation and internal-variable guards,
foreign-existing refusal, present-only/no-delete semantics, and blocked status.
It performs no wrapper invocation, kubectl call, Ansible operational play,
provider command, or Secret read.

## Stop conditions

Stop without mutation on any manifest/hash drift, symlink or ownership/mode drift,
missing or reusable attestation, forged internal result, noncanonical controller
path, absent diff/limit/approval gate, failed service or kubeconfig preflight,
foreign existing Namespace, label/schema drift, task-selection argument, extra
object kind, Secret/value disclosure, or any request to broaden this closure.

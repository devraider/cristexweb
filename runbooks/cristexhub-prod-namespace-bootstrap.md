# CristexHub PROD Namespace bootstrap

## Status and boundary

**NAMESPACE BOOTSTRAP COMPLETE; ALL LATER PROD PHASES BLOCKED.** The guarded,
present-only closure created exactly the `cristexhub-prod` Namespace after a
separately approved check and apply, and its separately approved idempotence apply
converged at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`. The Namespace is
`Active` with the four reviewed labels plus Kubernetes' mandatory
`kubernetes.io/metadata.name` label. No Secret, workload, route, database, broker,
Infisical object, Argo registration, or Argo sync was created by this checkpoint.

This completed Namespace checkpoint does not authorize later PROD activation. It
does not define or create a
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
- the focused offline contracts and negative fixtures under `tests/`, including
  `reject_cristexhub_prod_namespace_action_only.yml`,
  `reject_cristexhub_prod_namespace_internal_injection.yml`, and
  `reject_cristexhub_prod_namespace_task_start.sh`.

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

The committed manifest is bound to the non-overridable SHA-256 literal
`f029bb06bb698c6ddc3e083985f754bd326de8b18804523d1300eae54e8260d0` in the role
and action plugin; it is not an extra-vars/defaults input. The role checks the
exact regular non-symlink manifest leaf, mode and ownership, canonical repository
ancestors, and matching SHA-256 before any mutation-capable task.

## Guarded execution contract

`ansible/bin/bootstrap-cristexhub-prod-namespace` is the sole entrypoint. It
accepts exactly one argument, `check` or `apply`; it does not pass through task
selection, tags, extra arguments, or alternate playbooks. It uses the ignored
inventory, the exact `crtxweb` limit, `--diff`, and the pinned repository `.venv`
Ansible controller under an `env -i` allowlist. It deliberately does not request
sudo: the operator's existing `k3s-admin` group reads the protected kubeconfig, and
service discovery is read-only and unprivileged. It generates a private random
mode-`0600` single-run attestation and removes it on exit.

The role fails closed unless the wrapper attestation is present, regular,
non-symlinked, controller-owned, mode `0600`, and contains the matching token
marker. It requires explicit approval, `state: present`, diff mode, exactly one
selected host, the existing root:`k3s-admin` mode-`0640` kubeconfig, and running
k3s/Tailscale services. The role's internal-variable guard runs first, and the
mutating action independently binds its canonical role-task source, wrapper
attestation, exact approved/state values, complete internal preflight object,
task-selection controls, and arguments outside the exact Namespace definition.
The in-run preflight binds the attestation SHA-256, exact manifest SHA-256,
manifest identity, pre-state, path counts, kubeconfig contract, and service
contract before the mutation task. Direct action-only invocation and forged
internal/preflight values are rejected before the Kubernetes module.

Only `state: present` is implemented. Before a future approved run, the role
queries only `cristexhub-prod`; if it exists with any missing, changed, or extra
identity label, it refuses foreign existing namespaces and refuses silent foreign
adoption rather than silently reconciling it.
There is no `state: absent`, delete, force, or rollback deletion path; this
closure has no deletion path. Source rollback is a Git revert; Namespace deletion
would require a separate destructive design and approval.

## Approval sequence and evidence

The approved check predicted the single absent Namespace at
`ok=20 changed=1 unreachable=0 failed=0 skipped=2`. The first approved apply
created that Namespace (`changed=1`) but its post-verification stopped because the
closure had not accounted for Kubernetes' mandatory Namespace-name label. Read-only
inspection confirmed the Namespace was `Active` with exactly the intended labels
plus that mandatory label. The corrected exact-label closure and unprivileged
`k3s-admin` kubeconfig path then passed a fresh check at
`ok=20 changed=0 unreachable=0 failed=0 skipped=2`. The separately approved
idempotence apply passed at `ok=22 changed=0 unreachable=0 failed=0 skipped=0`,
including exact post-state and k3s/Tailscale health.

Earlier attempts stopped safely before Kubernetes mutation on the historical
case-sensitive Linux controller-path mismatch, local mode drift, unavailable
non-interactive sudo, and rejected sudo authentication. Those stops created no
additional object. Local controller paths were normalized to `0755`, the manifest
to `0644`, and the final wrapper uses existing unprivileged `k3s-admin` access.

The focused offline contract verifies the exact manifest, literal hash binding,
wrapper allowlist and non-passthrough boundary, canonical task-source/action-only
negative, attestation and internal-variable guards, forged preflight injection
negative, foreign-existing refusal, present-only/no-delete semantics, and blocked
status. The negative fixtures run only localhost controller-side guards when the
pinned offline controller is available; they perform no wrapper invocation,
kubectl call, Ansible operational play, provider command, Kubernetes API access,
or Secret read.

## Stop conditions

Stop without mutation on any manifest/hash drift, symlink or ownership/mode drift,
missing or reusable attestation, forged internal result, noncanonical controller
path, absent diff/limit/approval gate, failed service or kubeconfig preflight,
foreign existing Namespace, label/schema drift, task-selection argument, extra
object kind, Secret/value disclosure, or any request to broaden this closure.

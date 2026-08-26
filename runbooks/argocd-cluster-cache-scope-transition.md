# Argo cluster-cache namespace-scope transition

## Purpose

`ansible/bin/bootstrap-argocd-cluster-cache-scope-transition` is a one-time,
non-passthrough lane for the Argo cluster-registration cache collision. It may
inspect and patch only these three Ansible-owned Secrets in `argocd`, in the
listed source order:

- `argocd-cluster-cristexhub-dev`
- `argocd-cluster-cristexhub-prod`
- `argocd-cluster-reactive-resume-dev`

Each target is loaded from its original registration manifest's `stringData`.
The final registration manifests remain the desired source of truth; this lane
does not reconcile an Application, AppProject, Role, RoleBinding, workload,
Namespace, repository credential, or Reactive Resume dependency.

## Guard contract

The lane has exactly `check` and `apply` modes and rejects extra arguments,
task-selection controls, injected internal variables, a non-canonical source,
source hash drift, and a missing single-run attestation. It runs only against
the pinned `crtxweb` host with the pinned repository `.venv` controller and
`--diff`; the wrapper supplies a clean environment and removes its `0600`
attestation on exit.

Before mutation, it checks all three Secrets with `no_log` metadata/data checks:

- exact API identity, `Opaque` type, five data keys, server, cluster-resource,
  config, and logical name values;
- exact Ansible ownership labels and no owner references/finalizers;
- valid UID and resourceVersion bindings;
- each namespace value is exactly its legacy single namespace or the final
  `cristexhub-dev,cristexhub-prod` scope;
- the poststate binds each Secret's own decoded `data.name` to its own metadata
  identity, preventing a sorted-set or cross-object swap from passing.

For each Secret still in its exact legacy state, the action plugin dispatches a
single Kubernetes JSON Patch containing `test` operations for UID,
resourceVersion, and the old encoded `data.namespaces`, followed by the sole
allowed replacement of `/data/namespaces`. It never prints Secret data. A
partially completed run is resumable: already-final Secrets are left alone,
and foreign or partial scopes fail closed.

## Safe failure and recovery states

| State | Meaning | Safe next step |
|---|---|---|
| all three legacy | no Secret mutation | review `check`, then separately approve `apply` |
| one or two final, remaining legacy | bounded partial transition | rerun `check`; patch only exact remaining legacy records |
| all three final, Argo still stale | scope update completed but cache refresh unaccepted | inspect read-only cache/controller state; do not delete a duplicate Secret |
| UID/resourceVersion/data/name/label conflict | concurrent or foreign writer detected | stop, retain state, rerun `check` after ownership review |
| poststate/controller failure | fail-closed stop after bounded patches | no automatic rollback; use a reviewed forward repair and fresh approval |

There is no delete, prune, broad apply, or blind rollback path. A source revert
requires review and a fresh exact check; it does not claim that a shared URL cache
can be atomically restored by deletion. A malicious process already running as
the trusted controller UID can forge same-UID files and inputs and remains
outside the claimed integrity boundary.

## Offline validation

`.venv/bin/python -m unittest tests.test_argocd_cluster_cache_scope_transition_contract`

No live check or apply is implied by this source. A future operator must review
the check receipt, obtain separate approval for `apply`, and verify the exact
three Secret poststates plus fresh Argo status. The original registration lanes
remain final desired ownership; this one-time transition lane must not be reused
for routine reconciliation.

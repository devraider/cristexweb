# Argo cluster-cache namespace-scope transition

## Purpose

`ansible/bin/bootstrap-argocd-cluster-cache-scope-transition` is a one-time,
non-passthrough lane for the Argo cluster-registration cache collision. It may
inspect and patch only these three Ansible-owned Secrets in `argocd`:

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
  config, and name values;
- exact Ansible ownership labels and no owner references/finalizers;
- valid UID and resourceVersion bindings;
- each namespace value is exactly its legacy single namespace or the final
  `cristexhub-dev,cristexhub-prod` scope.

For each Secret still in its exact legacy state, the action plugin dispatches a
single Kubernetes JSON Patch containing `test` operations for UID,
resourceVersion, and the old encoded `data.namespaces`, followed by the sole
allowed replacement of `/data/namespaces`. It never prints Secret data. A
partially completed run is resumable: already-final Secrets are left alone,
and foreign or partial scopes fail closed.

## Offline validation

```text
.venv/bin/python -m unittest tests.test_argocd_cluster_cache_scope_transition_contract
```

No live check or apply is implied by this source. A future operator must review
the check receipt, obtain separate approval for `apply`, and verify the exact
three Secret poststates plus fresh Argo status. The original registration lanes
remain final desired ownership; this one-time transition lane must not be
reused for routine reconciliation.

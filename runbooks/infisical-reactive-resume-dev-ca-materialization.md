# Reactive Resume DEV CA materialization

This source-only closure projects two existing Infisical CA values into the
pre-created `cristexhub-dev` dependency objects. It creates no values and does
not create the Namespace or the DEV `InfisicalAuth`; the latter must already be
`cristexhub-dev-infisical-auth` and metadata-valid.

## Exact contract

- Infisical project: `619656da-14f3-4872-857b-be103cdc5326`
- Environment: `prod` (Infisical environment slug only)
- Existing Auth: `cristexhub-dev/cristexhub-dev-infisical-auth`
- Source `prod:/shared-services/postgresql`, template key
  `POSTGRESQL_TLS_CA_CRT` -> `ConfigMap/reactive-resume-dev-postgresql-ca` key
  `ca.crt`.
- Source `prod:/reactive-resume/dev/object-storage-tls`, template key `CA_CRT`
  -> `Opaque Secret/reactive-resume-dev-object-storage-ca` key `ca.crt`.
- Both target objects are Infisical-owned, Orphan-created, value-free in Git,
  and remain in `cristexhub-dev`.

The closure contains exactly two source/target admission policies and bindings,
one namespaced writer Role/Binding for the existing
`shared-services/infisical-operator-controller` ServiceAccount, and one
`InfisicalStaticSecret`. No Secret values, Auth credentials, or CA bytes are
stored in the repository.

## Guarded entrypoint

Run only the committed wrapper, never a direct playbook invocation:

```text
ansible/bin/bootstrap-infisical-reactive-resume-dev-ca check
ansible/bin/bootstrap-infisical-reactive-resume-dev-ca apply
```

`check` is the required first mode. The wrapper uses the repository-pinned
controller, a clean environment, an ephemeral single-run attestation, fixed
host/Namespace/target identities, and hash-bound source. `apply` requires a
separate operator approval and must be followed by metadata-only target checks
and Infisical reconcile readiness. Do not print or export values; no CA data is
read by the guard.

The existing DEV runtime admission boundary is deliberately narrowed to its
own exact identities in source so this additive CA policy owns only the two
reviewed CA target names. The old runtime closure remains otherwise unchanged.

Status: source-only closure implemented; live check/apply intentionally **NOT
RUN** in this change.

# Reactive Resume DEV CA materialization

This source-only closure projects two existing Infisical CA values into the
pre-created `cristexhub-dev` dependency objects. It creates no values and does
not create the Namespace or the DEV `InfisicalAuth`; the latter must already be
`cristexhub-dev-infisical-auth` and metadata-valid.

## Exact contract

- Infisical project: `619656da-14f3-4872-857b-be103cdc5326`
- Environment: `prod` (Infisical environment slug only)
- Existing Auth: `cristexhub-dev/cristexhub-dev-infisical-auth`
- Source `prod:/reactive-resume/dev/object-storage-tls`, template key
  `POSTGRESQL_CA_CRT` -> `ConfigMap/reactive-resume-dev-postgresql-ca` key
  `ca.crt`.
- The same source path's `STORAGE_TLS_CA_CRT` key projects to
  `Opaque Secret/reactive-resume-dev-object-storage-ca` key `ca.crt`.
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

Status: the guarded check predicted one closure change. The first approved apply
created the seven-object closure, but the initial object-storage template referenced
the nonexistent `CA_CRT` key and produced an invalid trust payload. Correcting it
to `STORAGE_TLS_CA_CRT` restored storage. The initially selected broad
`POSTGRESQL_TLS_CA_CRT` did not validate the live CloudNativePG endpoint, so a
DEV-scoped `POSTGRESQL_CA_CRT` copy of the live public CNPG CA was uploaded without
value output to the existing `prod:/reactive-resume/dev/object-storage-tls` custody
path. Source was narrowed to that one DEV trust path, both target certificates
validated, one exact ephemeral application Pod was restarted, and the Deployment
returned to `1/1` Ready with healthy database and storage. Final guarded
idempotence passed at `changed=0 failed=0`; zero private material was retained.

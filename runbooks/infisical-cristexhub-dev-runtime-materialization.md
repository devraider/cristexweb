# CristexHub DEV runtime Infisical materialization

Status: **source-only / NOT RUN / BLOCKED**.

This guarded seam defines, but does not apply, the application-owned
`cristexhub-dev-runtime` Secret in Namespace `cristexhub-dev`. Infisical Cloud
owns values; Ansible owns only this foundational Connection/Auth/StaticSecret,
admission, and additive writer RBAC closure. No Secret value is committed.

## Fixed source contract

- Project: `cristexweb-infrastructure`
- Project ID: `619656da-14f3-4872-857b-be103cdc5326`
- Environment slug: `prod` (Infisical identifier, not Kubernetes PROD)
- Path: `/cristexhub/dev/runtime`, non-recursive, empty tags
- Target: `cristexhub-dev-runtime`, type `Opaque`, orphaned
- Keys: `MONGODB_URL`, `RABBITMQ_URL`, `REDIS_URL`, `REDIS_PASSWORD`, `FERNET_KEY`, `OIDC_CLIENT_SECRET`, `OAUTH2_PROXY_COOKIE_SECRET`

## Guarded execution

Only `ansible/bin/bootstrap-infisical-cristexhub-dev-runtime check|apply` is an
entrypoint. It rejects passthrough/task selection, uses the pinned controller,
`--diff`, one host, a one-time mode-0600 attestation, and exact manifest hashes.
Both modes stop before mutation until the separately approved and materialized
`cristexhub-dev/cristexhub-dev-infisical-universal-auth` Secret exists with
`clientId` and `clientSecret`. This source change did not create that Secret.

The seam contains 13 value-free objects: four ValidatingAdmissionPolicies and
bindings, one Role/RoleBinding, one Connection, one Auth, and one StaticSecret.
No alternate target-producing Infisical CR is permitted. The writer Role grants
only Secret read/list/watch, create, and resourceNames-limited update for the
exact target, plus controller workload list/watch.

Application workload sync, secret materialization, credential creation, runtime
validation, rotation, Argo handoff, and deployment remain separately gated.

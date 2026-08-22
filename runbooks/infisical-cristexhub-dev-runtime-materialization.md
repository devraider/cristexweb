# CristexHub DEV runtime Infisical materialization

Status: **source-only / NOT RUN / BLOCKED**.

The canonical composition policy is
`ansible/files/policies/cristexhub-dev-runtime-materialization.yml`; its guarded
controller entrypoint is
`ansible/bin/materialize-infisical-cristexhub-dev-runtime apply`.

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
- Runtime target key closure: `MONGODB_URL`, `RABBITMQ_URL`, `REDIS_URL`,
  `REDIS_PASSWORD`, `FERNET_KEY`, `OIDC_CLIENT_SECRET`,
  `OAUTH2_PROXY_COOKIE_SECRET`, `CODE_RUNNER_AUTH_TOKEN`, `BROWSERLESS_TOKEN`, `PRIVATE_CA_BUNDLE`.
- `MONGODB_URL` and `RABBITMQ_URL` are composed from the existing DEV-scoped
  Infisical consumer credentials and service endpoints; credentials are URL-encoded
  and TLS is mandatory. `OIDC_CLIENT_SECRET` is read from the existing
  `/shared-services/keycloak` `CRISTEXHUB_DEV_OIDC_CLIENT_SECRET` predecessor
  without rotation. The future `cristexhub-dev` successor realm instead reserves
  `prod:/cristexhub/dev/identity/browser#OIDC_CLIENT_SECRET`; that path is disconnected,
  unmaterialized, and must not gain a second writer before a separately approved
  handoff. A clean bootstrap composes fresh `CODE_RUNNER_AUTH_TOKEN` and
  `BROWSERLESS_TOKEN` values inside its protected no-output bundle. The existing
  live path is non-empty, so its ten-key migration remains blocked until an exact
  rotation/CAS writer contract is separately approved. `PRIVATE_CA_BUNDLE` is the exact concatenation of the MongoDB and
  RabbitMQ public CA certificates (no leaf or private key), projected at
  `/etc/cristexhub/tls/ca-bundle.pem` for both clients. Redis, Fernet, and the
  OAuth cookie secret are generated only in the protected composition bundle.

## Guarded execution

Only `ansible/bin/bootstrap-infisical-cristexhub-dev-runtime check|apply` is an
entrypoint. It rejects passthrough/task selection, uses the pinned controller,
`--diff`, one host, a one-time mode-0600 attestation, and exact manifest hashes.
Both modes stop before mutation until the separately approved and materialized
`cristexhub-dev/cristexhub-dev-infisical-universal-auth` Secret exists with
`clientId` and `clientSecret`. This source change did not create that Secret.

The source-only composition workflow is separately guarded: it accepts only
`apply`, reads protected values through the DEV read-only Universal Auth identity,
requires exact source key closure and TLS CA validation, and uploads one exact
batch to `/cristexhub/dev/runtime` only after metadata preflight. It never emits
values, rotates existing values, or writes Kubernetes objects. Its generated
bundle is removed on exit and a revision/readback key-closure check is required.

The seam contains 13 value-free objects: four ValidatingAdmissionPolicies and
bindings, one Role/RoleBinding, one Connection, one Auth, and one StaticSecret.
No alternate target-producing Infisical CR is permitted. The writer Role grants
only Secret read/list/watch, create, and resourceNames-limited update for the
exact target, plus controller workload list/watch.

Application workload sync, secret materialization, credential creation, runtime
validation, rotation, Argo handoff, and deployment remain separately gated.

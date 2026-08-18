# CristexHub PROD runtime Infisical seam

Status: **source-only / NOT RUN / BLOCKED**.

This runbook records the value-free production runtime Secret seam only. The
canonical offline policy is
[`ansible/files/policies/cristexhub-prod-runtime-materialization.yml`](../ansible/files/policies/cristexhub-prod-runtime-materialization.yml).
No Infisical Cloud value was read or uploaded, no Kubernetes API was contacted, and
no Ansible operational wrapper was invoked for this change. `cristexhub-prod`
remains absent; its Namespace and workload promotion require separate approvals. No Infisical, Kubernetes, or Ansible operational wrapper was invoked.

## Fixed contract

- Infisical project: `cristexweb-infrastructure`
- Project ID: `619656da-14f3-4872-857b-be103cdc5326`
- Environment slug: `prod` — an Infisical Cloud identifier only; it is not
  Kubernetes PROD activation.
- Exact non-recursive source path: `/cristexhub/prod/runtime`; tags are empty.
- Shared PROD OIDC client-secret source contract: Infisical environment `prod`,
  path `/cristexhub/prod/runtime`, key `OIDC_CLIENT_SECRET`, and the same target
  key `OIDC_CLIENT_SECRET`; this is the value-free source used by the hosted
  Keycloak PROD client policy. No alternate source or value mapping is allowed.
- Kubernetes target Namespace: `cristexhub-prod` (must already exist and be
  `Active`; this seam never creates a Namespace).
- Source identity: `cristexhub-prod-infisical-auth`, using the separately
  materialized `cristexhub-prod-infisical-universal-auth` Secret with only
  `clientId` and `clientSecret` keys.
- Runtime target: `cristexhub-prod-runtime`, an orphaned `Opaque` Secret with
  exactly `MONGODB_URL`, `RABBITMQ_URL`, `REDIS_URL`, `REDIS_PASSWORD`,
  `FERNET_KEY`, `OIDC_CLIENT_SECRET`, `OAUTH2_PROXY_COOKIE_SECRET`,
  `PRIVATE_CA_BUNDLE`, and `CODE_RUNNER_AUTH_TOKEN`.
- Image-pull target: `cristexhub-prod-ghcr-pull`, an independent orphaned
  `kubernetes.io/dockerconfigjson` Secret with only `.dockerconfigjson`.

The committed source contains no Secret object and no secret value. The four
fail-closed ValidatingAdmissionPolicy/binding pairs constrain the exact PROD
Connection/Auth, StaticSecret, target names, metadata, types, and key closure.
Alternate target-producing Infisical CR kinds are denied in only the exact
`cristexhub-prod` namespace. The additive Role grants the shared Infisical
operator ServiceAccount only Secret read/list/watch, exact-name update, Secret
create (constrained by the VAP), and controller workload list/watch; it has no
patch, delete, impersonation, or workload-write privilege.

## Guarded source

The only component bootstrap entrypoint is:

```text
ansible/bin/bootstrap-infisical-cristexhub-prod-runtime check|apply
```

It launches the pinned repository controller in an allowlisted environment with
`--diff`, one selected host, a private one-time mode-0600 attestation, and no
passthrough/task-selection controls. The role validates canonical mode-0644
manifest leaves, the 13-object value-free closure, exact hashes, the existing
`Active` Namespace labels, and exact pre-state before its present-only mutation
path. The action plugin accepts only those 13 canonical non-Secret definitions,
its resolved role task source, and the bound attestation/preflight identity set.
There is no deletion or rotation path.

Both modes stop before any seam object mutation until the exact
`cristexhub-prod-infisical-universal-auth` Secret already exists with the reviewed
metadata and key names. Its values are never read by offline tests or committed
source. The existing guarded Infisical Operator closure deliberately does not watch
`cristexhub-prod` and has no PROD manager Role/Binding; widening that already-live
closure requires a separate reviewed source/check/apply/idempotence approval. This
operator production namespace watch/RBAC prerequisite, the application workload,
Infisical sync, target values, private validation, Argo handoff, and
PROD promotion remain separate gates.

## Offline evidence

The focused contract test verifies the exact source path/environment, the shared
value-free PROD OIDC client-secret source contract, independent PROD names and
identity, nine-key runtime closure, separate GHCR target, VAP
scope/failure policy, Role/RoleBinding boundaries, manifest/default/action hashes,
wrapper gates, and blocked policy/runbook statements. Run only offline validation:

```bash
.venv/bin/python -m unittest -v tests.test_infisical_cristexhub_prod_runtime_contract
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-infisical-cristexhub-prod-runtime
git diff --check
git diff --cached --quiet
```

Expected status for this source-only increment: focused tests pass; Namespace
creation, identity materialization, Infisical API access, Kubernetes access,
Secret sync, application deployment, public exposure, and PROD acceptance remain
**NOT RUN / BLOCKED**.

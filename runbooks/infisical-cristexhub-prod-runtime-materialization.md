# CristexHub PROD runtime Infisical seam

Status: **PRIOR NINE-KEY TARGET APPLIED; TEN-KEY SOURCE UPDATE NOT RUN / BLOCKED**.

This runbook records the value-free production runtime Secret seam only. The
canonical offline policy is
[`ansible/files/policies/cristexhub-prod-runtime-materialization.yml`](../ansible/files/policies/cristexhub-prod-runtime-materialization.yml).
Values were materialized through protected no-output controller operations; no value
was committed or printed. A read-only guarded wrapper check was
run after hardening and stopped at `ok=15 changed=0 unreachable=0 failed=1` because
the live Operator pod template included the bounded rollout receipt and an extra
`SSL_CERT_DIR` trust-store entry. The receipt is now explicitly bounded and the
exact `SSL_CERT_DIR=/etc/ssl/certs:/etc/infisical-proxy-ca` value is canonical
Operator source. A fresh Operator check passed at
`ok=30 changed=0 failed=0 skipped=5`; the runtime check then advanced to the intended absent Universal Auth
gate and stopped at `ok=23 changed=0 failed=1` without mutation. After separately
approved identity reuse, predecessor revocation, successor credential creation,
and exact Infisical path/value materialization, the seam created its 13 objects
and both target Secrets. The final guarded retry passed at
`ok=62 changed=0 failed=0 skipped=3`. The Namespace remains separately owned;
private workloads are now `Synced/Healthy`, while the Cloudflare route remains
unapplied. During read-only review, one local retained tool transcript accidentally
captured base64 Secret data. The transcript artifacts were removed; the PROD
Universal Auth predecessor and application/OIDC keys were rotated and verified.
The MongoDB/RabbitMQ credentials embedded in the URLs and the reused GHCR pull
credential still require separately verified rotation before public cutover.

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
  `PRIVATE_CA_BUNDLE`, `CODE_RUNNER_AUTH_TOKEN`, and `BROWSERLESS_TOKEN`.
- Image-pull target: `cristexhub-prod-ghcr-pull`, an independent orphaned
  `kubernetes.io/dockerconfigjson` Secret with only `.dockerconfigjson`.

The ten-key source is not runtime-applied: the live checkpoint remains the prior
nine-key target until `BROWSERLESS_TOKEN` is inserted through an approved Infisical
value lane and the guarded check/apply/idempotence sequence passes.

The committed manifest source contains no Secret object and no secret value. The four
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
manifest leaves, the unique 13-object value-free identity closure, exact hashes, the
existing `Active` Namespace labels, exact Operator Deployment/PROD manager RBAC,
generic admission specs, all six Infisical CR inventories, every PROD Secret name,
and exact pre-state before its present-only mutation path. It applies the four VAPs
first, waits for type-checking, applies their bindings, rechecks CR/Secret UID and
resourceVersion snapshots, then grants writer RBAC and creates Connection, Auth, and
StaticSecret in that order. Every Secret query/assertion is `no_log`; generated
targets require exact labels, types, key closure, and the sole non-empty
`secrets.infisical.com/version` annotation. The action plugin accepts only those 13
canonical non-Secret definitions, strict integer counts, and the derived identity
hash from its canonical role task source. There is no deletion or rotation path.

Both modes stop before any seam object mutation until the exact
`cristexhub-prod-infisical-universal-auth` Secret already exists with the reviewed
metadata and key names. Its values are never read by offline tests or committed
source. The guarded Infisical Operator source closure now watches `cristexhub-prod` and
contains its exact namespaced manager Role/Binding plus the generic Auth,
Connection, and StaticSecret five-namespace admission allowlists. Secret,
PushSecret, and DynamicSecret remain PROD-excluded. The Operator
watch/RBAC expansion is applied/idempotent; the prior nine-key runtime seam is
applied/idempotent, while this ten-key source update is blocked. The prior seam created the exact Connection, Auth,
StaticSecret, writer RBAC, admission objects, and two generated target Secrets;
it created no Namespace, PVC, database engine, or Cloudflare route.

## Offline evidence

The focused contract test verifies the exact source path/environment, the shared
value-free PROD OIDC client-secret source contract, independent PROD names and
identity, ten-key source runtime closure, separate GHCR target, VAP
scope/failure policy, Role/RoleBinding boundaries, manifest/default/action hashes,
wrapper gates, and blocked policy/runbook statements. Run only offline validation:

```bash
.venv/bin/python -m unittest -v tests.test_infisical_cristexhub_prod_runtime_contract
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-infisical-cristexhub-prod-runtime
git diff --check
git diff --cached --quiet
```

Historical runtime status: final nine-key idempotence passed at
`ok=62 changed=0 failed=0 skipped=3`; both prior target Secrets matched that remote key
closure, and Argo reported the private workloads `Synced/Healthy`. The ten-key source
update is not applied. Public exposure
remains blocked on the provider apply and the residual credential rotations recorded
above.

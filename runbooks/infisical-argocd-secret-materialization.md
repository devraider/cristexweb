# Infisical Argo CD Secret materialization seam

## Boundary

This is a source-only, separately guarded seam for the already-selected Infisical
Operator `v0.11.7`. It adds no secret values, credentials, Kubernetes Secret
manifest, Argo workload, route, or runtime approval. The existing 40-object idle
Operator closure remains unchanged and remains **NOT RUN/BLOCKED**. This seam is
also **NOT RUN/BLOCKED**.

The seam has exactly 11 Ansible-owned objects:

- three fail-closed `ValidatingAdmissionPolicy` objects and three `Deny` bindings;
- one namespaced `Role` and one `RoleBinding` for the existing
  `shared-services/infisical-operator-controller` ServiceAccount; and
- one `InfisicalConnection`, one `InfisicalAuth`, and one `InfisicalStaticSecret`.

The committed source never contains the human-created Universal Auth Secret or
any value from it. The materializer creates only these target Secret identities:

| Secret | Type | Exact keys |
|---|---|---|
| `argocd-secret` | `Opaque` | `admin.password`, `admin.passwordMtime`, `server.secretkey` |
| `argocd-redis` | `Opaque` | `auth` |
| `argocd-server-tls` | `kubernetes.io/tls` | `ca.crt`, `tls.crt`, `tls.key` |

All targets are explicitly templated, labelled `app.kubernetes.io/managed-by:
infisical`, `app.kubernetes.io/part-of: argocd`, and
`cristex.io/value-owner: infisical-cloud`, and use `creationPolicy: Orphan`.
The seam refuses existing foreign, wrong-type, wrong-key, wrong-label, or
non-orphan targets before any mutation. It also refuses
`argocd-initial-admin-secret`.

## Fixed human-created identifiers

A human operator must create the following out of band in Infisical Cloud and
Kubernetes before a separately approved seam check/apply. These are identifiers,
metadata, and source shape only; values remain outside Git and Ansible logs.

- Infisical Cloud project slug: `cristexweb-infrastructure`.
- Infisical environment slug: `bootstrap`.
- Infisical secret path: `/argocd`.
- Kubernetes credential Secret: `argocd/argocd-infisical-universal-auth`.
- Credential Secret type: `Opaque`; exact keys: `clientId`, `clientSecret`.
- The seven Infisical keys at `bootstrap:/argocd`:
  `ARGOCD_ADMIN_PASSWORD_BCRYPT`, `ARGOCD_ADMIN_PASSWORD_MTIME`,
  `ARGOCD_SERVER_SECRETKEY`, `ARGOCD_REDIS_AUTH`, `ARGOCD_TLS_CA_CRT`,
  `ARGOCD_TLS_CRT`, and `ARGOCD_TLS_KEY`.

The credential Secret is one same-Namespace reference: both fields of
`argocd/argocd-infisical-auth` point to that one Secret, using keys `clientId`
and `clientSecret`. No value, client ID, client secret, bcrypt hash, Redis
password, certificate, private key, project ID, or token is committed here.

## Admission and RBAC boundary

Admission is applied before the additive writer Role and its binding. The Secret
policy matches CREATE/UPDATE (Kubernetes admission reports an API PATCH as UPDATE)
and only permits the exact controller identity
`system:serviceaccount:shared-services:infisical-operator-controller` to write
those three names in `argocd`; it also requires each exact type, key set, target
labels, and orphan metadata without inspecting values. Other identities are not
changed by this policy. The alternate target policy denies `InfisicalSecret`,
`InfisicalPushSecret`, and `InfisicalDynamicSecret` in `argocd`. The StaticSecret
policy requires the exact name `argocd-infisical-secrets`, same-Namespace Auth
reference, explicit `recursive: false`, an explicit empty `tagSlugs` list, no
`projectId`, fixed sync options, and exact three target/template identity
contracts. The vendored CRD deliberately preserves `template.data` as unknown;
that untyped field is therefore enforced by the hash-bound source manifest and
Ansible action guard, never dereferenced from CEL.

The additive Role grants the vendored v0.11.7 reconciler only:

- Secret `get`, `list`, and `watch`, required by its namespace-scoped Secret cache
  and same-Namespace Universal Auth lookup; this trusted value-handling controller
  already reads the credential and no workload receives this Role;
- Secret `create` (the admission policy supplies the exact-name boundary);
- Secret `update` with `resourceNames` limited to the three target names; and
- Deployment/DaemonSet/StatefulSet `list` and `watch`, because every changed
  StaticSecret target lists all three workload kinds before deciding whether a
  reload is needed.

It grants no Secret `patch` or `delete` and no workload `get`, `create`,
`update`, `patch`, or `delete`. Existing idle manager Roles remain unchanged.

## Guarded sequence

Only this non-passthrough entrypoint is an authorized future path:

```text
ansible/bin/bootstrap-infisical-argocd-secrets check
ansible/bin/bootstrap-infisical-argocd-secrets apply
```

The wrapper supplies the pinned repository controller, clean environment, exact
inventory, `--diff`, one-host limit, present-only approval, and a mode-0600
single-run attestation. Direct playbook use, passthrough arguments, tags,
skip-tags, task selection, and sudo are rejected. The role verifies the existing
Namespace, credential metadata, all six Infisical CRDs, target pre-state, absence
of all noncanonical StaticSecrets and alternate target-producing CRs, and all 11
hash-bound source objects before
mutation. It then applies admission policies, waits for type-check/effective
policy readback, applies admission bindings and RBAC, and reconciles Connection,
Auth, and StaticSecret in that order; waits for `IsReady=True` on the v0.11.7
Connection/Auth and for current-generation `LastReconcileStatus=True` plus
`LastSuccessfulReconcileAt=True` on the StaticSecret; and verifies the exact
three target Secret metadata/type/key/label/orphan/non-immutable contracts without
logging values.

Check and apply, Secret creation, Infisical authentication, source sync, target
values, Argo CD installation, Argo readiness, idempotence, rotation, recovery,
and runtime negative tests are **NOT RUN/BLOCKED**; runtime remains **NOT RUN/BLOCKED** and requires separate review
and approvals. A source check is not evidence that the Infisical project,
environment, credential values, or targets exist.

## Offline validation

The seam is validated only with controller-local offline commands. No inventory
host, kubeconfig, Kubernetes API, Infisical API, credential, Secret value, or
mutation is used:

```bash
python3 -m unittest -v tests.test_infisical_argocd_secrets_contract
python3 -m unittest discover -s tests -v
sh -n ansible/bin/bootstrap-infisical-argocd-secrets
cd ansible
for playbook in playbooks/*.yml; do
  ansible-playbook -i .ansible/inventory.local.yml "$playbook" --syntax-check
done
ansible-lint --offline --profile production .
cd ..
python3 -m compileall -q tests ansible/plugins/action
bash -n tests/reject_infisical_argocd_secrets_task_start.sh
git diff --check
git diff --cached --quiet
```

The command results belong in `specs/k3s-iac-foundation/testcases.md` after the
actual offline checks. This source-only runbook records no live result.

## Rollback and residual risk

Before runtime, rollback is a Git revert of this source-only seam; it never
creates or deletes a Secret. After a future runtime approval, preserve orphaned
application Secrets and use a separately reviewed exact source/Role rollback.
The vendored controller still lists workload kinds on changed targets, and the
current v0.11.7 source has broader upstream reconciler capabilities than this
seam grants; admission plus exact Role permissions are therefore both required.
Infisical Cloud availability, Universal Auth recovery/rotation, project/source
creation, target cryptographic validity, Kubernetes admission support, and
single-node recovery remain open gates.

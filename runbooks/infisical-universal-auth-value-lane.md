# Infisical Universal Auth and bootstrap-value lane

## Status and boundary

This is a source-only, separately guarded secret-zero lane. It has not contacted
Infisical, a Kubernetes API, an inventory host, a Keychain, a registry, or an
account. It adds no Infisical account, identity, project, environment, CR, workload,
route, database, PVC, or committed Secret value. Runtime remains
**NOT RUN/BLOCKED**.

The canonical value-free contract is
[`infisical-secret-zero-lane.yml`](../ansible/files/policies/infisical-secret-zero-lane.yml).
The existing Argo CD and shared-database seams consume the exact identifiers in that
policy. The seed writer creates only these three same-Namespace `Opaque` Secrets:

| Namespace/name | Exact keys | Labels |
| --- | --- | --- |
| `argocd/argocd-infisical-universal-auth` | `clientId`, `clientSecret` | `app.kubernetes.io/managed-by=ansible`, `app.kubernetes.io/part-of=infisical-operator`, `cristex.io/component=infisical-runtime-auth`, `cristex.io/value-owner=infisical-cloud` |
| `shared-services/shared-postgresql-infisical-universal-auth` | `clientId`, `clientSecret` | same four exact labels |
| `shared-services/shared-mongodb-infisical-universal-auth` | `clientId`, `clientSecret` | same four exact labels |

The writer never creates target application/database Secrets, Infisical custom
resources, namespaces, workloads, Services, policies, or routes. Infisical Cloud
owns the values; Ansible owns this one-time Kubernetes seed boundary until a later
object-specific handoff.

## Fixed out-of-band identities and paths

A human administrator must create the six identities and the project/environment
out of band. This lane does not create, delete, broaden, or revoke identities or
projects. Each component has two distinct identities:

- a read-only runtime identity used by its Kubernetes `InfisicalAuth`; and
- a separate write-capable bootstrap identity used only by the protected controller
  uploader.

Runtime credentials are never reused for upload, and one component's credentials
are never used for another component. The fixed value destination is:

- project slug `cristexweb-infrastructure`;
- environment slug `bootstrap`;
- Argo CD path `/argocd`;
- PostgreSQL path `/shared-services/postgresql`; and
- MongoDB path `/shared-services/mongodb`.

The current database materialization seam uses the exact PostgreSQL and MongoDB
identities and paths above. The Argo seam uses the exact Argo identity and path.
The seven logical-consumer credential reservations are in scope for value
materialization, but both PROD reservations remain inactive and do not authorize
any PROD workload, Namespace, migration, route, or traffic. The value-free policy
records the protected controller lane as the sole generator/uploader; provisioning
roles cannot generate or rotate values.

## Protected controller inputs

The seed entrypoint accepts no credential values on its command line or in its
process environment. It reads one JSON object per component from the controller's
mode-`0600` protected directory, or from the equivalent login-Keychain item:

```text
~/Library/Application Support/CristexWeb/infisical/universal-auth/argocd-runtime.json
~/Library/Application Support/CristexWeb/infisical/universal-auth/postgresql-runtime.json
~/Library/Application Support/CristexWeb/infisical/universal-auth/mongodb-runtime.json
```

Each input object has exactly `clientId` and `clientSecret`, both non-empty strings
without control characters. The uploader uses separate `*-writer.json` inputs in
the same protected directory. The fixed Keychain services are:

```text
cristexweb-infisical-universal-auth-argocd-runtime
cristexweb-infisical-universal-auth-postgresql-runtime
cristexweb-infisical-universal-auth-mongodb-runtime
cristexweb-infisical-universal-auth-argocd-writer
cristexweb-infisical-universal-auth-postgresql-writer
cristexweb-infisical-universal-auth-mongodb-writer
```

Protected files and all parent directories must be owned by the controller user,
with directory mode `0700` and file mode `0600`; symlinks, group/world access,
foreign ownership, extra JSON fields, duplicate inputs, malformed JSON, and control
characters are refused. The wrapper passes only a protected vars-file pathname to
Ansible. It uses a clean allowlisted environment and no `--diff`; every task that
can contain a value is `no_log: true`.

## Kubernetes seed sequence

Only this entrypoint is authorized:

```text
ansible/bin/seed-infisical-universal-auth apply
```

It is apply-only. Check mode, diff mode, passthrough arguments, tags, task
selection, direct playbook invocation, sudo, and a symlinked wrapper are refused.
The role verifies the protected kubeconfig (`root:k3s-admin`, mode `0640`), k3s and
Tailscale health, and the exact `Active` `argocd` and `shared-services` Namespaces.

Before any mutation it lists the exact credential identities and the complete
`cristex.io/component=infisical-runtime-auth` inventory in both Namespaces. It
refuses missing, foreign, partial, extra, immutable, owner-referenced,
wrong-type, wrong-key, wrong-label, `binaryData`, or value-mismatched state. A
first seed therefore has all three Secrets absent; a retry is idempotent only when
all three existing values and metadata match the same protected input. No partial
recovery or implicit overwrite is permitted. Post-state is compared in memory and
never printed.

## Generated value sets and upload

Only this controller entrypoint is authorized for value generation/upload:

```text
ansible/bin/upload-infisical-bootstrap-values apply
```

It accepts only `apply` and reads writer credentials, endpoint configuration, and
any existing recovery state from protected files. Values are generated in a mode
`0700` temporary directory using pinned local tools. No value is accepted in
argv/environment, and no generated value is emitted to stdout, stderr, Ansible
output, curl diagnostics, or review artifacts.

The exact path/key sets are:

- `/argocd`: `ARGOCD_ADMIN_PASSWORD_BCRYPT`,
  `ARGOCD_ADMIN_PASSWORD_MTIME`, `ARGOCD_SERVER_SECRETKEY`, `ARGOCD_REDIS_AUTH`,
  `ARGOCD_TLS_CA_CRT`, `ARGOCD_TLS_CRT`, `ARGOCD_TLS_KEY`;
- `/shared-services/postgresql`: the five engine administrator/TLS keys plus
  `POSTGRESQL_CRISTEXHUB_DEV_USERNAME`, `POSTGRESQL_CRISTEXHUB_DEV_PASSWORD`,
  `POSTGRESQL_CRISTEXHUB_PROD_USERNAME`, `POSTGRESQL_CRISTEXHUB_PROD_PASSWORD`,
  `POSTGRESQL_REACTIVE_RESUME_DEV_USERNAME`,
  `POSTGRESQL_REACTIVE_RESUME_DEV_PASSWORD`,
  `POSTGRESQL_REACTIVE_RESUME_PROD_USERNAME`,
  `POSTGRESQL_REACTIVE_RESUME_PROD_PASSWORD`,
  `POSTGRESQL_KEYCLOAK_USERNAME`, and `POSTGRESQL_KEYCLOAK_PASSWORD`; and
- `/shared-services/mongodb`: the four engine administrator/TLS keys plus
  `MONGODB_CRISTEXHUB_DEV_USERNAME`, `MONGODB_CRISTEXHUB_DEV_PASSWORD`,
  `MONGODB_CRISTEXHUB_PROD_USERNAME`, and `MONGODB_CRISTEXHUB_PROD_PASSWORD`.

The seven consumer targets are `shared-postgresql-cristexhub-dev`,
`shared-postgresql-cristexhub-prod`, `shared-postgresql-reactive-resume-dev`,
`shared-postgresql-reactive-resume-prod`, `shared-postgresql-keycloak`,
`shared-mongodb-cristexhub-dev`, and `shared-mongodb-cristexhub-prod`. Usernames
are fixed logical principals; passwords are generated only in the protected
bundle. The two PROD targets are inactive reservations only.

The Argo administrator hash is bcrypt cost 12 and its timestamp is UTC RFC3339.
Argo and both database TLS leaves have exactly their reviewed DNS SAN sets,
`serverAuth`, a direct verified CA, matching private keys, SHA-256/384/512
certificate signatures, and at least 24 hours of remaining validity. MongoDB's
`MONGODB_TLS_PEM` is exactly one leaf certificate followed by its one private key;
its CA is separate. The generator uploads each generated value only to its
fixed component path and never to an unrelated path. Consumer usernames remain
fixed logical principals; consumer passwords are generated in the protected
bundle and uploaded as Infisical-owned values.

The uploader performs metadata-only project/environment/path/key preflight, refuses
foreign, partial, extra, or previously populated remote state without a matching
protected pending marker, and submits one exact batch per path. Each upload response
must contain the exact expected key closure and a non-null revision/version marker
before progress advances. If a POST may have succeeded but its response/progress write
was interrupted, a retry sees populated remote keys while the component remains pending
and stops as `UNKNOWN — STOP`; it never blindly overwrites or declares success. That
state requires separately reviewed, value-preserving recovery against verified vendor
metadata/revision semantics. Login request bodies, Bearer headers, upload bodies, API
responses, and diagnostics are protected files; `curl` receives only file paths
(`--data-binary @file`/protected config), with TLS verification enabled. The API
endpoint/schema remains a future separately verified vendor contract; no live request
or fake server is part of this source-only checkpoint.

## Recovery, cleanup, and rotation

The temporary directory and every plaintext generated/input derivative are removed
on success, failure, interruption, and signal. A generated bundle is encrypted
before it is retained. Only one exact encrypted pending artifact, its checksum, a
mode-`0600` pending/progress marker, and a completed marker may remain under:

```text
~/Library/Application Support/CristexWeb/recovery/infisical-bootstrap-values/
```

The age identity is held separately in the controller's protected age directory and
login Keychain; it never reaches a host or Infisical. A pending run resumes only the
same artifact after checking its filename, checksum, encrypted decrypt, project,
environment, path, identity, and key-set bindings. Missing or mismatched custody,
checksum, marker, API revision, or path state is **UNKNOWN — STOP**.

A completed marker refuses implicit regeneration or rotation. There is no `--rotate`
flag. Replacing a value or identity requires a separately reviewed, expiring
protected authorization, a new successor identity, overlap proof, exact Kubernetes
Secret update, operator/materialization health, and an independently approved
predecessor revocation. Runtime identity rotation and writer identity rotation are
separate operations. Routine rollback never deletes a Kubernetes Secret, Infisical
key, CR, Namespace, PVC, or identity.

The Kubernetes seed wrapper also fails closed unless two controller-owned mode-`0600`
sanitized evidence files exist. `k3s-datastore-preflight.local.json` must be schema 1,
identify a known datastore, report encryption `enabled` with rotation `finished`, and
contain no Secret, key, or token material. The separately reviewed
`k3s-secret-encryption-recovery.local.json` must use evidence class
`k3s-secret-encryption-recovery-attestation`, bind the exact SHA-256 of that preflight,
its exact k3s version and datastore type, and attest compatible backup, key recovery,
and isolated restore with all value-disclosure flags false. It has an exact key closure,
UTC `attested_at_utc` and `expires_at_utc` fields, and a maximum 24-hour validity
window; expired, future-dated, overlong, stale, or cross-preflight evidence fails closed.
No source in this lane creates that recovery attestation. Until datastore-specific backup
and isolated restore prove it, the file is absent and every credential-bearing Kubernetes
Secret write is blocked.

## Validation boundary

Offline tests use synthetic values and source-level request/response contracts only;
they do not start an Infisical-compatible endpoint or make a network request. The
focused controller-only commands are:

```bash
uv run --offline python -m unittest -v tests.test_infisical_secret_zero_lane_contract
sh -n ansible/bin/seed-infisical-universal-auth ansible/bin/upload-infisical-bootstrap-values
sh -n tests/reject_infisical_universal_auth_seed_task_start.sh tests/reject_infisical_values_upload_passthrough.sh
python3 -m compileall -q tests ansible/plugins/action
```

They prove exact routing, file-only request handling, TLS/bcrypt/key contracts,
no-secret output, cleanup, foreign-state refusal, pending recovery, and rotation
refusal. They do not
prove account permissions, project existence, API compatibility, Kubernetes
admission, operator readiness, Secret encryption at rest, database provisioning,
or any live identity/recovery result. Those remain **NOT RUN/BLOCKED** and require
separate approvals.

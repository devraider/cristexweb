# CristexHub PROD MongoDB credential rotation

Status: **SOURCE-ONLY METADATA PREFLIGHT / NOT RUN / BLOCKED**.

This is a dedicated, check-only lane for the exposed CristexHub PROD MongoDB
consumer credential. It does not write Infisical, call a value-bearing Infisical
endpoint, read Kubernetes Secret data, patch a Kubernetes Secret, create/delete
a MongoDB user, restart a workload, revoke a predecessor, or change DNS. It
must never print a password, URL, token, Secret `data`, authorization material,
or a response body containing any of those values.

The only entrypoint is:

```text
ansible/bin/check-cristexhub-prod-mongodb-credential-rotation check
```

There is intentionally no `apply` mode. The wrapper binds a clean controller,
canonical inventory/configuration, exact source hashes, one host, check/diff
mode, and a one-run attestation. The role performs metadata-only Kubernetes
requests for the two Infisical source objects and two materialized target
Secrets. Secret requests negotiate `PartialObjectMetadata`; ordinary Secret
JSON is forbidden. Deployment and Argo status requests contain no Secret
values and are used only as bounded readiness preflight.

## Frozen exact scope

| item | exact contract |
|---|---|
| Infisical project | `619656da-14f3-4872-857b-be103cdc5326` |
| environment | `prod` |
| engine source | `prod:/shared-services/mongodb`, recursive `false` |
| engine source keys | `MONGODB_CRISTEXHUB_PROD_USERNAME`, `MONGODB_CRISTEXHUB_PROD_PASSWORD` |
| runtime URL source | `prod:/cristexhub/prod/runtime`, recursive `false` |
| runtime URL key | `MONGODB_URL` |
| engine target | `shared-services/shared-mongodb-cristexhub-prod`, `Opaque`, `username`/`password` |
| runtime target | `cristexhub-prod/cristexhub-prod-runtime`, `Opaque`, `MONGODB_URL` among the exact ten-key runtime contract |
| consumers | `cristexhub-prod/backend` and `cristexhub-prod/celery-worker` |
| database | `cristexhub_prod` over authenticated TLS/SCRAM |

The source path and runtime URL path are separate source state machines. The
engine target is the consumer credential projection; the runtime URL is a
separate derived projection. Updating one path without the other is an
invalid partial rotation.

## Metadata-only revision and CAS contract

The preflight records, without values:

- each `InfisicalStaticSecret.metadata.resourceVersion` as the Kubernetes
  observation for its source object;
- each target Secret's
  `metadata.annotations['secrets.infisical.com/version']` as the Operator
  materialization observation;
- exact source/target identity, UID, owner labels, and resourceVersion.

These observations are **not** an Infisical Cloud revision and do not prove a
conditional write. The repository has no reviewed Infisical API CAS or
`If-Match` contract for either path. Therefore both path CAS states are
`unavailable`, source writing is `forbidden`, and the preflight ends with
`NOT-RUN-BLOCKED`. A future writer must independently capture and compare the
expected revision for `/shared-services/mongodb` and `/cristexhub/prod/runtime`,
update only the reviewed keys, preserve all unrelated keys, and prove
conditionality for each write. A timeout, lost response, revision mismatch, or
uncertain cross-path ordering is `UNKNOWN-STOP`; never retry blindly and never
claim rollback from an ambiguous result. Cross-path atomicity must not be
assumed.

The Infisical Operator remains the only Kubernetes value owner. Its source CRs,
materialization annotations, and controller readiness are inspected only as
metadata/status. No direct Kubernetes Secret writer is permitted.

## Required future sequence (not executable here)

1. **Protected metadata preflight.** Bind the canonical checkout, exact paths,
   target types/key closure, source and target ownership, non-terminating UIDs,
   source observations, target materialization versions, healthy Operator,
   healthy backend/Celery Deployments, private direct-server Argo `Synced` /
   `Healthy`, and the exact MongoDB NetworkPolicy preflight: both
   source-pinned policies must exist in `shared-services`, have the exact
   MongoDB pod selector/spec/labels, be non-terminating, and no foreign policy
   may overlap that selector. Never read a Secret body to identify the
   predecessor.
2. **Recovery gate.** Before any source write, obtain a fresh encrypted,
   immutable MongoDB backup/readback and isolated restore rehearsal covering the
   relevant PROD data. Preserve protected predecessor recovery custody and
   separately prepare protected successor custody. A database restore is not a
   credential restore; losing the principal/password or its authorization
   contract is not repaired by restoring data. Cleanup-first mode `0600` and
   zero plaintext residue are mandatory.
3. **Database principal operation.** Through a separately reviewed MongoDB
   administrator lane, create or prepare the same reviewed consumer principal
   with the successor credential. Do not use the administrator Secret in a
   workload. Require authenticated TLS/SCRAM, exact `cristexhub_prod` database
   authorization, no DEV/cross-database access, and persistence across the
   accepted MongoDB restart boundary. This lane contains no MongoDB admin
   command and cannot perform this step.
4. **Two-path conditional source cutover.** Under a separately approved writer,
   use expected-revision/CAS for both exact Infisical paths. The engine path and
   runtime URL path must be correlated by a sanitized rotation ID and expected
   revisions. If either write is ambiguous or the second path cannot be
   conditionally applied, stop `UNKNOWN-STOP`; do not silently complete only one
   path. The Operator must reconcile both target projections.
5. **Consumer restart/readiness.** Only after both projections reconcile, restart
   exactly `backend` and `celery-worker` through their reviewed owner path. Do
   not restart frontend, oauth2-proxy, Redis, MongoDB, or unrelated workloads.
   Require new Pod UIDs owned by the expected Deployment/ReplicaSet, both
   Deployments Ready and healthy, MongoDB TLS/SCRAM connection evidence without
   printing URLs/passwords, and Argo `Synced/Healthy`. Deployment readiness
   before cutover is not successor acceptance.
6. **Authentication and authorization negatives.** Run a protected TLS/SCRAM
   probe with value-bearing material kept out of argv/environment/logs. Prove
   positive access only to `cristexhub_prod`, denial for DEV/other databases,
   denial of admin/user-management operations, TLS verification, and NetworkPolicy
   enforcement. A rejected authorization operation proves authorization denial;
   it does not prove predecessor authentication revocation. This preflight intentionally
   reports `auth-negative-validation: NOT-RUN-BLOCKED`.
7. **Separate predecessor revocation.** Keep the predecessor untouched until
   successor database authorization, both source projections, new consumer UIDs,
   readiness, Argo health, recovery, and negative tests pass. Removing a role's
   permissions and observing authorization denial is a separate result from
   deleting/revoking the credential. Predecessor permission removal and final
   authentication revocation each require separate explicit approvals and a
   fresh login-failure proof. This lane performs neither and reports
   `SEPARATE-APPROVAL-REQUIRED`.
8. **Custody closure.** Remove temporary plaintext, rejected bundles, and
   transient credentials. Retain only approved encrypted recovery leaves and a
   sanitized receipt containing timestamps, identities, revisions, UIDs, and
   booleans—not values.

## Failure, rollback, and recovery boundaries

The rotation is non-atomic across MongoDB, two Infisical paths, Operator
reconciliation, Kubernetes Pods, and Argo. If the source writer changes the
engine path but not the runtime URL path, or reconciliation/restart fails, the
system may be mixed. Stop with `UNKNOWN-STOP`; do not infer success from one
Secret annotation or one Ready Deployment.

Rollback requires all of the following before it is considered available:

- encrypted predecessor and successor custody, independently recoverable;
- fresh backup/readback and isolated restore proof;
- the exact expected revision for the current source path;
- proven CAS writer access to restore source keys while preserving unrelated keys;
- the MongoDB principal and authorization contract restored separately;
- Operator reconciliation of both target projections;
- bounded consumer readiness and fresh Argo health.

Restoring source text alone is not rollback: it cannot restore a MongoDB
principal, revoke a successor, repair a mixed two-path update, or prove consumer
connections. After predecessor permissions are removed or the predecessor is
revoked, recovery requires a new separately approved credential operation. An
ambiguous response never authorizes a destructive retry or an automatic delete.

## Current result and approval boundaries

The dedicated check-only lane may establish only metadata/source closure and
current readiness. It truthfully remains blocked because Infisical CAS is not
proven, no value-bearing successor writer exists, recovery evidence is not
bound to this lane, authentication/authorization negatives are not run, and
predecessor revocation is separately gated.

Required future approvals are distinct:

- MongoDB principal preparation and exact authorization probes;
- fresh backup/readback and isolated restore;
- a two-path Infisical writer with expected-revision/CAS evidence;
- Operator reconciliation and exactly two consumer restart/readiness checks;
- protected authentication/authorization negative probes;
- predecessor permission removal, then predecessor credential revocation;
- final private PROD acceptance and public-route gate.

No Kubernetes apply, Infisical mutation, MongoDB credential command, Secret
export, DNS operation, Cloudflare operation, or public cutover is authorized by
this source-only lane.

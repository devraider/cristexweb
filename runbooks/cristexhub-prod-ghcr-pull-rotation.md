# CristexHub PROD GHCR pull credential rotation preflight

Status: **SOURCE-ONLY / CHECK-ONLY / NOT RUN / BLOCKED**.

This runbook defines the separate, value-free preflight for replacing the
private GitHub Container Registry credential used by CristexHub PROD. It does
not create a successor token, call GitHub, call Infisical, read a Kubernetes
Secret value, patch a Secret, restart a Deployment, revoke a registry token,
or authorize public exposure. Specifically, it does not call GitHub, does not
call Infisical, does not restart a Deployment, and does not revoke a registry
token.

The machine-readable contract is
[`ansible/files/policies/cristexhub-prod-ghcr-pull-rotation.yml`](../ansible/files/policies/cristexhub-prod-ghcr-pull-rotation.yml).
The guarded source entrypoint is
`ansible/bin/check-cristexhub-prod-ghcr-pull-rotation` and its only accepted
argument is `check`.

## Frozen custody and target contract

The value owner is Infisical Cloud, project
`619656da-14f3-4872-857b-be103cdc5326`, environment slug `prod`, path
`/cristexhub/prod/runtime`, non-recursive, source key `DOCKER_CONFIG_JSON`.
The Infisical source declaration is the existing
`InfisicalStaticSecret/cristexhub-prod-runtime` in namespace
`cristexhub-prod`; this preflight inspects that non-Secret declaration only.

Its exact target declaration is:

- `cristexhub-prod-ghcr-pull` in `cristexhub-prod`;
- Secret type `kubernetes.io/dockerconfigjson`;
- exactly one target key, `.dockerconfigjson`;
- `creationPolicy: Orphan`;
- labels `app.kubernetes.io/managed-by=infisical`,
  `app.kubernetes.io/part-of=cristexhub`, and
  `cristex.io/value-owner=infisical-cloud`.

The target Secret is inspected only through a Kubernetes
`PartialObjectMetadata` request. The response is required to contain only the
metadata representation, UID, resourceVersion, labels, annotations, and owner
metadata. The module rejects ordinary Secret representations and never requests,
parses, returns, logs, or compares `data`, `stringData`, or `type` from the
Secret endpoint. Type and key closure come from the value-free Infisical target
declaration above.

## Consumers and rollout gate

The exact current consumer set is five PROD Deployments:

- `backend`;
- `celery-worker`;
- `frontend`;
- `oauth2-proxy`;
- `redis`.

The preflight reads Deployment objects only to verify that each consumer:

1. has exactly one replica and is current/Ready;
2. references exactly `cristexhub-prod-ghcr-pull` as its image pull Secret;
3. uses only immutable `@sha256:<digest>` image references; and
4. is not terminating or widened by an extra Deployment.

This is an observation-only readiness gate. Its frozen status is
`FUTURE-CONTROLLED-ONE-WORKLOAD-AT-A-TIME`. A future rotation writer must retain
the captured Deployment UIDs, generations, revisions, image references, and pull
Secret name, then roll exactly one approved consumer at a time and wait for its
new ReplicaSet/Pod to be Ready before proceeding. Image digests and source
revision must remain unchanged. This source-only preflight does not perform that
rollout and cannot claim that a successor credential is pullable.

## Future replacement and revocation ownership

The registry credential has two distinct owners and operations:

- Infisical Cloud owns the source value and the conditional source update;
- GitHub Container Registry owns token issuance and predecessor revocation.

A future writer must prove a conditional Infisical update that changes only
`DOCKER_CONFIG_JSON`, preserves every unrelated key, and returns an unambiguous
new source revision. It must not write the Kubernetes target directly. The
Infisical Operator remains the sole target Secret value reconciler.

Before predecessor revocation, the operator must establish encrypted recovery
custody for both predecessor and successor metadata/material through a protected
channel, verify exact target ownership and fresh source revision, complete the
controlled rollout/readiness sequence, and prove that all five consumers still
use the same immutable images. A registry API success or a Pod readiness result
alone is not sufficient.

Predecessor revocation is a separate, explicit GitHub/provider approval. The
preflight's gate is intentionally `NOT-RUN-BLOCKED`; it cannot be changed by
extra-vars and no revoke flag is accepted. After an approved revoke, a separate
value-free test must prove fresh authentication failure for the predecessor.
Authorization denial, a missing image, or an unrelated HTTP error is not proof
of revocation. Ambiguous Infisical writes, registry responses, reconciliation,
or rollout results are `UNKNOWN-STOP` and must not trigger a blind retry.

## Safe command and evidence

After source review and explicit permission for a read-only live check, run only:

```text
ansible/bin/check-cristexhub-prod-ghcr-pull-rotation check
```

The wrapper uses a clean environment, `--check --diff`, one local host, a
single-use mode-`0600` attestation, and a pinned source closure. It performs
metadata/readiness inspection only. The output is sanitized and must contain
only identities, UIDs, resourceVersions, booleans, image-digest presence, and
workload names. It must never contain docker config JSON, tokens, passwords,
authorization headers, Secret `data`, registry response bodies, or source values.

The expected source-only result is `NOT-RUN-BLOCKED`; a passing check does not
approve credential replacement, workload rollout, predecessor revocation,
private PROD acceptance, Cloudflare planning, or public cutover.

## Required future approvals

- protected source metadata and predecessor identity check;
- encrypted recovery custody and independent restore proof;
- a source-hash-bound Infisical conditional writer preserving unrelated keys;
- controlled one-workload-at-a-time rollout and readiness approval;
- separate GitHub Container Registry predecessor revoke approval;
- fresh authentication-failure proof after revocation;
- final private PROD acceptance and all independent public-cutover gates.

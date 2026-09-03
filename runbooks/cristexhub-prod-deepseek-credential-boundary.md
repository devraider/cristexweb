# CristexHub PROD DeepSeek credential boundary

Status: **SOURCE-ONLY / VALUE-FREE / NOT RUN / BLOCKED**.

This runbook defines the boundary for the exposed DeepSeek predecessor. It does
not revoke, issue, copy, inspect, or test a credential. It adds no provider
client, Infisical writer, Kubernetes Secret, workload rollout, OpenTofu change,
DNS change, or public route. The machine-readable contract is
[`ansible/files/policies/cristexhub-prod-deepseek-credential-boundary.yml`](../ansible/files/policies/cristexhub-prod-deepseek-credential-boundary.yml).

## Ownership boundary

The DeepSeek account owner owns provider API-key lifecycle. The CristexHub
application owner owns the application secret source, its deployment revision,
and consumer configuration. This infrastructure repository owns only the
value-free evidence boundary and the existing HTTPS transport policy.

The existing OIDC CONNECT proxy permits only the reviewed destination
`api.deepseek.com:443`. Its unauthenticated `/models` response is transport
smoke only; it is not proof that a DeepSeek API key is valid, revoked, or
replaced. No provider account, provider credential, application key, or
application secret manager is owned or identified by this repository.

The current Infisical project context is known for other infrastructure lanes:
project `cristexweb-infrastructure`, project ID
`619656da-14f3-4872-857b-be103cdc5326`, environment slug `prod`. That context is
not proof that the DeepSeek key is stored there. The checked-in
`cristexhub-prod-runtime` source has no DeepSeek key mapping, and this repository
must not add one merely to close this residual.

## Exact target discovery, without values

Before any replacement work, a separately protected application-owner
investigation must identify exactly one source and exactly one consumer mapping.
The investigation may record metadata only:

1. application repository and deployed PROD revision;
2. exact PROD workload and environment-variable/configuration key name;
3. secret-manager owner and immutable target identifier;
4. if and only if Infisical is confirmed by the application owner: project ID,
   environment slug, non-recursive secret path, key name, source revision,
   materialization target name/type, owner labels, and target resource version;
5. provider account metadata and the predecessor key identifier/fingerprint,
   without key material; and
6. the intended successor source revision and application deployment revision.

A target is exact only when the owner attestation supplies one complete source
path/key and one complete materialized target (or explicitly proves a different
application-owned secret manager). A guessed path, a runtime URL, a Kubernetes
Secret value, a decoded or base64 field, an authorization header, or a key
fingerprint derived from reading the secret is not discovery evidence. Ordinary
Kubernetes Secret JSON and Infisical secret values must never be requested.

If the owner, provider account, application target, Infisical target, source
revision, or predecessor identity is unknown, stop. Do not infer that the key
is under `/cristexhub/prod/runtime`, do not add `DEEPSEEK_API_KEY` to the
infrastructure StaticSecret, and do not use the shared runtime Secret as a
rollback shortcut.

## Required external actions

The DeepSeek account owner must, through the protected provider console or an
official provider API owned by that account holder:

- prove account ownership;
- revoke the exposed predecessor;
- issue the provider successor; and
- return a sanitized receipt containing metadata, timestamps, and boolean
  outcomes only.

The application owner must identify and update the exact application-owned
source, preserve unrelated keys, reconcile the successor to the private PROD
consumer, and provide a value-free private authenticated-health receipt. These
actions belong to the application/provider owners, not this repository.

This infrastructure repository has no provider authority or provider
credential. Provider revocation from here is **forbidden unless ownership is
proven** through a later explicit architecture decision, protected account
ownership and permission metadata, a dedicated source-hash-bound guarded lane,
and a separate revocation approval. No such exception implementation exists
here. A check result from this source can never itself authorize provider
revocation.

## Check-only evidence contract

The boundary is **NOT RUN / BLOCKED**. A future check-only evidence bundle may
contain only sanitized metadata and booleans:

- owner and provider-account ownership proved;
- exact application target proved;
- exact Infisical target proved, if Infisical is the confirmed owner;
- predecessor identity proved;
- successor issued and reconciled;
- private authenticated successor probe passed;
- predecessor revoked;
- fresh authentication with the predecessor failed;
- plaintext residue absent; and
- source/application/provider revisions and materialized target resource
  version.

It must not contain values, Secret data, tokens, passwords, connection strings,
request/response bodies, cookies, authorization headers, or provider output.
No provider, Infisical, Kubernetes, OpenTofu, DNS, or workload mutation is part
of this source-only boundary. Transport status alone, including HTTP `401`, is
not a revocation proof.

## Mandatory order and stop states

The non-atomic sequence is:

1. prove the external application owner and DeepSeek account owner;
2. discover the exact application and optional Infisical target by metadata only;
3. establish encrypted predecessor/successor custody and cleanup boundaries;
4. have the DeepSeek account owner issue the successor;
5. reconcile the successor through the application-owned source;
6. pass a private authenticated successor probe;
7. obtain separate approval for predecessor revocation;
8. have the DeepSeek account owner revoke the predecessor;
9. prove fresh predecessor authentication failure; and
10. remove plaintext residue and retain only sanitized receipts.

Stop immediately with one of these states when its condition is encountered:

- `OWNER-UNKNOWN-STOP` or `PROVIDER-ACCOUNT-UNKNOWN-STOP`;
- `APPLICATION-TARGET-UNKNOWN-STOP` or `INFISICAL-TARGET-UNKNOWN-STOP`;
- `PREDECESSOR-UNKNOWN-STOP`, `SUCCESSOR-UNKNOWN-STOP`, or
  `CUSTODY-UNKNOWN-STOP`;
- `REVISION-UNKNOWN-STOP` or `PROVIDER-REVOCATION-UNKNOWN-STOP`;
- `AUTHENTICATION-ACCEPTANCE-UNKNOWN-STOP`;
- `AMBIGUOUS-WRITE-UNKNOWN-STOP`;
- `PLAINTEXT-RESIDUE-STOP`; or
- `PUBLIC-CUTOVER-STOP`.

A timeout or ambiguous provider/application result is not success and is not
rollback evidence. Never claim predecessor revocation from authorization
failure, an unauthenticated transport `401`, or a Kubernetes readiness result.

## PROD public-cutover gate

`hub.cristex-soft.com` remains private and the Cloudflare route remains
unapplied. Public cutover is forbidden until the external owner/account path is
proven, the exact application or Infisical target is proven, the provider
successor is privately authenticated, the predecessor is separately revoked
and fails authentication, all other credential rotations and MongoDB
NetworkPolicy enforcement pass, private PROD acceptance passes, and the exact
protected Cloudflare plan/state recovery gates pass.

Nothing in this document authorizes a provider call, Infisical call, Kubernetes
operation, DNS change, Cloudflare operation, secret rotation, workload rollout,
or public cutover.

## Offline validation

The dedicated contract test checks the value-free policy and this runbook. It
is source validation only; no provider, Infisical, Kubernetes, DNS, OpenTofu, or
runtime operation is implied.

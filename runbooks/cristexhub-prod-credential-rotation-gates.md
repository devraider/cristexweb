# CristexHub PROD credential-rotation gates

Status: **SOURCE-ONLY CONTRACT / NOT RUN / BLOCKED**.

This runbook freezes the safe order for the four residual credential actions
identified during private PROD review. It adds no writer, broker/database
administrator, registry client, Kubernetes Secret mutation, Infisical API call,
provider call, workload rollout, or public route. Values, tokens, passwords,
connection strings, hashes, cookies, and authorization material are absent from
this document and must remain absent from all evidence.

The machine-readable contract is
[`ansible/files/policies/cristexhub-prod-credential-rotation-gates.yml`](../ansible/files/policies/cristexhub-prod-credential-rotation-gates.yml).
The existing RabbitMQ design remains canonical for its detailed successor-user
sequence; this document does not replace or widen it.

## Exact residual scopes

| Residual | Value owner and source | Existing target | Consumer | Current blocker |
|---|---|---|---|---|
| MongoDB URL credential | Infisical `prod:/shared-services/mongodb` | `shared-mongodb-cristexhub-prod`, keys `username`/`password` | PROD runtime `MONGODB_URL`, database `cristexhub_prod` | no dedicated writer/CAS or proven authorization/recovery lane |
| RabbitMQ URL credential | Infisical `prod:/shared-services/rabbitmq` | `shared-rabbitmq-cristexhub-prod`, keys `username`/`password`/`passwordHash` | PROD runtime `RABBITMQ_URL`, vhost `/cristexhub-prod` | definitions recovery, message disposition, least-privilege proof, and writer/CAS are blocked |
| GHCR pull credential | Infisical `prod:/cristexhub/prod/runtime`, key `DOCKER_CONFIG_JSON` | `cristexhub-prod-ghcr-pull`, `.dockerconfigjson` | the five existing PROD image consumers | registry revocation/successor custody and writer/CAS are blocked; image digests must not change |
| DeepSeek API key | owner/source not identified in this infrastructure repository | no target in this repository | PROD application through exact proxy destination `api.deepseek.com:443` | provider-side revocation and the application-owned successor path are unknown |

The DeepSeek row is intentionally unresolved. The infrastructure repository must
not invent a path, add `DEEPSEEK_API_KEY` to the runtime seam, or copy an
application secret into this repository. First identify the owning application
secret manager and provider account through a separate protected investigation;
then revoke the exposed predecessor and prove a provider-issued successor without
outputting either value.

## Required common sequence

Every rotation is a separate non-atomic state machine. The following gates are
mandatory for each applicable residual:

1. **Protected metadata preflight.** Confirm the exact source path, target name,
   target type/key closure, owner labels, source revision, and current predecessor
   identity from metadata only. Never request ordinary Kubernetes Secret JSON,
   decode `data`, infer a username from a Secret, or read a URL to recover a
   predecessor.
2. **Recovery before mutation.** Establish encrypted predecessor and successor
   custody, independent recovery, and a cleanup-first mode-`0600` boundary. A
   definitions backup does not recover RabbitMQ queued messages; database or
   application recovery is separate. If recovery, ownership, or source revision is
   unknown, stop with `UNKNOWN-STOP`.
3. **Conditional source write.** A dedicated writer must prove an expected-revision
   or conditional-write/CAS protocol and preserve every unrelated key. Infisical
   has no assumed CAS contract here. A timeout, ambiguous response, one-key write,
   or returned revision without an atomicity proof is `UNKNOWN-STOP`; do not retry
   blindly or claim rollback.
4. **Owner-controlled reconciliation.** The Infisical Operator remains the sole
   Kubernetes Secret value owner. No direct `kubectl`, Ansible, Argo, or helper
   Secret patch is allowed. Reconciliation must be checked through exact target
   metadata and bounded new Pod UIDs before any predecessor revocation.
5. **Private acceptance before revocation.** Prove the exact PROD consumer is
   Ready, the relevant database/broker authorization and cross-environment
   negatives pass, the required NetworkPolicy is enforced, and Argo is
   `Synced/Healthy`. A readiness result alone is not credential acceptance.
6. **Separate revocation proofs.** A denied operation proves authorization denial,
   not authentication revocation. Remove predecessor permissions first only when
   the protocol explicitly requires it; delete/revoke the predecessor only under a
   distinct approval, then prove fresh authentication failure.
7. **Custody closure.** Remove plaintext temporary material and rejected bundles,
   retain only explicitly approved encrypted recovery leaves, and emit sanitized
   timestamps, identities, revisions, and boolean results. Never record values.

## Residual-specific gates

### MongoDB

The successor must preserve the same reviewed application principal unless a
separate identity decision approves otherwise. Before source cutover, the
operator must have a fresh encrypted backup/readback and isolated restore for the
relevant application data, exact MongoDB TLS/SCRAM and database authorization
proof, and the shared MongoDB deny-first NetworkPolicy plus positive/negative
reachability tests. `shared-mongodb-networkpolicy` is a separate apply gate and
must not be folded into credential rotation. The database administrator credential
is never exposed to a workload and is not a rollback shortcut.

### RabbitMQ

Follow [`cristexhub-prod-rabbitmq-credential-rotation.md`](cristexhub-prod-rabbitmq-credential-rotation.md):
first prove the actual Celery resource set and least-privilege permissions, then
prepare an overlapping successor, reconcile the source-owned URL, roll only the
required PROD consumers, and distinguish predecessor authorization denial from
authentication revocation. The current observed principal discrepancy and broad
permission expressions are hard stops. Definitions/policies recovery and queued
message reconciliation are separate hard preconditions.

### GHCR

The successor must be scoped only to the private GHCR registry and must not alter
any deployed image digest or source revision. The source writer must preserve all
unrelated `/cristexhub/prod/runtime` keys and update only `DOCKER_CONFIG_JSON`
through a proven conditional write. Before predecessor revocation, prove that all
five existing PROD consumers pull/continue to run from the same immutable image
references and that the materialized target is owned by Infisical. A registry
credential acceptance test must not print the docker config, token, authorization
header, or registry response body.

### DeepSeek

No rotation implementation is authorized here. The current proxy source proves
only transport to `api.deepseek.com:443`; an unauthenticated `401` is transport
smoke, not API authorization. Do not add a provider key to infrastructure source,
Kubernetes manifests, OpenTofu, CI, or evidence. Provider revocation, successor
issuance, application-owner reconciliation, and a value-free private API health
check require their own reviewed lane.

## Public route and MongoDB policy gates

The Cloudflare PROD route remains a separate final gate. Before any protected plan,
first complete the exact six-address foundation state import and its encrypted
backup/readback/isolated-restore checks. The plan must contain only:

1. the reviewed Tunnel configuration ingress addition for
   `hub.cristex-soft.com`; and
2. creation of `cloudflare_dns_record.cristexhub_prod` as the exact proxied CNAME.

A DNS-capable provider credential, no replacement/destroy actions, an exact plan
review, private PROD acceptance, and separate public-cutover approval are required.
No credential rotation, policy apply, state import, provider plan, or public route
is run by this source-only contract.

The source-only MongoDB NetworkPolicy closure remains independently check-ready
and apply-gated. Its two policies select only the live operator labels, default
deny both directions, and allow the reviewed DEV/PROD client and DNS/replica-set
flows. Applying the policies and running enforcement probes are separate approvals;
source presence or a policy listing alone never proves enforcement.

## Required future approval gates

- dedicated source-hash-bound MongoDB rotation writer, protected metadata-only
  preflight, conditional write, recovery, and authorization tests;
- the separately reviewed RabbitMQ rotation lane and definitions/message recovery;
- registry revocation and GHCR successor custody plus a source-hash-bound writer;
- identification and provider revocation of the exposed DeepSeek predecessor;
- shared MongoDB NetworkPolicy check, apply, and positive/negative enforcement
  probe approvals;
- six-address Cloudflare foundation import approval, then a separate exact PROD
  plan review and separate public cutover approval;
- final private PROD acceptance with all database/broker/registry/key negatives,
  Argo health, immutable image identity, backup/restore, and rollback evidence.

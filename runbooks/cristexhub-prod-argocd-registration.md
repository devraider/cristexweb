# CristexHub PROD Argo registration and private activation

Status: **SOURCE FIX READY / HISTORICAL REGISTRATION APPLIED / LIVE STATUS UNKNOWN / RECONCILIATION APPLY PENDING / PUBLIC ROUTE PENDING**.

The historical five-object closure remains present and the private PROD
workloads are currently Ready at the pinned revision, but the live Argo
Application is `Unknown/Missing` with a ComparisonError because the old
server-based destination does not resolve the scoped cluster registration. The
committed source now targets the exact `cristexhub-prod-local` cluster alias;
that correction is source-only until a separately approved registration apply.
The guarded live apply must restore `Synced/Healthy` and fails closed while the
Application remains `Unknown`. This source change does not create the Namespace,
own application Secret values, publish images, change databases, or add the
Cloudflare route.

## One-time legacy destination transition

The first alias correction is deliberately a one-time, two-object transition.
The guarded role permits only the existing `Application` and `AppProject` when
both live objects still match the previously committed server-destination
manifests byte-for-byte at the canonical spec level, retain the exact Ansible
ownership labels/empty owner and finalizer sets, and carry the pinned live UIDs
`e2016a99-2c4f-4e2e-ac28-0640cafa2a8e` (`Application`) and
`6c04c48c-7d71-46c3-b4d0-7fc9f437f5d6` (`AppProject`). The pinned legacy
manifest hashes are `29a3bd87c83d881e73f6e50739e9b510d89f58d2d851be93276658f1ad35bdf1`
(Application) and `4625c40d6030961d799f7b04b386f5a840273bc96b5d7031a507bf48ab57afa2`
(AppProject). A changed UID, any extra ownership metadata, a partial pair, or
any foreign/extra drift fails closed. The three other registration objects
remain exact present-only objects and are never part of this transition.

Check mode must predict exactly those two alias updates for the current legacy
state; apply is a separately approved mutation. Before either update, the role
binds the exact UID and `metadata.resourceVersion` for all five existing
registration objects, re-queries all five immediately before mutation, and passes
each unchanged resourceVersion in the desired object as a Kubernetes
resourceVersion optimistic-concurrency precondition. A replacement, changed resourceVersion, missing object,
partial/mixed transition, or metadata key outside the exact server-generated set
fails closed. Canonical desired hashes ignore only that one bound
`metadata.resourceVersion` field; all other desired and metadata fields remain
hash-bound. After the pair has converged, subsequent checks may be idempotent with
zero transition candidates. No delete, prune, sync, Namespace, workload, or
public-route operation is included.

## Exact source

The Argo `Application` is pinned to the reviewed protected-main CristexHub
revision `751885a42798d282e168131db147f13694a0a621`, repository
`ssh://git@ssh.github.com:443/devraider/cristexhub.git`, and path
`infra/kubernetes/cristexhub-prod`. Branch names, tags, and floating revisions
are refused.

The exact five-object registration closure is:

1. `argocd/AppProject/cristexhub-prod`;
2. `argocd/Application/cristexhub-prod`;
3. `cristexhub-prod/Role/argocd-application-controller-cristexhub-prod`;
4. `cristexhub-prod/RoleBinding/argocd-application-controller-cristexhub-prod`;
5. `argocd/Secret/argocd-cluster-cristexhub-prod`.

The cluster Secret is value-free registration metadata for the in-cluster API.
It selects only `cristexhub-prod`, has `clusterResources=false`, and contains no
token, password, kubeconfig, or private key. The separate Infisical-owned
`argocd-repository-cristexhub` Secret remains the only private Git credential;
the guarded role validates only its metadata closure.

## Fail-closed registration

`ansible/bin/bootstrap-cristexhub-prod-registration check|apply` is the only
entrypoint. It pins `/home/paul/projects/cristexweb`, rejects symlinked entrypoint
or controller paths, and uses the project `.venv`, an empty allowlisted environment,
`--diff`, one inventory host, and a private one-run attestation that is removed
when Ansible exits. Cancellation terminates the isolated controller process
group, waits with a bounded TERM-to-KILL escalation, removes the attestation,
and returns a signal-specific nonzero status.
The role checks:

- the protected regular root:`k3s-admin` mode-`0640` kubeconfig;
- the exact precreated and labelled `cristexhub-prod` Namespace;
- the exact Infisical-owned Argo repository credential metadata;
- raw manifest hashes and exact object count;
- absence of foreign objects, extra data, annotations, finalizers, metadata keys,
  or drifted fields at the five target identities;
- exact five-object UID/resourceVersion prestate binding, immediate re-query, and
  Kubernetes optimistic-concurrency preconditions for the bounded alias update;
- the exact `cristexhub-prod-local` cluster-alias destination and automated non-pruning Application policy;
- after live apply only, an Argo Application status of `Synced/Healthy`; check mode
  remains source-only and does not require live status.

The action plugin accepts only the canonical role task, exact present-only
objects, exact hashes, complete preflight binding, and wrapper attestation. It
has no delete path. The controller operating-system user remains a trusted
boundary: because that user owns the repository and Ansible process, source
cannot cryptographically distinguish the wrapper from a deliberately reproduced
canonical invocation. Human approval, reviewed source, and controller access
therefore remain mandatory rather than being replaced by the attestation.

The AppProject permits only ConfigMaps, Services, Deployments, NetworkPolicies,
and Ingresses in `cristexhub-prod`. It permits no Namespace, Secret, PVC, RBAC,
or cluster-scoped application object. Controller RBAC is namespaced and has no
`delete` verb.

The active Application source uses the exact `cristexhub-prod-local` cluster
alias with `server: ''`, `selfHeal=true`, `prune=false`, `allowEmpty=false`,
`CreateNamespace=false`, `ServerSideApply=false`, `Replace=false`, and
`FailOnSharedResource=true`. The AppProject accepts only that alias and the
`cristexhub-prod` Namespace; it does not add a second destination.

## Current registration/reconciliation status and remaining acceptance gates

The historical registration objects, Secret materialization, and private
workload readiness remain observed, but the current Application status is
`Unknown/Missing` until the alias correction is separately applied. The
private workload sync transition is therefore not currently accepted. The
corrected guarded apply must prove `Synced/Healthy` before this registration is
again treated as reconciled. The following dependency gates remain observed or
open:

- exact-main image promotion with immutable backend, frontend, and Keycloak
  evidence; current source publication governance remains a separate gate;
- separately approved Infisical Operator PROD watch/RBAC/admission expansion;
- Universal Auth and exact `cristexhub-prod-runtime` plus
  `cristexhub-prod-ghcr-pull` materialization;
- runtime engine/connectivity evidence for PostgreSQL, MongoDB, RabbitMQ, and Redis
  PROD consumers; this does not prove logical database authorization, cross-access
  negatives, backup/restore, or production scope acceptance. MongoDB private ingress
  isolation is still blocked by its NetworkPolicy gap;
- exact Keycloak `cristexhub-prod` client reconciliation plus app-level OIDC smoke;
  authenticated login/callback and live CONNECT positive/negative tests remain open;
- private workload readiness and Argo sync transition.

Public cutover remains blocked by the MongoDB NetworkPolicy apply/enforcement probe,
exposed MongoDB/RabbitMQ/GHCR/DeepSeek credential rotations, RabbitMQ identity and
permission reconciliation, complete OIDC/CONNECT validation, and finally a protected
DNS-capable Cloudflare credential plus exact two-change plan/apply.

## Offline validation

```bash
.venv/bin/python -m unittest -v tests.test_cristexhub_prod_registration_contract
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-cristexhub-prod-registration
sh -n tests/reject_cristexhub_prod_registration_resource_version.sh
tests/reject_cristexhub_prod_registration_resource_version.sh
cd ansible && ../.venv/bin/ansible-playbook playbooks/bootstrap_cristexhub_prod_registration.yml --syntax-check
```

Expected result: these offline checks pass without mutation. They validate the
alias-based source and guarded post-check only; they do not change the live
`Unknown/Missing` Application status. A separately approved registration apply
must restore and revalidate `Synced/Healthy`; no provider or Cloudflare route
mutation is performed by these offline commands.

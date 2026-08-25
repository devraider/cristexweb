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
- absence of foreign objects, extra data, annotations, finalizers, or drifted
  fields at the five target identities;
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
cd ansible && ../.venv/bin/ansible-playbook playbooks/bootstrap_cristexhub_prod_registration.yml --syntax-check
```

Expected result: these offline checks pass without mutation. They validate the
alias-based source and guarded post-check only; they do not change the live
`Unknown/Missing` Application status. A separately approved registration apply
must restore and revalidate `Synced/Healthy`; no provider or Cloudflare route
mutation is performed by these offline commands.

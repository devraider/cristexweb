# CristexHub PROD Argo registration and private activation

Status: **APPLIED / IDEMPOTENT / SYNCED / HEALTHY / PUBLIC ROUTE PENDING**.

This five-object closure now registers and continuously reconciles the private
PROD workload at the pinned revision. It does not create the Namespace, own
application Secret values, publish images, change databases, or add the
Cloudflare route. Registration apply passed, the active-state retry converged at
`changed=0`, and Argo reports `Synced/Healthy`.

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
- the exact in-cluster server destination and automated non-pruning Application policy.

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

The active Application uses `selfHeal=true`, `prune=false`, `allowEmpty=false`,
`CreateNamespace=false`, `ServerSideApply=false`, `Replace=false`, and
`FailOnSharedResource=true`. The AppProject accepts only the exact in-cluster
server and `cristexhub-prod` Namespace.

## Remaining gate after private activation

The private registration and synchronization gates below have completed:

- exact-main image promotion with immutable backend, frontend, and Keycloak
  evidence; current source publication governance remains a separate gate;
- separately approved Infisical Operator PROD watch/RBAC/admission expansion;
- Universal Auth and exact `cristexhub-prod-runtime` plus
  `cristexhub-prod-ghcr-pull` materialization;
- isolated PostgreSQL, MongoDB, RabbitMQ, and Redis PROD scopes plus recovery
  and negative cross-access evidence;
- exact Keycloak `cristexhub-prod` client reconciliation and private OIDC tests;
- private workload validation and Argo sync transition.

Cloudflare `hub.cristex-soft.com` remains the only unapplied activation phase.
Route source is committed, but provider apply still requires a protected
Cloudflare API token and exact plan review.

## Offline validation

```bash
.venv/bin/python -m unittest -v tests.test_cristexhub_prod_registration_contract
.venv/bin/python -m compileall -q ansible/plugins/action tests
sh -n ansible/bin/bootstrap-cristexhub-prod-registration
cd ansible && ../.venv/bin/ansible-playbook playbooks/bootstrap_cristexhub_prod_registration.yml --syntax-check
```

Expected result: offline checks pass; no provider, host, Kubernetes, Infisical,
Argo, Keycloak, database, broker, Secret, image, DNS, or Cloudflare mutation is
performed.

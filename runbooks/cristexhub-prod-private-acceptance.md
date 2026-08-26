# CristexHub PROD private acceptance preflight

Status: **SOURCE-ONLY / CHECK-ONLY / NOT RUN**. The credential policy status is `source-only-rotation-blocked`.

This closure is a read-only preflight for the already-approved private
`cristexhub-prod` workload. It does not create, update, delete, restart, sync,
scale, or otherwise mutate Kubernetes objects. It does not read ordinary Secret
JSON or Secret `data`, call Infisical, call OpenTofu/Cloudflare, rotate a
credential, or publish a route.

The only entrypoint is:

```text
ansible/bin/check-cristexhub-prod-private-acceptance check
```

The wrapper is non-passthrough, one-host, direct-controller `dash`, check/diff
only, and uses a single-use mode-0600 attestation. Direct Ansible invocation,
task selection, extra variables, alternate inventory, alternate kubeconfig, and
apply mode are outside this closure. Every Kubernetes query is `kubernetes.core.k8s_info`
with the protected k3s administrator kubeconfig and `check_mode: false` only to
permit read-only observation during an Ansible check run. No query requests a
Secret object.

## Exact checks

The role is bound to:

- Namespace `cristexhub-prod`, already `Active`;
- Argo `Application/cristexhub-prod` and `AppProject/cristexhub-prod` in
  `argocd`;
- direct destination `https://kubernetes.default.svc`, namespace
  `cristexhub-prod`, repository
  `ssh://git@ssh.github.com:443/devraider/cristexhub.git`, path
  `infra/kubernetes/cristexhub-prod`, and revision
  `751885a42798d282e168131db147f13694a0a621`;
- automated Argo policy `selfHeal=true`, `prune=false`, `allowEmpty=false`;
- exactly five PROD Deployments: `backend`, `celery-worker`, `frontend`,
  `oauth2-proxy`, and `redis`, each with one observed/updated/available/ready
  replica;
- exactly one Running/Ready, non-host-network Pod for each workload label;
- a stable non-empty PROD NetworkPolicy inventory; and
- host `k3s` and `tailscaled` services in the running state.

The preflight also performs content-free HTTPS probes of the private application
hostname and reviewed shared-realm OIDC discovery. The application probe accepts
only HTTP `200` or the expected unauthenticated `302` and never follows the
redirect or records response content. OIDC content is held under `no_log` and
must identify only the reviewed issuer, authorization endpoint, token endpoint,
and JWKS endpoint for realm `cristexhub`.

The result is a **preflight**, not final PROD acceptance. A successful result
proves only the above metadata/readiness and transport conditions. It does not
prove database authorization, RabbitMQ least privilege, credential rotation,
GHCR predecessor revocation, DeepSeek provider revocation, NetworkPolicy packet
enforcement, backup/restore, rollback, authenticated OIDC callback, or public
negative reachability.

## Separate mandatory gates

Before private PROD can be accepted or a public route can be considered, the
following independent evidence must be fresh and sanitized:

1. MongoDB and RabbitMQ successor credential rotations with protected custody,
   conditional source writes, least-privilege/cross-environment negatives, and
   predecessor revocation proof;
2. GHCR pull-credential replacement/revocation while preserving every deployed
   immutable image digest;
3. DeepSeek predecessor revocation and provider-issued successor through the
   application-owned secret path; this infrastructure repository has no such
   path and must not invent one;
4. shared MongoDB NetworkPolicy check, separately approved apply, and positive /
   negative enforcement probes;
5. database and broker backups, isolated restores, and declared RPO/RTO;
6. authenticated PKCE OIDC login/callback/logout, session, role, and
   cross-environment negatives;
7. the protected six-address Cloudflare foundation state import and recovery;
8. an exact two change protected PROD OpenTofu plan containing only the Tunnel
   ingress update and `cloudflare_dns_record.cristexhub_prod` create; and
9. separate public-cutover authorization after private acceptance.

No result from this preflight authorizes any of those operations. In particular,
`hub.cristex-soft.com` remains unapplied until the state, plan, provider
permission, credential, recovery, validation, and public-cutover approvals all
pass.

## Offline validation

```bash
.venv/bin/python -m unittest -v tests.test_cristexhub_prod_private_acceptance_contract
sh -n ansible/bin/check-cristexhub-prod-private-acceptance
cd ansible && ../.venv/bin/ansible-playbook playbooks/check_cristexhub_prod_private_acceptance.yml --syntax-check
```

These commands validate source only. No Kubernetes API, Secret, Infisical,
OpenTofu, Cloudflare, DNS, workload, or public route operation is implied.

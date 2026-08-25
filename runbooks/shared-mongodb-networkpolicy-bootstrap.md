# Shared MongoDB NetworkPolicy closure — source-only

Status: **SOURCE-ONLY / CHECK-READY / NOT APPLIED**.

This is a new, dedicated guarded closure for exactly two NetworkPolicies covering
only the live operator-managed `shared-mongodb` pod set in `shared-services`. It
must not be run through the legacy standalone `mongodb_bootstrap` role, plugin,
wrapper, or manifests. No apply was run for this closure.

## Exact source

The committed component is
`ansible/files/components/shared-mongodb-networkpolicy/` and contains only:

1. `NetworkPolicy/shared-mongodb-networkpolicy-default-deny`;
2. `NetworkPolicy/shared-mongodb-networkpolicy-allow`.

Both policies select exactly:

```yaml
app: shared-mongodb-svc
app.kubernetes.io/part-of: shared-databases
cristex.io/component: mongodb
```

The default policy declares both `Ingress` and `Egress` policy types and has no
allow rules. The allow policy permits only:

- ingress TCP `27017` from exactly four client selectors: `backend` and
  `celery-worker` (each requiring `app.kubernetes.io/part-of=cristexhub`) in
  each of the exact `cristexhub-dev` and `cristexhub-prod` namespaces;
- ingress TCP `27017` from the same MongoDB pod selector for replica-set traffic;
- egress TCP `27017` to that same MongoDB pod selector;
- egress TCP and UDP `53` only to CoreDNS pods (`k8s-app=kube-dns`) in
  `kube-system`.

There is deliberately **no** `mongodb-system` operator ingress exception and no
host-CIDR, NodePort, public route, Secret, Service, workload, or database source.
The MongoDB operator reconciles through the Kubernetes API; it does not need a
MongoDB TCP ingress exception.

## Guarded check entrypoint

The only entrypoint is:

```text
ansible/bin/bootstrap-shared-mongodb-networkpolicy check
```

The wrapper is check-only and rejects `apply`. It uses the pinned repository
controller, a clean allowlisted environment, one host, `--diff --check`, and a
single-use mode-`0600` attestation. The role additionally requires the protected
root:`k3s-admin` mode-`0640` kubeconfig, the established `shared-services` Namespace,
the live `MongoDBCommunity/shared-mongodb` resource with status `Running`, version
`8.0.12`, and one current member, exactly `shared-mongodb-0` owned by
`StatefulSet/shared-mongodb` and Running/Ready/nonterminating, exactly ready
backend/Celery clients in both DEV and PROD with `hostNetwork=false`, and ready
CoreDNS selected by `k8s-app=kube-dns`. It enumerates every existing
`shared-services` NetworkPolicy and fails closed on any non-target selector that can
match the live Mongo labels, including empty and expression selectors. It refuses
foreign target drift and all task-selection controls. The action plugin has an
explicit source-only guard and cannot apply in non-check mode.

The wrapper never touches the legacy five-object standalone MongoDB closure:
`ansible/bin/bootstrap-mongodb`, `mongodb_bootstrap`, and
`ansible/files/components/mongodb/` remain separate and unchanged.

## Offline validation

```bash
.venv/bin/python -m unittest -v tests.test_shared_mongodb_networkpolicy_contract
.venv/bin/python -m compileall -q ansible/plugins/action/shared_mongodb_networkpolicy_guarded_k8s.py tests/test_shared_mongodb_networkpolicy_contract.py
sh -n ansible/bin/bootstrap-shared-mongodb-networkpolicy
cd ansible && ansible-playbook playbooks/bootstrap_shared_mongodb_networkpolicy.yml --syntax-check
git diff --check
```

The hardened read-only check passed at
`ok=34 changed=1 unreachable=0 failed=0 skipped=0`; its sole predicted mutation task
contained exactly the two absent policies, and check mode made no Kubernetes change.
No apply, policy mutation, Secret read, or runtime traffic test is implied. A future
apply, if ever authorized, requires a separate explicit approval and a reviewed transition
from the check-only wrapper to a new bounded execution lane; this change does not
provide that lane.

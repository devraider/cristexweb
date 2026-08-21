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

- ingress TCP `27017` from `backend` and `celery-worker` pods in the exact
  `cristexhub-dev` and `cristexhub-prod` namespaces;
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
single-use mode-`0600` attestation. The role additionally requires the established
`shared-services` Namespace, the live `MongoDBCommunity/shared-mongodb` resource
(version `8.0.12`, one ReplicaSet member), and at least one live pod matching the
exact selector before validating the two source objects. It refuses foreign
existing policies and all task-selection controls. The action plugin has an
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

No Kubernetes apply, policy mutation, Secret read, or runtime traffic test is
implied by this source-only closure. A future apply, if ever authorized, requires
a separate explicit approval and a reviewed transition from the check-only wrapper
to a new bounded execution lane; this change does not provide that lane.

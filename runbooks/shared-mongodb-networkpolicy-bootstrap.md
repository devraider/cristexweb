# Shared MongoDB NetworkPolicy closure — source-only

Status: **CHECK-READY / APPLY-GATED / NOT APPLIED**.

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

## Guarded check/apply entrypoint

The only entrypoint is:

```text
ansible/bin/bootstrap-shared-mongodb-networkpolicy check|apply
```

`check` is the default source-only gate and uses `--diff --check`. `apply` is a
separate, explicit mutation gate: it requires the operator to set
`CRISTEXWEB_SHARED_MONGODB_NETWORKPOLICY_APPLY_APPROVED=v1`, runs without
`--check`, and still uses the same pinned repository controller, clean
allowlisted environment, one host, exact attestation, source hashes, action
plugin, and pre-state UID/resourceVersion ledger. The wrapper also acquires a portable, atomically-created cooperative lock
directory (`mkdir`) for the complete run. Its mode-0600 owner record binds the
attestation token to the live wrapper PID, Linux process starttime, and a digest
of the exact canonical `/bin/sh <wrapper> <mode>` argv. The action plugin also
verifies the wrapper executable/argv and walks PPID ancestry from the running
Ansible action back to that PID; unrelated live processes, forged lock/env
records, and direct playbook invocation fail closed. A held or stale lock fails
closed; this works on the supported Linux and macOS controller paths without
requiring a platform-specific `flock` utility. Existing targets are reconciled through one
JSON-patch request whose `test` operations condition UID, resourceVersion,
labels, and spec at mutation time. Absent targets use a focused create-only API
module: a concurrent creator returns a conflict and is never merged or updated;
the server-assigned UID/resourceVersion is required in the create result and is
bound again in the post-create ledger. The deny policy is written first, followed
by a fresh inventory/ledger refresh and the allow policy. Apply then performs a fresh namespace-wide
inventory and exact target readback, preserving existing UIDs and rejecting
foreign overlapping selectors. Direct Ansible invocation, task selection, and
an apply without that approval are refused. Neither mode reads Secret values or
invokes the legacy MongoDB closure. The role additionally requires the protected
root:`k3s-admin` mode-`0640` kubeconfig, the established `shared-services` Namespace,
the live `MongoDBCommunity/shared-mongodb` resource with status `Running`, version
`8.0.12`, and one current member, exactly `shared-mongodb-0` owned by
`StatefulSet/shared-mongodb` and Running/Ready/nonterminating, exactly ready
backend/Celery clients in both DEV and PROD with `hostNetwork=false`, and ready
CoreDNS selected by `k8s-app=kube-dns`. It enumerates every existing
`shared-services` NetworkPolicy and fails closed on any non-target selector that can
match the live Mongo labels, including empty and expression selectors. It refuses
foreign, terminating, and replacement target drift and all task-selection controls.
The action plugin requires the exact mode, approval, source, and pre-state ledger.
Before any mutation it rejects target annotations and foreign managed-field
owners, and the wrapper/action pair bind fixed hashes for the wrapper, action,
role defaults/tasks, playbook, controller, inventory, and Ansible configuration.
Role path/hash overrides and inherited controller/toolchain overrides are refused.

The wrapper never touches the legacy five-object standalone MongoDB closure:
`ansible/bin/bootstrap-mongodb`, `mongodb_bootstrap`, and
`ansible/files/components/mongodb/` remain separate and unchanged.

## Post-apply enforcement probe — separate source-only gate

There is currently **no MongoDB-specific enforcement probe implementation** in this
repository. The generic `ansible/playbooks/probe_k3s_network_policy.yml` exercise
uses synthetic policies and a synthetic server in `default`; its historical CNI
receipt is not evidence that the shared MongoDB policies select the live MongoDB
pod or enforce the DEV/PROD client boundary. Do not use that generic receipt, a
NetworkPolicy listing, or a successful MongoDB login as shared-policy enforcement
evidence. The dedicated post-apply probe remains **NOT RUN/BLOCKED** and must be
approved independently of both the NetworkPolicy apply and credential-rotation
lanes.

Before an implementation exists, the only accepted source contract for that probe
is the following. It must run only after a fresh successful NetworkPolicy apply
post-state and must never mutate the two applied policies, the MongoDB resource,
or any workload:

- Use only the already-existing `shared-services`, `cristexhub-dev`,
  `cristexhub-prod`, and `default` Namespaces. Namespace create/adoption/deletion
  is forbidden. Query the live MongoDB StatefulSet and Pod, both policy UIDs and
  resourceVersions, and the Service using metadata-only reads; never request
  Secret JSON or Secret data.
- Create only short-lived, non-root, tokenless, `hostNetwork: false` Pods with an
  independently verified immutable image. Every Pod name must come from a fixed
  lowercase DNS-1123 `generateName` prefix; caller-supplied names are forbidden.
  The run ID and both immutable ownership labels must be written before creation
  and the API-returned UID and resourceVersion must be recorded immediately in a
  private mode-`0600` ledger.
- Positive ingress checks must create four distinct temporary clients: DEV
  backend labels, DEV Celery labels, PROD backend labels, and PROD Celery labels.
  Each must prove TCP `27017` reachability to the private
  `shared-mongodb.shared-services.svc` endpoint. A separate shared-services
  helper carrying the exact live Mongo selector must prove Mongo peer TCP
  reachability and DNS resolution through CoreDNS on both UDP and TCP `53`.
  These are connectivity checks only and must not read credentials or claim
  MongoDB authorization, replica-set, or data acceptance.
- Negative checks must use foreign labels and a foreign namespace (at minimum a
  `default` client and an untrusted shared-services client) and prove that both
  cannot reach the MongoDB endpoint. A timeout, eviction, scheduling failure, or
  authentication error is not negative NetworkPolicy evidence; each Pod must
  reach an exact, bounded terminal result that distinguishes policy rejection
  from tool, image, DNS, or node failure.
- Create and delete approvals must be separate gates and separate reviewed
  check/apply transitions. Cleanup may delete only the exact generated Pod
  identities in the private ledger, after re-reading each object and verifying
  both ownership labels, UID, namespace, kind, and non-termination. Every delete
  must send the same UID as an API precondition and use non-cascading `Orphan`
  propagation. If the process stops before ledger persistence, recovery may
  discover only the fixed generated prefixes plus both immutable labels in those
  existing Namespaces, rebuild the ledger in check mode, and stop for review;
  selector-wide deletion and adoption are forbidden.
- The fixed cleanup allowlist must contain `Pod` only. It must contain no
  Namespace, Secret, PersistentVolumeClaim, Service, NetworkPolicy, or workload
  deletion path, and the probe must create no public route, NodePort, LoadBalancer,
  or tunnel. A failed positive/negative check must still enter exact cleanup and
  retain a sanitized receipt; no residual Pod or private ledger is silently
  ignored.

Until that dedicated source closure and its separate approvals exist, this runbook
claims no MongoDB NetworkPolicy enforcement result. No live enforcement probe has
been run from this source-only checkpoint.

## Offline validation

```bash
.venv/bin/python -m unittest -v tests.test_shared_mongodb_networkpolicy_contract
.venv/bin/python -m compileall -q ansible/plugins/action/shared_mongodb_networkpolicy_guarded_k8s.py tests/test_shared_mongodb_networkpolicy_contract.py
sh -n ansible/bin/bootstrap-shared-mongodb-networkpolicy
cd ansible && ansible-playbook playbooks/bootstrap_shared_mongodb_networkpolicy.yml --syntax-check
git diff --check
```

The earlier read-only receipt at
`ok=34 changed=1 unreachable=0 failed=0 skipped=0` is **historical and predates the
lifecycle/pre-state hardening**; it is not acceptance evidence for the current
source. A **fresh check is required** after every source or hash change and must
show the exact two-policy prediction with no Kubernetes mutation. Apply remains a
separate approval and must follow a fresh successful check; no apply, policy
mutation, Secret read, or runtime traffic test is claimed by this document.

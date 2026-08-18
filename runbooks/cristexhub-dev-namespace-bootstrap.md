# CristexHub DEV Namespace bootstrap

## Status and boundary

**CHECKPOINT COMPLETE — IDEMPOTENT.** This increment defines only the exact
`cristexhub-dev` Namespace and a dedicated guarded Ansible bootstrap. It does not
reuse or reopen the completed platform or `shared-services` Namespace wrappers.
`cristexhub-prod` remains absent and is blocked until DEV validation, recovery, and
soak evidence satisfy the promotion gate.

No Secret, workload, Service, PVC, policy, route, or PROD object is part of this
source. ResourceQuota, LimitRange, ServiceAccount, RBAC, NetworkPolicy, Infisical,
Argo CD, database, broker, and application objects remain separate future increments.

## Exact source closure

The bootstrap owns only:

- `kubernetes/applications/namespaces/cristexhub-dev.yaml`;
- `ansible/bin/bootstrap-cristexhub-dev-namespace`;
- `ansible/playbooks/bootstrap_cristexhub_dev_namespace.yml`;
- `ansible/plugins/action/cristexhub_dev_namespace_guarded_k8s.py`; and
- `ansible/roles/cristexhub_dev_namespace_bootstrap/`.

The manifest contains only `apiVersion: v1`, `kind: Namespace`, the exact name, and
four approved labels:

- `app.kubernetes.io/part-of: cristexhub`;
- `cristex.io/environment: dev`;
- `cristex.io/bootstrap-writer: ansible`; and
- `cristex.io/desired-owner: argocd`.

The Argo label is future intent only. Ansible remains bootstrap writer until a later
object-specific registration/adoption, successful sync, managed-field proof, and
cessation of Ansible reconciliation complete the handoff.

## Guarded execution contract

The sole entrypoint is `ansible/bin/bootstrap-cristexhub-dev-namespace`. It accepts
only `check` or `apply`, loads the explicit ignored inventory, uses the one-host
limit, enables diff, and asks for the remote sudo password only through
`--ask-become-pass`. It launches the pinned repository controller in an allowlisted
clean environment with a private single-run attestation. The dedicated mutation
action also reads Ansible's controller CLI context directly and fails before the
Kubernetes module under `--start-at-task`, `--step`, non-default tags, or skipped
tags; ordinary or extra variables cannot forge that context. It independently
requires the exact present-only module arguments and exact four-label DEV definition.

The role refuses external internal-variable injection, symlinked or noncanonical
source, unsafe modes or ownership, an unexpected manifest shape, an existing foreign
Namespace, any state other than present, absent diff/limit/approval gates, and failed
k3s/Tailscale or kubeconfig preflight. It can reconcile exactly one Namespace with
`state: present`; it has no deletion path. Live post-state requires exact name, all
four labels, `Active` phase, and preserved service health.

## Approval sequence

The separately approved check ran through the sole wrapper and passed:

```text
crtxweb : ok=20 changed=1 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
```

The exact committed closure has one change-capable loop item and one Namespace
manifest, so the single check-mode change predicted only creation of
`cristexhub-dev`. The two skipped tasks are live post-state query/verification; check
mode made no mutation.

The first apply then passed:

```text
crtxweb : ok=22 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

The one exact mutation created `cristexhub-dev`; zero skipped/failed tasks prove the
protected post-state and service checks ran successfully. The role verified all four
labels, `Active` phase, and preserved k3s/Tailscale health.

The idempotence apply passed:

```text
crtxweb : ok=22 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

Exact post-state and service health remained valid with no change. The Namespace
checkpoint is complete. It authorizes no follow-on object or reopening/broadening of
this wrapper. A successful Namespace checkpoint does not
authorize policies, Secrets, workloads, data services, routes, Argo adoption, or
PROD.

## Stop and rollback

Stop on any extra object, PROD target, foreign Namespace, schema or label drift,
source/path/mode/ownership drift, missing attestation, failed service or kubeconfig
preflight, failed post-state, secret disclosure, task-selection use, or mutation-
argument drift.

Source rollback is Git revert. Runtime rollback does not delete the Namespace.
Namespace deletion requires a separate destructive design and explicit approval;
this bootstrap intentionally implements no deletion.

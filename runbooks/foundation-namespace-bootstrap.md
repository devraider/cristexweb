# Foundation Namespace bootstrap

## Status and boundary

The exact source for `shared-services` and a dedicated bounded Ansible bootstrap
are implemented. The source is deployable, but every runtime checkpoint is **NOT
RUN**. The earlier `platform-secrets` and `platform-identity` source was superseded
before its wrapper ever ran; removing those files is not evidence of a live rename or
deletion. This record authorizes no discovery, wrapper check, apply, idempotence run,
Secret operation, workload, route, or cluster contact.

The completed `argocd`/`platform-edge` bootstrap remains closed and unchanged. Its
wrapper, role, manifests, approvals, and evidence are not reused or reopened.

## Exact source closure

The new bootstrap owns only:

- `kubernetes/platform/namespaces/shared-services.yaml`;
- `ansible/bin/bootstrap-foundation-namespaces`;
- `ansible/playbooks/bootstrap_foundation_namespaces.yml`; and
- `ansible/roles/foundation_namespace_bootstrap/`.

Each manifest contains only `apiVersion: v1`, `kind: Namespace`, the exact name, and
these three labels:

- `app.kubernetes.io/part-of: cristex-platform`;
- `cristex.io/bootstrap-writer: ansible`; and
- `cristex.io/desired-owner: argocd`.

There is no annotation, finalizer, delete path, `absent` state, passthrough argument,
Secret, ServiceAccount, workload, Service, NetworkPolicy, PVC, chart, values file,
route, Infisical object, Argo object, Keycloak object, or PostgreSQL object in this
increment.

## Guarded execution contract

The only future entrypoint is `ansible/bin/bootstrap-foundation-namespaces`. It
accepts exactly one mode, `check` or `apply`, uses the explicit local inventory and
one-host limit, enables diff, prompts for the local become password, and launches the
repository controller in an allowlisted clean environment. It supplies an ephemeral,
single-run attestation under a component-specific environment namespace and binds
all protected in-run preflight results immediately before reconciliation. A forged
wrapper-format token/file alone cannot make a direct task-start invocation reach the
Kubernetes module. Extra arguments, forged internal variables, symlinked or
noncanonical source, unsafe modes/ownership, a foreign existing Namespace, and any
state other than present fail closed.

These controls prevent accidental direct invocation and task-selection bypass. They
are not a privilege boundary against a malicious operator who already controls the
same controller account, local sudo authentication, and protected kubeconfig access;
such an operator already holds equivalent cluster authority. Operator access and
review remain security boundaries.

The role verifies k3s and Tailscale health, the protected kubeconfig metadata, exact
manifest schema and labels, and exact existing-object identity before reconciliation.
A live run may only create or reconcile the one exact `shared-services` Namespace
with state present.
Live post-state verification requires exact identity, labels, `Active` phase, and
preserved service health. Check mode predicts changes but skips live post-state
claims.

The labels state provenance and future intent only. Ansible remains bootstrap writer;
Argo ownership requires a later object-specific registration/adoption, successful
sync, managed-field evidence, and cessation of Ansible reconciliation. A label alone
is not a handoff.

## Future approval sequence

Each command below is a one-line zsh command and is documentation only:

1. After a separately approved read-only discovery, request separate approval for `ansible/bin/bootstrap-foundation-namespaces check`.
2. Review the complete check/diff result and require that only `shared-services` is predicted.
3. Request a new, separate approval for `ansible/bin/bootstrap-foundation-namespaces apply`.
4. Review exact post-state and service-health evidence.
5. Request another separate approval for `ansible/bin/bootstrap-foundation-namespaces apply` and require `changed=0` as the idempotence checkpoint.

Discovery and mutation never share approval. A check result never authorizes the
first apply, and the first apply never authorizes idempotence. No approval is inferred
from this source or runbook.

## Stop and rollback

Stop on any unexpected object, foreign existing Namespace, label/schema drift,
source/path/ownership/mode drift, task-selection attempt, missing attestation,
kubeconfig drift, service-health failure, failed exact post-state assertion, Secret
or workload appearance, or output containing sensitive/controller metadata.

Source-only rollback is Git revert. Future routine runtime rollback does not delete a
Namespace. Namespace deletion requires a separate destructive design and approval;
this bootstrap intentionally has no deletion implementation.

## Remaining blockers

- separately approved read-only live discovery;
- separate wrapper check and reviewed prediction;
- separate first apply and post-state review;
- separate idempotence apply requiring `changed=0`;
- later promotion from the selected offline Infisical Operator `v0.11.7` baseline through the inert [privileged-prerequisites inventory](infisical-operator-privileged-prerequisites-design.md) to separately reviewed component-specific source;
- secret-zero and non-sensitive synchronization/recovery evidence; and
- Argo, Keycloak/PostgreSQL, OIDC, stateful recovery, and every route/runtime gate.

Until those checkpoints pass, the `shared-services` Namespace runtime state remains
**NOT RUN** and no new cluster object is claimed. A later discovery must stop rather
than delete anything if either superseded Namespace unexpectedly exists.

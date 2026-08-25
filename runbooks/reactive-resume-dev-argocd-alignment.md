# Reactive Resume DEV Argo handoff alignment

## Status

**SUPERSEDED AFTER ARGO ADOPTION — DO NOT RERUN.** This lane was the one-shot, present-only alignment of exactly seven canonical
`ansible/files/components/reactive-resume-dev-argocd` objects and the four
reviewed destination NetworkPolicies listed in the role defaults. It does not
include the migration Job, any Secret, a Namespace, PVC, RBAC object, delete,
prune, Argo sync, or workload restart.

## Exact closure

The seven DEV objects are the Deployment, private Ingress, three DEV
NetworkPolicies, Service, and ServiceAccount in `cristexhub-dev`. The four
shared-services destination policies are:

- `shared-postgresql-ingress`
- `keycloak-allow-reactive-resume-dev`
- `oidc-connect-proxy-allow-reactive-resume-dev`
- `reactive-resume-object-storage-allow-dev`

The role loads only these eleven immutable source paths, validates raw file
SHA-256 hashes and canonical object hashes, rejects Jobs and Secrets, and
refuses foreign ownership, Argo tracking annotations, Argo managed fields,
owner references, or finalizers. The custom action guard accepts only the
exact eleven identities, `state: present`, the k3s administrator kubeconfig,
`wait: false`, and `wait_timeout: 60`. It has no delete path and no prune path.

The migration Job remains a separately guarded one-shot prerequisite and is
not part of this lane or automated Argo desired state.

## Guarded entrypoint

```text
ansible/bin/bootstrap-reactive-resume-dev-argocd-alignment check
ansible/bin/bootstrap-reactive-resume-dev-argocd-alignment apply
```

The canonical Linux wrapper accepts only `check|apply`, requires the pinned
repository controller and inventory, rejects task-selection and inherited
Ansible override controls, creates a single-run mode-0600 attestation, forces
`--diff --limit crtxweb`, and uses an allowlisted clean environment. `check`
must be reviewed and passed before any separately approved `apply`.

## Ownership and residual gates

This lane was Ansible-owned bootstrap alignment only. Registration, adoption, and
successful sync now pass; Argo now owns the adopted workload objects. The lane must
refuse Argo tracking markers and must not be rerun. Migration completion, database,
OIDC, recovery, and soak acceptance remain separate gates.

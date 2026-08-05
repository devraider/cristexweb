# Infrastructure Agent Rules

This root `AGENTS.md` is authoritative for the entire repository.

## Current boundary

- Operational implementation is limited to the read-only Ansible discovery playbook and the separately approved one-package dependency bootstrap under `ansible/`. No host baseline or deployment exists.
- Python exists only in offline contract tests; it is not operational infrastructure automation.
- This repository otherwise owns design documentation for future host configuration, external-resource IaC, GitOps desired state, and recovery runbooks.
- No hosted runtime, general Ansible host baseline, OpenTofu configuration, Kubernetes manifest, Helm chart, or workflow exists here yet.
- CristexHub application source, local Compose assets, Keycloak theme, and Browserless gateway remain external concerns in the CristexHub application repository and must not be copied here.
- One non-elevated discovery and one elevated-but-unavailable Kubernetes query run have completed. The operator approved installing only `python3-kubernetes` to enable `k8s_info`; any other host mutation or later implementation remains blocked until its explicit approval gate. Offline validation remains allowed.

## Ownership

Each resource has exactly one reconciliation owner:

| Area | Owner |
|---|---|
| Debian host, mounts, firewall, Tailscale host access, k3s installation | Ansible |
| Cloudflare and GitHub resources | OpenTofu |
| Kubernetes objects and Helm releases | Argo CD |
| Runtime secret values and rotation | Infisical |
| Tests, image builds, and immutable private-GHCR publication | GitHub Actions |
| Production approvals and destructive operations | Human operator |

Future implementation belongs at repository-root `ansible/`, `opentofu/`,
`kubernetes/`, and `runbooks/`. Do not use OpenTofu Kubernetes or Helm providers
for objects reconciled by Argo CD. GitHub Actions must not deploy directly with
`kubectl`, Helm, or Argo CD.

## Host automation standard

- Debian plus Ansible is the approved host-management path for G1. NixOS migration
  is out of scope unless a later architecture decision explicitly replaces this
  owner.
- Prefer Ansible built-in modules over `shell` or `command`. Use shell execution
  only when no suitable module exists, make it idempotent, and document why.
- The current discovery uses Ansible built-ins plus `kubernetes.core.k8s_info`; it
  contains no operational Python, command allowlist, shell, raw, script, or command
  task.
- Controller tools are pinned by root `pyproject.toml` and `uv.lock`; `uv` owns the
  ignored project-local `.venv`, while Galaxy collections install only into the
  ignored `ansible/.ansible/collections/` path.
- Use Python only for offline tests or a later approved focused plugin/custom module
  when built-in Ansible behavior is demonstrably insufficient. Do not recreate
  package, file, service, user, mount, or information modules.
- Operational simplicity, idempotence, safety, and maintainability are the
  acceptance criteria.

## Safety gates

Explicit operator approval is required before any of these actions:

- SSH command that mutates a host;
- Ansible play without check/diff mode;
- `tofu apply`, import, state mutation, or destroy;
- Helm install/upgrade, Argo sync, or Kubernetes apply/delete;
- namespace, PVC, database, volume, or backup deletion;
- disk partitioning, formatting, mounting, or k3s reinstall;
- DNS, Cloudflare Tunnel, firewall, Tailscale ACL, or public-route mutation;
- secret creation, export, rotation, or revocation;
- DEV or PROD deployment and public cutover.

Discovery commands must be read-only. Never combine discovery and mutation in one
script or approval request. Never use namespace/PVC deletion or blind OpenTofu
destroy as routine rollback.

## Networking

- Retain bundled k3s Traefik as the sole ingress controller unless a later approved migration replaces it. Do not add a second ingress controller.
- PROD application traffic may become public only through an explicitly reviewed Cloudflare Tunnel route to Traefik.
- DEV, SSH, the k3s API, Argo CD, dashboards, databases, brokers, code-runner, and administrative endpoints remain private through host Tailscale or explicit port-forwarding.
- Databases and brokers must never receive public Ingress, NodePort, or Tunnel routes.
- Every exposure change must document authentication, source, destination, port, expected public status, negative reachability checks, and rollback.

## Secrets and state

- Never commit plaintext credentials, kubeconfigs, private keys, tunnel tokens, database URLs containing credentials, Infisical machine credentials, or real `.env` files.
- Kubernetes manifests contain only Infisical references, never secret values.
- Do not place secret values in OpenTofu variables, plans, outputs, committed state, examples, CI logs, or review artifacts.
- The root [`.gitignore`](.gitignore) protects OpenTofu/Terraform working directories, state, plans, local variable/override/crash files; Ansible retry/cache/facts; kubeconfigs; local environment/credential/key artifacts; and generated secret material. `.terraform.lock.hcl` is deliberately tracked so provider selections are reviewable.
- DEV and PROD use separate Infisical environments, identities, application credentials, encryption keys, database principals, and backup paths.
- Preserve and back up application encryption keys independently; losing them can make encrypted application data unrecoverable.

## Data and recovery

- Shared PostgreSQL and MongoDB engines are an accepted resource-saving design, not an availability or security boundary.
- DEV and PROD must have separate databases, owners/users, credentials, migrations, backup sets, and negative cross-access tests.
- Redis remains environment-local. A shared RabbitMQ requires separate users and virtual hosts plus resource limits.
- Stateful work requires a verified backup before mutation and an isolated restore rehearsal before production acceptance.
- Rollback prefers Git revert and a previously verified image digest. Database changes must be forward-compatible or have a tested data recovery plan.

## Delivery and evidence

- Deploy immutable image digests or commit-SHA references; never deploy `latest`.
- DEV must pass validation and soak before PROD is created or promoted.
- PROD must pass private validation before any Cloudflare public cutover.
- Each change updates the relevant `specs/<milestone>/testcases.md` with actual commands and results.
- Run offline checks before provider-backed plans, provider-backed plans before applies, and private validation before public validation.
- Record residual risks honestly. A single node and shared database engines remain shared failure domains even after logical isolation tests pass.

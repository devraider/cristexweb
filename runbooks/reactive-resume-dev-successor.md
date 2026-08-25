# Reactive Resume DEV successor catalog check

## Boundary

This is a **source-only, read-only** DEV preflight. It does not apply a
Database, DatabaseRole, Secret, ConfigMap, Infisical CR, ValidatingAdmissionPolicy,
workload, PVC, route, or namespace. It never writes Infisical, PostgreSQL, or
Kubernetes state. PROD and predecessor credentials are forbidden.

The observed successor database and roles may have been created by SQL without
CNPG `Database`/`DatabaseRole` CRs. This lane therefore does not declare or
reconcile successor CNPG objects. It fails closed if such CRs appear until
exact lifecycle provenance and owner handoff are separately established.

## Existing value owners

The runtime and migration `InfisicalStaticSecret` sources are checked as
value-free CR specs and target metadata. The PostgreSQL CA is **not** declared
here: `reactive-resume-dev-ca` under the existing
`infisical-reactive-resume-dev-ca` lane owns both CA targets from
`/reactive-resume/dev/object-storage-tls`. A competing CA StaticSecret source is
forbidden. Secret payloads and ConfigMap data are never requested.

## Catalog check

The checker runs inside the Ready CNPG primary with the pinned PostgreSQL 17
image and peer-authenticated local Unix socket as `postgres`. It does not assume
or mount `/etc/postgresql/admin/*`, `/tls/ca.crt`, a password file, a pgpass
file, or a network database endpoint. It validates without outputting row data
or credentials:

- exact `LOGIN`, `NOINHERIT`, non-superuser, non-createdb, non-createrole,
  non-replication, non-bypassrls runtime and migration roles;
- zero role memberships and migration ownership of the successor database;
- target database `CONNECT`/`TEMPORARY` and public-schema ACLs;
- all application relation ownership and exact runtime DML/migration owner ACLs;
- public sequence and function privileges;
- migration-role default relation/sequence privileges and absence of runtime
  or predecessor defaults; and
- denial of runtime/migrator cross-database `CONNECT` and database/role creation.

The current read-only observation found the SQL-created successor and exact
NOINHERIT/ACL/default-privilege catalog, but cross-database connectivity remains
blocked by PUBLIC defaults on `platform_admin` and `postgres`. The check must
therefore remain blocked; it must not repair that drift.

## Guarded invocation

```text
ansible/bin/check-reactive-resume-dev-successor check
```

The non-passthrough wrapper supplies `--check --diff --limit crtxweb`, a
single-use attestation, an allowlisted environment, and the pinned controller.
Before invoking Ansible it verifies the fixed `SOURCE-CLOSURE.sha256` for the
checker, source manifest, all three nested successor YAML leaves, the existing
`ansible/files/components/infisical-reactive-resume-dev-ca/source/reactive-resume-dev-ca-static-secret.yaml`
CA source leaf, role task/defaults, playbook, policy, `ansible.cfg`, metadata-only
library, wrapper, and action plugin. It validates every leaf's
mode and digest, and canonicalizes only the wrapper closure-manifest pin and
action self/closure-manifest pins; no source leaf is omitted or normalized away.
The complete closure is checked before the pinned Ansible controller starts, so
no earlier role task can run against an unverified checkout. The wrapper attests
its raw source hash; the action compares that raw attestation to the current file
and separately requires the canonical wrapper hash from the closure. The action
guard repeats that closure check. A direct playbook or role invocation is not an
authorized entrypoint and is rejected by the wrapper-bound role contract. A
malicious process already running as the trusted controller UID could mint
same-UID environment, attestation, or Ansible inputs; that process is outside the
claimed integrity boundary. The role uses metadata-only Secret/ConfigMap
requests and read-only `kubernetes.core.k8s_info`/`kubernetes.core.k8s_exec`
operations. No source-only check is authorization to activate the application,
rotate credentials, adopt CNPG ownership, run migrations, or promote PROD.

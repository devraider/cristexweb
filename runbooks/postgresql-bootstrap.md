# Guarded PostgreSQL source-only bootstrap

## Status and boundary

This runbook describes the committed, value-free source closure for one
non-authoritative PostgreSQL `17.10` smoke pod in `shared-services`. It is not a
runtime approval and has not been run against a host, registry, Kubernetes API,
Infisical, Secret, PVC, database, or Argo CD.

The source is deliberately a raw one-replica StatefulSet, private ClusterIP
Service, retained `40Gi` `local-path` RWO claim, tokenless ServiceAccount, and
exact NetworkPolicies. It pins
`docker.io/library/postgres@sha256:dbbeb22a65db2503050cdbbe5e78f017478f10a1002a226463f049dbb017e99b`.
The pod is a smoke path only: it is not HA, authoritative, or a production data
store. It does not provision the five logical consumer databases/roles, backups,
restores, migration state, or an Ansible-to-Argo handoff.

Infisical Cloud remains the only value owner. The separate source-only
[Infisical database Secret materialization seam](infisical-database-secret-materialization.md)
freezes the exact Universal Auth, project/environment/path, StaticSecret, VAP, RBAC,
and target contracts; its check/apply and generated Secret sync remain
**NOT RUN/BLOCKED**. This wrapper refuses to proceed until
`shared-services/Secret/shared-postgresql-admin` has exactly `username` and `password`
and `shared-services/Secret/shared-postgresql-tls` has exactly `ca.crt`, `tls.crt`, and
`tls.key`, with type and labels proving Infisical ownership. Before any workload
mutation, the canonical-task-bound no-log validator requires a password of at least
32 bytes and one current directly issued server certificate/private-key pair with a
strong key, server-auth EKU, and the exact SANs `localhost`,
`shared-postgresql.shared-services.svc`, and
`shared-postgresql.shared-services.svc.cluster.local`. No Secret manifest or value is
committed, logged, returned, or passed in argv. The separate source-only
[Infisical Universal Auth/value lane](infisical-universal-auth-value-lane.md) reserves
`/shared-services/postgresql` in project `cristexweb-infrastructure` and Infisical environment
`prod` (Infisical Cloud only; Kubernetes `cristexhub-prod` remains inactive) with exact administrator/TLS keys, and seeds only
`shared-services/shared-postgresql-infisical-universal-auth`. It does not create this
PostgreSQL target Secret, provision a database, or authorize this runtime closure;
its identities, values, upload, recovery, and rotation remain **NOT RUN/BLOCKED**.

## Source contract

The six hash-bound manifests are under
`ansible/files/components/postgresql/` and are listed in
`ansible/files/components/postgresql/MANIFESTS.sha256`:

1. deny-first SCRAM/TLS `pg_hba.conf` ConfigMap;
2. tokenless PostgreSQL ServiceAccount;
3. private ClusterIP Service on TCP `5432`;
4. default-deny ingress/egress NetworkPolicy;
5. exact namespace-labeled consumer ingress NetworkPolicy; and
6. one-replica StatefulSet with immutable image, exact resources, retained PVC,
   TLS staging, local probes, and read-only root filesystem.

The StatefulSet sets `PGDATA=/var/lib/postgresql/data/pgdata`, uses writable
emptyDirs for `/var/run/postgresql` and `/tmp`, and runs the main and TLS-staging
containers as UID/GID `999`. The TLS key is staged with mode `0600`; each startup,
readiness, and liveness probe reads credentials from mounted files into the process
environment, authenticates with `psql` over `verify-full` TLS, and then fails if a
plaintext TCP query succeeds. No probe places a password in argv. The final server
command enables TLS, points at the Infisical-owned certificate/CA, and uses the
mounted SCRAM/deny-first HBA.

## Authorized entrypoint

Only the non-passthrough wrapper is authorized:

```text
ansible/bin/bootstrap-postgresql check
ansible/bin/bootstrap-postgresql apply
```

The wrapper rejects all other arguments and task selection, requires the canonical
`/Users/paul/Projects/cristexweb` checkout and pinned local Ansible controller,
creates a single-use mode-`0600` attestation, forces `--diff`, limits to `crtxweb`,
and passes no credentials or values. The custom action plugin rejects changed
objects, Secrets, foreign task sources, forged internal preflight state, and
`--start-at-task`/`--step`/tag selection before dispatching to
`kubernetes.core.k8s`.

`check` must be reviewed for exactly six possible present-only objects and no
mutation. Only after a separate approval may `apply` be run. In apply mode the
role waits for the StatefulSet's observed generation, updated replica, and matching
revisions; the PostgreSQL Pod to be Running and Ready; and the guarded generated PVC
`postgresql-data-shared-postgresql-0` to be Bound with exact labels, access mode,
volume mode, class, and capacity. It verifies the Service remains private and that
k3s and Tailscale remain running. The wrapper has no
Secret creation, delete, PVC delete, database provisioning, backup, restore, or
Argo command.

## Stop and residual gates

Stop before applying on any source/hash/ownership drift, missing or extra Secret
key, non-Infisical Secret label, foreign object, unexpected diff, failed check,
non-ready PVC/Pod/StatefulSet, image pull failure, or policy mismatch. Do not
remove the PVC or StatefulSet as rollback. A later reviewed change must preserve
data and use an explicit migration/backup plan.

Runtime acceptance remains blocked until separate evidence covers image trust and
pullability, TLS identity/rotation, SCRAM positive and plaintext-negative tests,
NetworkPolicy enforcement, storage/reclaim behavior, logical authorization for all
consumer scopes, backup/restore and RPO/RTO, secret recovery, and the exact
object-by-object Ansible-to-Argo handoff. Standalone one-replica PostgreSQL is not
HA and must not be promoted as authoritative.

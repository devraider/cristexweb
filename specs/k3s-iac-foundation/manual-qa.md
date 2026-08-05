# Manual QA — k3s IaC foundation

## Evidence rules

Every executed case records date/time, tester, Git revision, deployed image digest,
environment, redacted evidence location, result, and rollback outcome. Never paste
passwords, tokens, cookies, kubeconfigs, connection strings, private keys, database
rows, personal data, or full secret-bearing command output.

All cases remain **PENDING** because no hosted runtime exists. One non-elevated
Ansible discovery produced a reviewed host-only report. A separately approved
become attempt confirmed the datastore, but all Kubernetes queries were unavailable
because the remote Python dependencies are absent. No successful cluster inventory,
dependency mutation, deployment, recovery-access proof, or complete manual runtime
validation occurred. These partial results do not satisfy the manual cases.

| ID | Requirements | Scenario | Expected | Status |
|---|---|---|---|---|
| MQA-01 | KIF-001, KIF-007, KIF-008 | Read-only Ansible inventory and recovery access | The approved one-host check/diff run leaves SSH/Tailscale available; actual curated k3s/storage facts are captured without mutation or secret output | PENDING |
| MQA-02 | KIF-005, KIF-009, KIF-010 | Private administration | Argo CD and k3s API work through the approved private path and are unreachable publicly | PENDING |
| MQA-03 | KIF-013–KIF-015 | Infisical rotation | A test secret rotates and revokes without plaintext in Git/logs; recovery credential remains usable | PENDING |
| MQA-04 | KIF-016–KIF-021 | DEV isolation | DEV reaches only its databases/services and cannot authenticate to or connect to PROD resources | PENDING |
| MQA-05 | KIF-017, KIF-018 | Database authorization | DEV PostgreSQL/MongoDB principals receive explicit denial against PROD data, and vice versa | PENDING |
| MQA-06 | KIF-022–KIF-025 | DEV promotion and rollback | Argo deploys a reviewed immutable digest and Git revert restores the prior verified digest | PENDING |
| MQA-07 | KIF-026–KIF-028 | Backup and isolated restore | Encrypted off-node backup restores into isolation within RPO/RTO and application validation passes | PENDING |
| MQA-08 | KIF-025 | Private PROD acceptance | PROD auth, API, workers, migration, data isolation, resource headroom, backup, and rollback pass before public routing | PENDING |
| MQA-09 | KIF-010–KIF-012 | Public cutover | `hub.cristex-soft.com` works through Cloudflare Tunnel; DEV/admin/data endpoints remain publicly unreachable | PENDING |
| MQA-10 | KIF-007, KIF-028–KIF-030 | Reboot and replacement recovery | Host reboot preserves access/workloads; documented replacement-host recovery restores desired state and data | PENDING |
| MQA-11 | KIF-019, KIF-029 | Single-node pressure | Database and application limits preserve control-plane headroom; alerts arrive for disk/resource/backup failure | PENDING |
| MQA-12 | KIF-003, KIF-030 | Rollback safety | Git, image, route, secret, and host rollback avoid namespace/PVC deletion and blind external destroy | PENDING |

## Public exposure checklist

Before MQA-09 can pass, verify from outside the LAN/tailnet:

- only the approved PROD hostname resolves/routes;
- application OIDC/JWT enforcement remains active;
- deliberate unauthenticated application routes are enumerated and abuse-tested;
- DEV, Argo CD, k3s API, SSH, databases, brokers, dashboards, Browserless,
  code-runner, and identity administration are unreachable;
- direct-origin WAN ports are closed;
- disabling the Cloudflare route removes public access without breaking private PROD.

## Recovery checklist

A restore rehearsal must start from a clean isolated target and prove recovery of:

- pinned host/k3s configuration;
- Argo CD repository access;
- Infisical bootstrap access and environment identities;
- OpenTofu state and external-resource ownership;
- application encryption keys;
- PostgreSQL and MongoDB data;
- immutable images or reproducible builds;
- private validation before public route reactivation.

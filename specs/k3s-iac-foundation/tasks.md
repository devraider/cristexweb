# Tasks — k3s IaC foundation

## Documentation foundation

- [x] Document infrastructure-specific ownership and safety rules (`KIF-001`–`KIF-006`).
- [x] Document the target architecture, accepted shared-data trade-off, stages,
  stop conditions, and rollback (`KIF-009`–`KIF-030`).
- [x] Define the requirements, test contract, manual QA, and truthful backlog status
  without adding executable IaC (`KIF-030`).
- [x] Add the protective root `.gitignore` while keeping `.terraform.lock.hcl`
  trackable (`KIF-006`).
- [x] Record the documentation-only validation in this milestone's testcases
  (`KIF-004`, `KIF-030`).

## Stage 1 — read-only discovery

- [ ] Obtain explicit approval for read-only elevated k3s inventory (`KIF-001`).
- [ ] Capture sanitized host, datastore, CNI, NetworkPolicy, DNS, Traefik,
  StorageClass, disk, route, firewall, and resource state (`KIF-008`).
- [ ] Confirm recovery access and record current configuration backups (`KIF-007`,
  `KIF-028`).
- [ ] Resolve the decision register for the next stage; do not mutate while
  discovery is incomplete (`KIF-002`, `KIF-003`).

Approval gate: operator approves the sanitized inventory and first mutation plan.

## Stage 2 — host safety baseline

- [ ] Verify the protective ignore rules before generating any Ansible artifacts (`KIF-006`).
- [ ] Implement the smallest Ansible inventory/playbook for approved host and k3s
  settings (`KIF-004`, `KIF-005`, `KIF-007`).
- [ ] Run syntax/lint and check/diff mode before the first mutation (`KIF-002`,
  `KIF-007`).
- [ ] Obtain explicit approval for the first Ansible mutation (`KIF-002`).
- [ ] Prove idempotence, reboot recovery, SSH, and Tailscale access (`KIF-007`).

Stop gate: stop on access loss, unexpected network/package changes, or ambiguous
disk state. Restore preserved configuration before continuing.

## Stage 3 — external resources

- [ ] Verify the root OpenTofu ignore policy, then select a protected, encrypted,
  locked, recoverable state backend (`KIF-006`, `KIF-028`).
- [ ] Implement only approved Cloudflare/GitHub resources; do not use Kubernetes or
  Helm providers (`KIF-005`).
- [ ] Validate formatting/configuration and review a sanitized plan (`KIF-002`,
  `KIF-013`).
- [ ] Obtain explicit approval for the first OpenTofu apply (`KIF-002`).
- [ ] Create no public application route in this stage (`KIF-010`, `KIF-011`).

Stop gate: stop on secret-bearing state/plan, replacement/destroy outside scope, or
missing state recovery. Reverse changes only through another reviewed plan.

## Stage 4 — GitOps and secret bootstrap

- [ ] Pin and render the minimal Argo CD and Infisical operator versions
  (`KIF-005`, `KIF-013`, `KIF-023`).
- [ ] Approve and document the private Git/Infisical/GHCR/Cloudflare secret-zero
  sequence (`KIF-014`, `KIF-015`).
- [ ] Obtain explicit approval for bounded Argo CD bootstrap (`KIF-002`).
- [ ] Keep Argo CD private and prove Git reconciliation using a demo workload
  (`KIF-010`, `KIF-022`).
- [ ] Prove one non-sensitive Infisical sync, rotation, and revocation without value
  disclosure (`KIF-013`–`KIF-015`).

Stop gate: stop if an admin surface becomes public, secret content appears in Git or
logs, or bootstrap cannot be recovered.

## Stage 5 — namespaces, policy, and shared data

- [ ] Approve StorageClass, live-data path, backup path, capacity, and any destructive
  disk preparation separately (`KIF-002`, `KIF-003`, `KIF-019`, `KIF-026`).
- [ ] Add DEV, PROD, and shared-data namespaces, service accounts, RBAC, quotas,
  limits, and default-deny policies (`KIF-016`, `KIF-019`, `KIF-021`).
- [ ] Obtain explicit approval before creating stateful services (`KIF-002`).
- [ ] Create shared PostgreSQL with separate databases/roles and negative access
  tests (`KIF-017`).
- [ ] Create shared MongoDB with separate databases/users and negative access tests
  (`KIF-018`).
- [ ] Create per-environment Redis; retain shared RabbitMQ only after separate
  user/vhost/limit tests (`KIF-020`).
- [ ] Complete backup and isolated restore tests before application data is accepted
  (`KIF-026`–`KIF-028`).

Stop gate: stop on cross-access, public data exposure, failed restore, unsafe node
pressure, or inability to preserve encryption keys. Never delete PVCs as rollback.

## Stage 6 — private DEV

- [ ] Deploy the minimal CristexHub DEV slice by immutable digest (`KIF-023`,
  `KIF-024`).
- [ ] Validate OIDC/auth, API, worker, exactly-one Beat, migration, WebSocket, and
  private routing behavior (`KIF-010`, `KIF-021`, `KIF-025`).
- [ ] Measure capacity before adding Reactive Resume, Browserless, or other optional
  components (`KIF-019`, `KIF-029`).
- [ ] Prove Git/digest rollback and complete the approved soak (`KIF-024`, `KIF-025`,
  `KIF-030`).

Stop gate: stop on public DEV exposure, migration ambiguity, unsafe resource
pressure, or rollback failure.

## Stage 7 — scheduled recovery

- [ ] Approve RPO, RTO, retention, encryption, Google Drive identity, and recovery
  custody (`KIF-015`, `KIF-026`–`KIF-028`).
- [ ] Implement non-destructive scheduled dumps and encrypted `rclone copy`
  (`KIF-026`).
- [ ] Rebuild in isolation and record restore timing/data/application validation
  (`KIF-027`, `KIF-028`, `KIF-030`).
- [ ] Add bounded backup/disk/node/tunnel/workload health signals (`KIF-029`).

Stop gate: stop if any required recovery artifact exists only on the node or a
restore needs unavailable credentials.

## Stage 8 — private PROD

- [ ] Obtain explicit approval for the PROD namespace after DEV soak/recovery passes
  (`KIF-002`, `KIF-025`).
- [ ] Create separate PROD identities, databases, credentials, keys, backup paths,
  and policies (`KIF-014`–`KIF-021`).
- [ ] Promote the same verified digest and validate PROD privately (`KIF-024`,
  `KIF-025`).
- [ ] Prove PROD isolation, backup, restore, and rollback (`KIF-017`–`KIF-030`).

Stop gate: stop if DEV can reach PROD, any admin/data surface is public, or recovery
and rollback evidence is incomplete.

## Stage 9 — public PROD

- [ ] Review the exact Cloudflare hostname, authentication path, tunnel destination,
  origin exposure, negative routes, and rollback (`KIF-011`, `KIF-012`).
- [ ] Obtain explicit approval for DNS/Tunnel cutover (`KIF-002`).
- [ ] Publish only the approved PROD application route (`KIF-011`).
- [ ] Verify public PROD and negative public reachability for DEV/admin/data services
  (`KIF-012`).
- [ ] Rehearse route rollback while private PROD remains healthy (`KIF-030`).

## Closeout

- [ ] Run independent security, recovery, and documentation review.
- [ ] Disposition every finding and rerun affected gates.
- [ ] Update testcases, manual QA, status, and runbooks with actual, sanitized
  evidence (`KIF-030`).
- [ ] Mark complete only after restore, rollback, exposure, and isolation gates pass.

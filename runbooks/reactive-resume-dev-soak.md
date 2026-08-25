# Reactive Resume DEV private hostname soak

## Purpose and boundary

This runbook defines the source-only, guarded, read-only acceptance closure for
`https://resume-dev.cristex-soft.com/`. It verifies that the private route and
shared `cristexhub` OIDC integration remain healthy over time without creating,
updating, deleting, restarting, enabling, or reconciling any live object.

The only authorized entrypoint is:

```text
ansible/bin/soak-reactive-resume-dev check
```

The wrapper is non-passthrough, pins the repository/controller, limits execution
to `crtxweb`, creates a single-use attestation, and always invokes Ansible with
`--check --diff`. The role independently refuses a non-check invocation,
foreign internal variables, extra hosts, alternate URLs, alternate realms, and
non-canonical duration/sample values. `uri`, `kubernetes.core.k8s_info`, and
`service_facts` are read-only; the pause between samples is not a mutation.
There is no apply, delete, enable, restart, Secret writer, DNS/provider path,
or Argo sync path.

## Exact 15-minute acceptance contract

The fixed contract is 16 samples at 60-second intervals: sample zero runs
immediately and samples 1–15 run after one minute each, for a minimum elapsed
window of 900 seconds. A run passes only when **all 16 samples** pass every
check below; one timeout, TLS failure, issuer mismatch, readiness loss, timer
drift, or PROD resource causes a fail-closed stop.

Every sample verifies:

- browser-trusted HTTPS to the exact health URL, with certificate validation
  enabled, HTTP `200`, and JSON status `healthy`;
- OIDC discovery at the shared realm URL and exact issuer
  `https://auth.cristex-soft.com/realms/cristexhub` (the successor realm is
  deliberately rejected);
- `cristexhub-dev` Deployment `reactive-resume-dev`: observed generation,
  one desired/updated/available/ready replica;
- ClusterIP-only Service `reactive-resume-dev`, exactly port `3000` targeting
  `http`;
- Traefik `websecure` Ingress `reactive-resume-dev-private`, exact hostname,
  TLS Secret reference `reactive-resume-dev-tls`, and exact route annotations;
- precreated `kubernetes.io/tls` Secret metadata with exactly `tls.crt` and
  `tls.key` keys, without reading or emitting values;
- zero `app.kubernetes.io/part-of=reactive-resume` resources in
  `cristexhub-prod` across Secret, Deployment, StatefulSet, Job, CronJob,
  Service, Ingress, NetworkPolicy, PVC, and InfisicalStaticSecret classes.

The host-side check additionally requires the existing
`cristexweb-reactive-resume-dev-backup.timer` to be `running` and `enabled`.
The soak never enables or starts it.

## Sanitized receipt

The final Ansible receipt is intentionally limited to:

- receipt identifier and `sanitized-v1` format;
- hostname, fixed duration, interval, and sample count;
- pass booleans for TLS/health, OIDC issuer, app readiness, backup timer, and
  zero PROD activation;
- `values_output=false`.

Response bodies, OIDC documents, Kubernetes Secret data, cookies, tokens,
identities, addresses not needed for the fixed contract, and credentials are
`no_log` and never belong in evidence. A pass receipt is not a backup/restore
proof or an Argo ownership handoff.

## Residual gates and risks

This source closure does not perform the required non-empty object-storage
backup/restore proof, measure RPO/RTO, reconcile an Argo Application, rotate
credentials, or activate PROD. Those remain separate guarded operations. The
single-node host, private DNS/Tailscale dependency, shared stateful services,
and certificate renewal process remain residual availability dependencies.

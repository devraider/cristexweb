# cloudflared candidate provenance — source-only evidence

## Status and boundary

**CANDIDATE — NOT DEPLOYABLE — NOT SELECTED.** Runtime evidence is **NOT RUN**.

This document records controller-side public-source research captured at
`2026-08-07T06:13:42Z`. It does not select a release, authorize a Cloudflare
resource, approve a route or hostname, or add an OpenTofu resource, Kubernetes
object, chart, values file, credential, or secret value. The ignored research files
are evidence inputs only; they are not committed deployment source. No inventory,
SSH, host, become, kubeconfig, Kubernetes API, Cloudflare-authenticated API or
provider, secret store, deployment, or route was used to collect or validate this
evidence. A later repository commit is source traceability, not runtime evidence.

The candidate may become deployable source only after every blocker below is
resolved, a human accepts the provenance/trust evidence and selects the version,
and a separate change adds reviewed desired state under the existing ownership and
approval rules.

## Release and source provenance evidence

| Item | Captured candidate evidence |
|---|---|
| Retrieval time | `2026-08-07T06:13:42Z` |
| Official latest release | `2026.7.3` |
| Release state | draft `false`; prerelease `false` |
| Published time | `2026-07-23T10:19:16Z` |
| Official release URL | `https://github.com/cloudflare/cloudflared/releases/tag/2026.7.3` |
| Annotated tag object | `92bf87305b06c8614e78f5e6a7c6b2364a236c36` |
| Resolved source commit | `3a2b45c2a511fcdd81b68c190938e4ffadbea5dc` |
| GitHub verification state | annotated tag unsigned; resolved commit unsigned |
| Official Darwin arm64 archive | SHA-256 `90c5a4f914d705fd70c135dba6d80b1791d254b08d6d4136301941f88330dd09` |
| Controller-side version result | `cloudflared version 2026.7.3 (built 2026-07-23-10:03 UTC)` |
| Official linux/amd64 binary asset | SHA-256 `9d71c677db00134c1bd4144b7783486b654ad281b1ea62b4972098d19f770f17`; not executed |

The official release API and exact asset digests bind this record to the observed
release content. The verified controller-side help binary was the Darwin arm64
asset, not the linux/amd64 runtime binary or container. GitHub reports both the
annotated tag and resolved commit as unsigned. Therefore publisher identity,
release authorization, provenance trust, and source-to-binary reproducibility are
**not established** by this evidence.

## Container image provenance evidence

| Item | Captured candidate evidence |
|---|---|
| Candidate image | `docker.io/cloudflare/cloudflared:2026.7.3` |
| Observed multi-platform index | `sha256:e39ee8da81ad5e05d77f38d2f51c60ca51bf2a8450ac3abab50c17fdb91d91bf` |
| Required linux/amd64 child | `sha256:b392761b711c0e5649d9b64e1fc9a10ba0563fa3e712ed7c26bde5cc1fbe9059` |
| linux/amd64 config | `sha256:41320ce229c5fb52a316a5e3af2e6a1faa32b114aa9e2a5eed0652eff59e8eef` |
| Config platform | `linux`; `amd64` |
| Config user | `65532:65532` |
| Config entrypoint | `cloudflared`; `--no-autoupdate` |
| Config default command | `version` |
| Config source linkage | `org.opencontainers.image.source=https://github.com/cloudflare/cloudflared`; `CI_GIT_COMMIT=3a2b45c2a511fcdd81b68c190938e4ffadbea5dc` |

The config source label and CI commit match the unsigned source commit above. The
registry digests establish observed content linkage, not a publisher signature,
identity, authorization, or trusted build attestation. The tag is mutable; any later
deployable source must use the exact selected architecture-specific child digest,
not the tag or multi-platform index alone.

## Token, health, and network behavior evidence

| Item | Captured candidate evidence |
|---|---|
| Token-file interface | release help exposes `--token-file value`; no token or example value was captured |
| Credential precedence | `--token` takes precedence over credentials and token-file; token-file takes precedence over credentials |
| Readiness endpoint | `/ready` returns HTTP 200 only with more than zero active connections; otherwise HTTP 503 |
| Independent health endpoint | `/healthcheck` returns `OK` independently of active tunnel connections |
| Default virtual metrics binding | all interfaces; semi-deterministic ports `20241` through `20245`, then a random fallback |
| Metrics server surface | readiness, health, metrics, debug, quick-tunnel, diagnostics, and configuration handlers share the listener |
| Required Cloudflare edge egress | outbound port `7844`: UDP for QUIC and TCP for HTTP/2 to the documented tunnel endpoints |
| Name resolution | DNS is required for the documented tunnel endpoints |

A later manifest must choose one fixed reviewed metrics port rather than the default
range or random fallback. It must expose no Service or Ingress for the metrics
listener and must restrict the metrics, debug, quick-tunnel, diagnostics, and
configuration surface. Readiness must use connection-aware `/ready`; `/healthcheck` alone cannot
prove that the tunnel can carry traffic.

The official firewall documentation identifies the required edge transport and
endpoints. This record intentionally does not copy the published address lists.
Exact DNS, Cloudflare-edge, and selected Traefik origin flows must be reviewed and
tested in the component NetworkPolicy before deployment.

## Blocking decisions and evidence

All items below block deployable cloudflared source and runtime:

1. **Human trust, version selection, and soak:** accept or reject the unsigned
   tag/commit and other provenance gaps, select or reject `2026.7.3`, and approve a
   compatibility and soak policy. This candidate record is not selection.
2. **Image assurance and availability:** obtain or explicitly disposition an image
   publisher signature, SBOM, vulnerability review, and trusted build evidence;
   prove independent off-node availability of the exact selected linux/amd64 child
   digest or approve a verified mirror/preload procedure.
3. **Container hardening compatibility:** test a read-only root filesystem, dropped
   capabilities, seccomp profile, non-root execution, and exact writable paths. This
   is **NOT TESTED** because the local Docker daemon was inactive; config user
   metadata alone is not runtime proof.
4. **Token secret-zero, recovery, and rotation:** approve Infisical ownership of the
   token-file value, the bootstrap identity, least-privilege access, file mount and
   permissions, off-node recovery, rotation, revocation, and non-disclosing tests.
   No token may enter Git, OpenTofu state/plan, command arguments, environment
   examples, or logs.
5. **Cloudflare external-resource ownership and state recovery:** OpenTofu must own
   the Tunnel and related Cloudflare resources. Provider initialization,
   authentication, resource design, encrypted timestamped state backup, independent
   key custody, integrity verification, isolated restore, reviewed plan, and apply
   are all blocked.
6. **Argo CD installation and handoff:** install and privately validate Argo CD,
   register the desired-state source, and evidence successful reconciliation before
   Argo owns any cloudflared Kubernetes object. Future-owner labels alone are not a
   handoff.
7. **Exact component traffic policy:** review and negatively test DNS, Traefik, and
   Cloudflare-edge flows, including outbound port `7844` UDP/QUIC and TCP/HTTP/2;
   deny unrelated namespace, control-plane, metadata, metrics, debug, quick-tunnel,
   configuration, and public access. Listing a NetworkPolicy is not enforcement evidence.
8. **Public route and hostname approval:** no public route or hostname is approved.
   Any later PROD route to bundled Traefik requires separate positive authentication
   and routing tests, negative DEV/admin/data reachability tests, and rollback.
9. **Single-node availability:** one replica on one physical node is a shared failure
   domain. The operator must accept the availability and connector interruption risk
   and define bounded health/alerting expectations.
10. **Runtime approvals:** separately approve secret creation, OpenTofu provider and
    resource operations, Argo desired state, Kubernetes reconciliation, private
    validation, and any later public cutover. Runtime remains **NOT RUN**.

Until these gates close, the rollback for this increment is only a Git revert of
this documentation and its offline contract test. There is no runtime rollback
because no Cloudflare resource, token, Kubernetes object, route, or deployment was
created.

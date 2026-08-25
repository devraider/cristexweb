# Reactive Resume DEV browser TLS renewal

This is a source-only guarded renewal closure for the private
`https://resume-dev.cristex-soft.com` route. It does not change DNS, Cloudflare
Tunnel ingress, Kubernetes objects, or the reserved PROD hostname.

## Exact ownership and custody

- Cloudflare is used only for DNS-01 at
  `_acme-challenge.resume-dev.cristex-soft.com` in the fixed zone.
- The API token is read only from the protected host file
  `~/.config/cristexweb/cloudflare-argo-dns-token`, owned by the timer user (`paul:paul`)
  and mode `0600`. It is never an argument, journal field, plan, state value, or
  evidence value.
- Certbot's Cloudflare DNS plugin creates and removes only its exact challenge
  TXT record. Cleanup runs on successful and failed challenges; the renewal
  process refuses to report success unless its cleanup path completed.
- The generated certificate and key exist only in a mode-0700 temporary
  workspace and mode-0600 leaves. The Infisical upload uses only the
  pre-authenticated local CLI session, never a token flag or secret-bearing
  environment variable.
- Infisical owns `prod:/reactive-resume/dev/tls`, keys `TLS_CRT` and `TLS_KEY`.
  The existing InfisicalStaticSecret materializes
  `cristexhub-dev/reactive-resume-dev-tls` with `creationPolicy: Orphan`.
  Direct `kubectl` Secret writes are forbidden.

## Renewal behavior

The service first checks the currently served public certificate. If it has at
least 30 days remaining it exits with a sanitized `skipped` receipt. If it is
within the threshold, it runs Certbot with DNS-01 only, validates the exact
single SAN, validity, and certificate/key correspondence, then writes exactly
those two values through the Infisical path. Any failure leaves existing
Infisical values untouched. Temporary workspace cleanup is installed before
certificate generation and removes certbot state, credentials, payload, and
private material.

The source requires distro packages `certbot` and
`python3-certbot-dns-cloudflare`. The host installer is a separate guarded
Ansible mode; source authoring does not install packages or run renewal.

## Safe systemd lifecycle

The units are installed disabled and stopped by default:

```text
ansible/bin/configure-reactive-resume-dev-tls-renewal check
ansible/bin/configure-reactive-resume-dev-tls-renewal apply
ansible/bin/configure-reactive-resume-dev-tls-renewal enable-check
ansible/bin/configure-reactive-resume-dev-tls-renewal enable-apply
```

`enable-apply` is a separate approval boundary. The daily timer is persistent,
randomized by 15 minutes, locked against concurrent execution, non-root, and
hardened with `ProtectSystem`, `ProtectHome=read-only`, `PrivateTmp`,
`NoNewPrivileges`, restricted address families, and an explicit writable state
root. Timer disablement is the rollback; no Kubernetes, DNS, Tunnel, or PROD
rollback is implied.

## Validation and renewal acceptance

Offline contract tests must verify the exact policy, token metadata contract,
Infisical path/key closure, systemd hardening, challenge cleanup language,
manifest hashes, wrapper rejection of passthrough arguments, and absence of
certificate/private-key values from source. A separately approved live run must
verify a near-expiry certificate renewal, exact SAN/key match, Infisical
materialization, Traefik HTTPS continuity, and zero temporary residue. The
source closure itself performs no provider or live operation.

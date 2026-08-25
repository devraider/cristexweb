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
- The renewal validates the live endpoint with the system trust store, exact
  hostname/SAN, and a 30-day threshold before any issuance. Certbot uses a
  persistent protected lineage with `--keep-until-expiring`; it does not use
  `--renew-by-default`, so a failed custody handoff resumes the issued lineage
  instead of requesting duplicate certificates.
- Certbot's Cloudflare DNS plugin creates only the exact challenge TXT record.
  The controller explicitly lists the exact name before issuance, refuses
  pre-existing records, performs one exact-name DNS write/delete scope probe,
  deletes any record left by the locked run through the exact zone API, and
  verifies an empty readback on success and failure.
- Newly generated working copies and upload payloads exist only in a
  mode-0700 temporary workspace with mode-0600 leaves. Certbot's persistent
  account/lineage (including its protected private key) remains only beneath
  the mode-0700 state root so interrupted custody can resume without duplicate
  issuance. The Infisical upload uses only the pre-authenticated local CLI
  session, never a token flag or secret-bearing environment variable.
- Infisical owns `prod:/reactive-resume/dev/tls`, keys `TLS_CRT` and `TLS_KEY`.
  The existing InfisicalStaticSecret materializes
  `cristexhub-dev/reactive-resume-dev-tls` with `creationPolicy: Orphan`.
  Direct `kubectl` Secret writes are forbidden.

## Renewal behavior

The service first checks the currently served public certificate through
`openssl s_client -verify_return_error` and the system CA bundle. It requires
an exact hostname/SAN and at least 30 days remaining before returning a
sanitized `skipped` receipt. If it is within the threshold, it runs pinned
Certbot DNS-01 only, validates the exact single SAN, 30-day validity, and
certificate/key correspondence, then writes an exact two-key payload through the
Infisical path. The Infisical pre-state must already contain exactly `TLS_CRT`
and `TLS_KEY`; post-upload YAML key-set and byte readback are verified without
value output, and a mismatch attempts to restore the pre-upload two-key payload
before failing. Temporary workspace cleanup removes credentials, payload, and
private material; protected Certbot account/lineage metadata remains under the
mode-0700 state root to prevent duplicate issuance.

Install mode installs the pinned Debian packages `certbot=4.0.0-2+deb13u1`
and `python3-certbot-dns-cloudflare=4.0.0-1` with `update_cache: false`, then
verifies their architecture and executable provenance. The service uses the
pinned user-owned Infisical standalone binary version `0.43.121` at
`/home/paul/.nvm/versions/node/v24.19.0/lib/node_modules/@infisical/cli/bin/infisical`;
it does not assume a nonexistent `/usr/local/bin/infisical`. Package installation
and renewal remain separate guarded operations.

## Safe systemd lifecycle

The units are installed disabled and stopped by default. Every wrapper call
invokes Ansible with `--ask-become-pass`; enter the sudo password only in the
controlling terminal and never pipe or redirect the prompt.

```text
ansible/bin/configure-reactive-resume-dev-tls-renewal check
ansible/bin/configure-reactive-resume-dev-tls-renewal apply
ansible/bin/configure-reactive-resume-dev-tls-renewal enable-check
ansible/bin/configure-reactive-resume-dev-tls-renewal enable-apply
```

`apply` is a separate approved host-mutation boundary and installs the exact
Certbot prerequisites while leaving the renewal timer disabled. `enable-apply`
is a second approval boundary. The daily timer is persistent,
randomized by 15 minutes, locked against concurrent execution, non-root, and
hardened with `ProtectSystem`, `ProtectHome=read-only`, `PrivateTmp`,
`NoNewPrivileges`, restricted address families, and an explicit writable state
root. Timer disablement is the rollback; no Kubernetes, DNS, Tunnel, or PROD
rollback is implied.

## Validation and renewal acceptance

Offline contract tests must verify the exact policy, endpoint SAN/trust and
30-day preflight, token metadata and zone/account validation, pinned dependency
provenance, Infisical exact-two-key upload/readback and rollback language,
explicit challenge cleanup verification, systemd hardening, manifest hashes,
wrapper rejection of passthrough arguments, and absence of
certificate/private-key values from source. A separately approved live run must
verify a near-expiry certificate renewal, exact SAN/key match, Infisical
materialization, Traefik HTTPS continuity, and zero temporary residue. The
source closure itself performs no provider or live operation.

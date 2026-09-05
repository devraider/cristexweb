# Reactive Resume DEV shared-realm client

## Status and ownership

**SOURCE CHECK PASSED; PRIVATE RUNTIME ACCEPTANCE RECORDED; VALUES REMAIN
PRIVATE.** The exact value-free shared-realm client source and its
non-passthrough check-only wrapper are implemented. The guarded source check
passed without Keycloak/API/Kubernetes mutation and validates only the committed
contract; it does not itself reconcile or inspect the runtime client.

A separate approved private-runtime acceptance is recorded for this client: the
active `reactive-resume-dev` client uses the shared `cristexhub` realm, its
Infisical-owned secret is materialized only into the private application runtime,
and the private-hostname acceptance cycle covered shared-realm OIDC login,
session, and logout/application flow. That runtime evidence is intentionally
separate from this source check and must not be attributed to this wrapper. Full
application acceptance, database authorization/recovery, and public/PROD gates
remain separate and open.

This is the exact value-free source contract for the privately accepted
Reactive Resume DEV client. Ansible owns this bounded source-only validation;
Keycloak runtime client values remain owned by Infisical Cloud and materialized
only into the private application runtime. This source does not call Keycloak,
read users, read client secrets, or mutate a realm.

The client is additive in the existing `cristexhub` realm. Existing CristexHub
clients and users are preserved; client deletion is forbidden. The old
same-named client in `cristexhub-dev` is represented only as a disabled rollback
handle and must never be deleted. Re-enabling it and restoring the old issuer are
a separate reviewed rollback operation.

## Exact contract

- client ID: `reactive-resume-dev`;
- realm/issuer: `cristexhub` / `https://auth.cristex-soft.com/realms/cristexhub`;
- exact callback: `https://dev-resume.cristex-soft.com/api/auth/oauth2/callback/custom`;
- web origin: `https://dev-resume.cristex-soft.com`;
- post-logout redirect: `https://dev-resume.cristex-soft.com/` (one exact URI,
  never a wildcard);
- confidential OpenID Connect client with standard authorization code flow;
- PKCE challenge method `S256`;
- secret path: `prod:/reactive-resume/dev/runtime`, key `OAUTH_CLIENT_SECRET`;
- secret value: Infisical-owned and private; no value is present in this source;
- old rollback client: `reactive-resume-dev` in `cristexhub-dev`, disabled,
  retained, deletion forbidden.

## Guarded check

```text
ansible/bin/bootstrap-keycloak-reactive-resume-dev-client check
```

The wrapper is non-passthrough and check-only. It requires diff mode, the fixed
single-host limit, a one-run mode-0600 attestation, exact source hashes, and
rejects API/admin token inputs. The action plugin has no URI, command, shell,
Keycloak, or Kubernetes mutation path. It validates only the committed source
contract and emits no values.

No apply mode exists in this closure. The recorded runtime reconciliation and
private acceptance were a separate operation; this wrapper is not its evidence or
owner. Any future client mutation requires an explicit separate API/transport,
least-privilege actor, preserve-existing client/user proof, exact before/after
metadata, and rollback approval.

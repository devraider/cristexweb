# Sanitized PROD route plan fixture provenance

This fixture is an offline, value-sanitized contract artifact for the guarded
6-to-7 route transition. It is not protected state and has never been sent to
Cloudflare.

## Pinned inputs

- OpenTofu: `1.12.5` (`/opt/opentofu/1.12.5/tofu`)
- Cloudflare provider: `5.23.0` (`registry.opentofu.org/cloudflare/cloudflare`)
- Provider schema command: `TF_CLI_CONFIG_FILE=/tmp/tofu-schema-probe/cli.tfrc
  /opt/opentofu/1.12.5/tofu -chdir=/tmp/tofu-schema-probe providers schema -json`
- Offline provider executable SHA-256:
  `73c49687d5b31bc0ea15962be1bb3d75bda3d07782e7b02faeb3c4a1851332fd`
- OpenTofu executable SHA-256:
  `36dae7ca1e4f1552a6faef27179dc16ef403203e956f31416c17b3d87a38c3f4`

The committed `opentofu/.terraform.lock.hcl` remains the source of provider
version and checksum selection. The provider schema was inspected offline;
no provider endpoint, backend, or protected state was contacted.

## Construction and sanitization

The resource/change envelope follows `tofu show -json` format `1.2` emitted by
OpenTofu `1.12.5`. The provider schema's optional/computed fields are retained:
DNS state uses a plain record UUID, CNAME `settings` is normalized to all-false
members, tunnel metadata is the normalized string `"{}"`, and tunnel-config
state retains `id`, `created_at`, `source`, and `version` alongside `config`.
The top-level checks list contains the exact five passing source-variable
validation entries, and `relevant_attributes` contains the exact three
resource/attribute paths emitted for the two route changes. Root output changes
are five exact no-ops with concrete equal before/after values and explicit false
markers, matching the pinned CLI rather than a hand-written create map.
The create change retains the provider's computed `after_unknown` projection;
only schema-declared computed fields are true.

All record IDs in the fixture are deterministic, unique, clearly marked
distinct sanitized placeholders. The tunnel account_tag is deliberately the fixed,
non-secret Cloudflare account ID required by provider semantics, and is paired
with the attested account identity in the one-to-one receipt. The fixture is not
protected state and no credential value is copied. The values are paired with a
one-to-one sanitization receipt:
`opentofu-1.12.5-cloudflare-5.23.0-prod-route.identity-receipt.json`; that
receipt explicitly records that protected identity values are not included.
The receipt SHA-256 is
`5a8b684fff73afaa2412142e5f6d3136e055d3de73fa9cbf6d7fbe207f9ebd71` and the
contract test consumes that receipt before accepting the fixture. The fixture
never claims its DNS placeholders are real Cloudflare identities; the account_tag
is intentionally the fixed semantic account ID.
No API token, credential, tunnel secret, authorization code, or backend state value
is present. Timestamps, comments, hostnames, account/zone/tunnel identifiers,
and origin are fixed semantic contract values required by the offline validator;
no live response is implied.

At runtime the validator receives a mode-0600 identity profile produced by the
canonical wrapper from protected prompts. It binds every existing DNS record ID
and the tunnel `account_tag` to that profile, while the account, zone, tunnel,
address, and output identities remain fixed semantic values. The fixture tests
use the sanitized identity profile only.

To reproduce the envelope, run the provider-schema command above and execute the
`valid_plan()` builder in
`tests/test_opentofu_foundation_prod_plan_contract.py`, then serialize with
`json.dumps(..., sort_keys=True, indent=2)` and normalize the fixture mode to
`0644`. The builder intentionally adds the five output no-ops, exact checks,
relevant-attribute paths, and the six-to-seven resource action set. OpenTofu 1.12.5 emits an explicit
`before: null` and `before_sensitive: false` for the DNS create; the builder
retains those fields exactly. It does not read state or call a provider.

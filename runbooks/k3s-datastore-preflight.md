# Source-only k3s datastore and encryption preflight

## Boundary

This runbook documents the guarded, check-only source for a single read-only k3s
preflight. It does not back up, restore, enable, disable, rotate, re-encrypt,
restart, reconfigure, or mutate a host, cluster, datastore, encryption state,
Secret, or controller configuration. One separately approved live read-only run
completed and emitted only the ignored sanitized artifact described below; its
unknown result authorizes no later operation.

The only entrypoint is:

```text
ansible/bin/preflight-k3s-datastore check
```

The wrapper accepts exactly `check`. It rejects `apply`, extra arguments, task
selection, and passthrough controls; launches the pinned repository controller
from a clean allowlisted environment; requires the ignored local inventory; uses
`--check --diff --limit crtxweb --become --ask-become-pass`; supplies explicit
preflight elevation approval; and preserves `become: false` on every controller-local
delegated task. A mode-0600 single-run attestation is removed on
exit. Direct playbook/role invocation and forged internal variables fail before
any host task.

## Read-only collection

The role runs only fixed `ansible.builtin.command` argv under `no_log: true` and
`check_mode: false` for the read-only probes required by the check: the pinned
k3s version, systemd `ExecStart` and service-state properties, k3s
`secrets-encrypt status --output json`, and a JSON Node list. Fixed `stat` calls
inspect metadata for the k3s executable, configuration file, datastore directory,
and controller artifact. Only after the exact root-owned mode-`0600` config passes
a fixed 65536-byte size gate does a private `slurp` read `config.yaml`. Fixed
private systemd `Environment` and `EnvironmentFiles` property reads must both be
empty before local/default data-directory evidence is accepted. Selected top-level
`data-dir`, `datastore-endpoint`, `cluster-init`, and
`secrets-encryption` fields must be a bounded mapping with unique keys and exact
scalar types. Raw stdout/stderr, ExecStart/config content, paths, URLs, key
metadata, tokens, kubeconfig content, Secret data, and node identities are never
projected or logged. No command is shell-evaluated. Private raw facts are cleared
before report construction.

The parser is strict and fail-closed. It emits no inferred unknown stage as a
known stage. The JSON encryption object is bounded to the official
`EncryptionState` fields; only status/rotation enums are projected. Initial
`start` maps only to `initial`, completed `reencrypt_finished` maps to `finished`,
and either stable projection requires boolean `hashmatch=true`. The report
records:

- validated semantic k3s version or `null`;
- executable, config, ExecStart, and data-directory source stages;
- datastore type (`sqlite`, `embedded_etcd`, `external`, `ambiguous`, or
  `unknown`) plus only marker booleans;
- encryption command/status and rotation stage;
- k3s/Tailscale service stage and bounded Node count/Ready count/health; and
- disclosure-control booleans, all fixed to `false` to indicate that no
  disclosure-bearing evidence field was emitted.

The controller artifact is the ignored
`ansible/.ansible/k3s-datastore-preflight.local.json`, written only after the
protected parse/schema gate and with mode `0600`. Enhanced source emits schema
version `2`; version `1` artifacts predate bounded config/environment/JSON parsing and
are rejected by the Universal Auth gate. The artifact has no timestamp so synthetic
fixtures remain deterministic. Review the artifact
locally; never commit or share it without a separate disclosure review.

## Offline validation

The synthetic fixture
`tests/validate_k3s_datastore_preflight.yml` supplies fake ExecStart, config,
kubeconfig, token, key, node-identity, stdout, and stderr values and asserts
that none reaches the exact report closure. The focused Python contract covers
layout, fixed argv, gates, strict schema, wrapper rejection, and artifact ignore
rules. These tests do not contact SSH, become, Kubernetes, a provider, or a
Secret store.

## Runtime state

Source implementation and offline contracts are present. The separately approved
live read-only run passed `ok=45 changed=1 unreachable=0 failed=0`; its sanitized
schema-v1 artifact recorded `v1.36.2+k3s1`, `config_status=present_safe`,
`data_dir_source=config_override_unknown`, and unknown datastore/encryption/rotation
stages. That result is retained as honest unknown evidence and does not authorize
backup, restore, encryption, host, cluster, or Secret mutation. The official source
pin is K3s tag `v1.36.2+k3s1`, commit
`01b6f04aaa69e8b09303f0393d4b4f1811da23aa`. Any later check, runtime report review,
backup, or recovery operation remains **NOT RUN/BLOCKED** and requires separate
approval.

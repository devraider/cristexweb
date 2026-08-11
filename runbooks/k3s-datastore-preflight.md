# Source-only k3s datastore and encryption preflight

## Boundary

This runbook documents the guarded, check-only source for a single read-only k3s
preflight. It does not back up, restore, enable, disable, rotate, re-encrypt,
restart, reconfigure, or mutate a host, cluster, datastore, encryption state,
Secret, or controller configuration. The source is offline-validated only;
no host invocation is evidence of a live result.

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
`secrets-encrypt status`, and a JSON Node list. Fixed `stat` calls inspect only
metadata for the k3s executable, configuration file, datastore directory, and
controller artifact. Raw stdout/stderr, ExecStart/config content, paths, URLs,
key metadata, tokens, kubeconfig content, Secret data, and node identities are
never projected or logged. No command is shell-evaluated.

The parser is strict and fail-closed. It emits no inferred unknown stage as a
known stage. The report records:

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
protected parse/schema gate and with mode `0600`. It has schema version `1` and
no timestamp so synthetic fixtures remain deterministic. Review the artifact
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

Source implementation and offline contracts are present. A live check, runtime
report, human review of actual datastore/encryption stages, and any later backup
or recovery operation remain **NOT RUN/BLOCKED** and require separate approval.

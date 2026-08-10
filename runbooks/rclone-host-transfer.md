# Guarded host rclone and Infisical proxy recovery transfer

## Status

**INSTALLER CHECK PASSED; FIRST APPLY STOPPED BEFORE MUTATION; RETRY PENDING.**
The approved installer check passed at `ok=25 changed=1 failed=0`; the sole change
was its check-mode prediction. The first apply stopped at
`ok=22 changed=0 failed=1` when nested `ansible.builtin.file` dispatch lacked the
Ansible `normal` action fallback. No installer action completed. Source now covers
that dispatch with a regression test and controller-local integration proof; live
retry remains pending. No host install, rollback, OAuth, Google Drive transfer, host
staging, Secret, Kubernetes, Infisical, or Argo mutation has completed.

## Ownership and custody boundary

All Google Drive/rclone execution belongs on the Debian 13 x86_64 k3s/database host
under guarded Ansible. The inventory-selected non-root host operator is resolved
with getent; committed source does not hardcode an account name. The Mac/controller
retains plaintext generation and decryption plus both local and login-Keychain
copies of the age private identity. The host receives only the existing encrypted
`.tar.gz.age` and its `.sha256`; it never receives the age identity or plaintext.

## Pinned installer

`ansible/bin/install-rclone check|apply|rollback-check|rollback-apply` is the sole
installer entrypoint. It pins rclone `1.71.1`, verifies the official `SHA256SUMS`,
Linux-amd64 ZIP, exact five-file archive layout, and extracted binary digest on the
controller, transfers the archive to `/var/cache/rclone`, installs the root-owned
`/opt/rclone/1.71.1/rclone`, and selects it through `/usr/local/bin/rclone`.
Rollback removes only that exact selector. Versioned payload and cache are retained.
Check mode makes no changes. Apply may ask for sudo interactively; sudo credentials
must never be passed through variables, environment, or files. Both paths require
separate live approval. Check passed; the first apply made no change and the fixed
apply retry plus idempotence remain **NOT RUN**.

## OAuth gate

OAuth is a later, explicit interactive host gate after installer approval. Run as
the resolved non-root operator, using the exact config path
`$HOME/.config/rclone/rclone.conf`; Ansible creates/validates only parent metadata and
must never read, template, copy, or log configuration or token JSON. A fresh host
uses `/usr/local/bin/rclone --config "$HOME/.config/rclone/rclone.conf" config
--auth-no-open-browser` to create exactly the `drive` remote; `config reconnect
drive:` is only for a remote that already exists. Prefer an SSH local-forward callback
from the Mac to the host session rather than copying token JSON through the
controller. Review the rclone-provided localhost callback port, open only that
temporary `ssh -L` tunnel, complete consent in the local browser, close the tunnel,
and verify host config ownership and mode `0600`. No token belongs in Git, Ansible
extra vars, evidence, shell history, or logs. OAuth and independent Google-account
recovery are **NOT RUN/BLOCKED**.

## Exact pending transfer

`ansible/bin/transfer-infisical-proxy-recovery check|apply|cleanup-check|cleanup-apply`
is the only transfer entrypoint. It is pinned to the existing timestamped pending
ciphertext, checksum, digest, and destination
`drive:cristexweb-recovery/infisical-proxy/<timestamp>/`. Apply stages only encrypted
files in operator-owned mode-`0700` host directories with mode-`0600` leaves, uses
four fixed-argv `rclone copyto --immutable --config <home>/.config/rclone/rclone.conf`
commands (two uploads and two readbacks), fetches only encrypted readbacks, and
removes only its exact host staging root after success. It never uses sync, move,
purge, or delete. Existing staging is refused; cleanup accepts only the exact safe
staging root and never changes Drive. Check mode runs only local `listremotes --long`
to prove the sole `drive: drive` backend without network access or writes. The
separately approved apply performs the no-log `about drive:` OAuth request before
staging; rclone may refresh the mode-0600 host config during that approved apply, so
its ownership and mode are revalidated afterward.

The controller then compares ciphertext/checksum, decrypts only in a trapped private
temporary directory, verifies the exact archive membership, TLS chain/hostname/key
relationship, and proxy authentication relationship without output, and atomically
creates mode-`0600` `drive-verified`. The marker is bound to exact filename,
ciphertext digest, and remote path. A failed verification creates no marker and the
trap removes controller plaintext. The current pending bundle and age identity are
never regenerated or rotated by this transfer. The controller file and login
Keychain are two copies in one physical failure domain; independent age-identity
custody remains a separate secret-export gate before recovery can be considered
complete.

`bootstrap-infisical-proxy-secrets` no longer invokes or requires controller rclone.
It must match the exact `drive-verified` marker before creating Secret variables or
reaching Kubernetes mutation. Secret creation remains **NOT RUN/BLOCKED**.

## Approval sequence

1. Offline contracts and syntax checks (source validation only).
2. Separately approved installer `check`, then `apply`, then idempotence `apply`.
3. Separately approved interactive host OAuth with private callback tunnel.
4. Transfer `check`; separately approve `apply`. Use cleanup only for exact encrypted
   residue after a stopped run.
5. Review `drive-verified`; separately approve Secret bootstrap.

Stop on any collision, residue, ownership/mode drift, digest mismatch, selector
drift, config metadata failure, service-health failure, or readback verification
failure. k3s and Tailscale must remain running throughout.

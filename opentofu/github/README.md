# Private Reactive Resume GitHub root

This is a separate, source-only OpenTofu root for the standalone private GitHub
repository `devraider/cristex-reactive-resume`. It is intentionally separate from
the Cloudflare root under `../` so a GitHub plan cannot include the protected
Cloudflare state or the pending public-route change.

## Exact boundary

The root contains exactly three resources:

- `github_repository.reactive_resume_mirror`
  - owner: `devraider`
  - name: `cristex-reactive-resume`
  - visibility: `private`
  - `auto_init = false`
  - issues/projects/wiki disabled
  - `prevent_destroy = true`
- `github_repository_vulnerability_alerts.reactive_resume_mirror`
  - vulnerability alerts enabled through the non-deprecated dedicated resource
  - `prevent_destroy = true`
- `github_actions_repository_permissions.reactive_resume_mirror`
  - Actions disabled before any upstream ref is pushed
  - no selected-actions policy is sent while disabled because GitHub rejects that combination
  - `prevent_destroy = true` because provider deletion resets permissive defaults

The repository is a metadata-only container. This root does not manage source files,
branches, rulesets, branch protection, webhooks, deploy keys, Actions secrets,
repository secrets, package resources, package visibility, teams, collaborators,
applications, tokens, or any GitHub Actions workflow. It does not mirror or publish
application source; source remains owned by the external application repository.

The GitHub provider is pinned to `integrations/github` `6.13.0`. Authentication is
provider-native and must be supplied through the provider's protected environment
mechanism (for example `GITHUB_TOKEN`); no token variable, secret, output, file,
plan, or state value is declared here. The importer rejects any direct-root
`.tf` or `.tf.json` file outside the manifest's exact OpenTofu loadable set.

The independent local backend is:

```text
/var/lib/opentofu/cristexweb/github.tfstate
```

That state requires its own encrypted backup/readback, independent-key recovery,
integrity verification, and isolated `TOFU_DISABLE_CHECKPOINT=1 tofu state list` restore rehearsal before any
provider-backed operation. The separate Ansible lane is documented in
[`runbooks/opentofu-github-state-backup.md`](../../runbooks/opentofu-github-state-backup.md)
and uses only the fixed GitHub state/archive/unit closure; it never controls the
foundation timer or state. Controller-only provider/backend initialization and
warning-free `tofu validate` passed with the state path still absent. No `tofu plan`,
`tofu apply`, import, state mutation, or GitHub API call was performed.

The existing repository import workflow is documented in
[`runbooks/opentofu-github-repository-import.md`](../../runbooks/opentofu-github-repository-import.md).
Before any token prompt, provider initialization, or import, the entrypoint
verifies the committed [`SOURCE.sha256`](SOURCE.sha256) manifest and the
canonical form of the importer itself. The manifest enumerates the complete
tracked root/source closure (OpenTofu files, lockfile, validators, repository
preflight, and import entrypoint), including exact file modes and SHA-256
content. The runtime root's direct `.tf`/`.tf.json` loadable set is compared to
that exact manifest; any missing, extra, symlinked, mode-drifted, or hash-drifted
leaf fails closed. It is a separate guarded entrypoint that accepts only
`check|import`, prompts for an ephemeral protected token, imports exactly the
three existing-repository addresses, validates a protected no-op plan, and
requires the independent encrypted backup/readback and isolated restore lane.
It has no create, delete, destroy, apply, state-push, or state-removal path.
Every OpenTofu child runs with `TOFU_DISABLE_CHECKPOINT=1`, including the final
state-list gate.

## Apply gates

Before a future separately approved check/plan/apply:

1. confirm the canonical Git worktree and this root's exact file/resource closure;
2. with the token entered by the guarded import entrypoint, run its read-only
   exact-repository preflight; it pins `api.github.com`, verifies the authenticated
   identity is exactly `devraider`, and requires the existing repository to be
   private. The separate `bin/check-repository-absence` remains the create-path
   guard and must not be used for this existing-repository import;
3. before genesis, run the separate absence attestation/readback/restore rehearsal;
   after genesis, back up and rehearse recovery of `github.tfstate`;
4. write the binary plan and `tofu show -json` rendering to protected mode-`0600`
   files, then run `bin/validate-create-plan PLAN.json`;
5. for an existing repository, run only the three exact imports and accept only
   the protected no-op plan; reject replacement, create, destroy, source-file,
   secret, webhook, deploy-key, permissive Actions, package, collaborator, team,
   provider drift, output, or Cloudflare address;
6. after import, require immutable encrypted state backup/readback, isolated restore,
   a second no-op plan, and private repository post-state verification. A separate
   create-path may accept only the validated three-create plan; it is not part of
   this import operation.

Creating this repository does not authorize a source push, image build, GHCR package,
workflow, Kubernetes object, Infisical value, PostgreSQL role/Secret, deployment, or
public route. Those are separate ownership and approval boundaries.

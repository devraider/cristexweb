# Private Reactive Resume GitHub root

This is a separate, source-only OpenTofu root for the standalone private GitHub
repository `devraider/cristex-reactive-resume`. It is intentionally separate from
the Cloudflare root under `../` so a GitHub plan cannot include the protected
Cloudflare state or the pending public-route change.

## Exact boundary

The root contains exactly two resources:

- `github_repository.reactive_resume_mirror`
  - owner: `devraider`
  - name: `cristex-reactive-resume`
  - visibility: `private`
  - `auto_init = false`
  - issues/projects/wiki/downloads disabled
  - vulnerability alerts enabled
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
plan, or state value is declared here.

The independent local backend is:

```text
/var/lib/opentofu/cristexweb/github.tfstate
```

That state requires its own encrypted backup/readback, independent-key recovery,
integrity verification, and isolated `tofu state list` restore rehearsal before any
provider-backed operation. No `tofu init`, `tofu plan`, `tofu apply`, import, or
GitHub API call was performed while authoring this source.

## Apply gates

Before a future separately approved check/plan/apply:

1. confirm the canonical Git worktree and this root's exact file/resource closure;
2. with `GITHUB_TOKEN` supplied only by the protected process environment, run
   `bin/check-repository-absence`; it performs one fixed GET and succeeds only on an
   authenticated absent-repository result. Import an existing matching repository
   instead of creating a duplicate;
3. back up and rehearse recovery of `github.tfstate`;
4. write the binary plan and `tofu show -json` rendering to protected mode-`0600`
   files, then run `bin/validate-create-plan PLAN.json`;
5. accept only the two exact GitHub create actions; reject replacement, destroy,
   source-file, secret, webhook, deploy-key, permissive Actions, package,
   collaborator, team, provider drift, output, or Cloudflare address;
6. apply only the previously validated binary plan after explicit GitHub provider
   and repository approval, then require a second no-op plan and private repository
   post-state verification.

Creating this repository does not authorize a source push, image build, GHCR package,
workflow, Kubernetes object, Infisical value, PostgreSQL role/Secret, deployment, or
public route. Those are separate ownership and approval boundaries.

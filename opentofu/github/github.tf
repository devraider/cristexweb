resource "github_repository" "reactive_resume_mirror" {
  name                 = "cristex-reactive-resume"
  description          = "Private standalone Reactive Resume source mirror"
  visibility           = "private"
  auto_init            = false
  has_issues           = false
  has_projects         = false
  has_wiki             = false
  has_downloads        = false
  vulnerability_alerts = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "github_actions_repository_permissions" "reactive_resume_mirror" {
  repository      = github_repository.reactive_resume_mirror.name
  enabled         = false
  allowed_actions = "selected"

  allowed_actions_config {
    github_owned_allowed = false
    verified_allowed     = false
    patterns_allowed     = []
  }

  lifecycle {
    prevent_destroy = true
  }
}

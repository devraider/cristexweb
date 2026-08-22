resource "github_repository" "reactive_resume_mirror" {
  name         = "cristex-reactive-resume"
  description  = "Private standalone Reactive Resume source mirror"
  visibility   = "private"
  auto_init    = false
  has_issues   = false
  has_projects = false
  has_wiki     = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "github_repository_vulnerability_alerts" "reactive_resume_mirror" {
  repository = github_repository.reactive_resume_mirror.name
  enabled    = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "github_actions_repository_permissions" "reactive_resume_mirror" {
  repository = github_repository.reactive_resume_mirror.name
  enabled    = false

  lifecycle {
    prevent_destroy = true
  }
}

terraform {
  backend "local" {
    path = "/var/lib/opentofu/cristexweb/github.tfstate"
  }
}

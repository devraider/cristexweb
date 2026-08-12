variable "cloudflare_account_id" {
  description = "Cloudflare account ID. Supply through an uncommitted tfvars file or environment variable."
  type        = string
  sensitive   = false

  validation {
    condition     = can(regex("^[0-9a-f]{32}$", var.cloudflare_account_id))
    error_message = "cloudflare_account_id must be a 32-character lowercase hexadecimal Cloudflare account ID."
  }
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for cristex-soft.com. Supply through an uncommitted tfvars file or environment variable."
  type        = string
  sensitive   = false

  validation {
    condition     = can(regex("^[0-9a-f]{32}$", var.cloudflare_zone_id))
    error_message = "cloudflare_zone_id must be a 32-character lowercase hexadecimal Cloudflare zone ID."
  }
}

variable "cloudflare_tunnel_name" {
  description = "Stable human-readable name for the remotely managed Cloudflare Tunnel."
  type        = string
  default     = "cristexhub-keycloak"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$", var.cloudflare_tunnel_name))
    error_message = "cloudflare_tunnel_name must be 2-64 lowercase letters, digits, or hyphens and may not start or end with a hyphen."
  }
}

variable "public_hostname" {
  description = "Approved public hostname routed by the Tunnel."
  type        = string
  default     = "auth.cristex-soft.com"

  validation {
    condition     = var.public_hostname == "auth.cristex-soft.com"
    error_message = "Only auth.cristex-soft.com is authorized by this module."
  }
}

variable "traefik_origin_service" {
  description = "Private Traefik origin URL reached by cloudflared inside the cluster."
  type        = string
  default     = "http://traefik.kube-system.svc.cluster.local:80"

  validation {
    condition     = var.traefik_origin_service == "http://traefik.kube-system.svc.cluster.local:80"
    error_message = "traefik_origin_service is fixed to the private bundled Traefik Service URL."
  }
}

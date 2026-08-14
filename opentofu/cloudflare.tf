resource "cloudflare_zero_trust_tunnel_cloudflared" "keycloak" {
  account_id = var.cloudflare_account_id
  name       = var.cloudflare_tunnel_name
  config_src = "cloudflare"

  lifecycle {
    prevent_destroy = true
  }
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "keycloak" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.keycloak.id
  source     = "cloudflare"

  config = {
    ingress = [
      {
        hostname = var.public_hostname
        service  = var.traefik_origin_service
      },
      {
        hostname = "dev-hub.cristex-soft.com"
        service  = var.traefik_origin_service
      },
      {
        service = "http_status:404"
      }
    ]
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "cloudflare_dns_record" "keycloak" {
  zone_id = var.cloudflare_zone_id
  name    = var.public_hostname
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.keycloak.id}.cfargotunnel.com"
  ttl     = 1
  proxied = true
  comment = "Managed by OpenTofu; Cloudflare Tunnel to private Traefik origin"

  lifecycle {
    prevent_destroy = true
  }
}

resource "cloudflare_dns_record" "cristexhub_dev" {
  zone_id = var.cloudflare_zone_id
  name    = "dev-hub.cristex-soft.com"
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.keycloak.id}.cfargotunnel.com"
  ttl     = 1
  proxied = true
  comment = "Managed by OpenTofu; Cloudflare Tunnel to CristexHub DEV via private Traefik origin"

  lifecycle {
    prevent_destroy = true
  }
}

resource "cloudflare_dns_record" "argocd_tailscale" {
  zone_id = var.cloudflare_zone_id
  name    = "argo.cristex-soft.com"
  type    = "A"
  content = "100.122.139.32"
  ttl     = 300
  proxied = false
  comment = "Managed by OpenTofu; private Argo CD endpoint on Tailscale"

  lifecycle {
    prevent_destroy = true
  }
}

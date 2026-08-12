output "tunnel_id" {
  description = "Cloudflare Tunnel UUID; required for the separately guarded token handoff."
  value       = cloudflare_zero_trust_tunnel_cloudflared.keycloak.id
}

output "tunnel_name" {
  description = "Cloudflare Tunnel name."
  value       = cloudflare_zero_trust_tunnel_cloudflared.keycloak.name
}

output "public_hostname" {
  description = "Public hostname configured for the Tunnel."
  value       = var.public_hostname
}

output "dns_record_name" {
  description = "DNS record name managed for the Tunnel hostname."
  value       = cloudflare_dns_record.keycloak.name
}

output "token_handoff" {
  description = "The Tunnel token is intentionally not retrieved, output, or stored by OpenTofu."
  value       = "MANUAL_INFISICAL_HANDOFF_REQUIRED"
}

output "api_endpoint" {
  description = "Base URL the frontend should call. With apig_public=true this is publicly resolvable."
  value       = "https://${huaweicloud_apig_group.main.id}.apic.${var.region}.huaweicloudapis.com/release"
}

output "apig_app_code" {
  description = "AppCode sent as the X-Apig-AppCode header by the frontend (APIG App authentication)."
  value       = huaweicloud_apig_appcode.main.value
}

output "obs_bucket" {
  value = huaweicloud_obs_bucket.main.bucket
}

output "geminidb_endpoint" {
  description = "DynamoDB-compatible endpoint (host:port) the functions connect to."
  value       = "http://${huaweicloud_geminidb_instance.main.lb_ip_address}:${huaweicloud_geminidb_instance.main.lb_port}"
}

output "function_urns" {
  value = { for k, v in huaweicloud_fgs_function.fn : k => v.urn }
}

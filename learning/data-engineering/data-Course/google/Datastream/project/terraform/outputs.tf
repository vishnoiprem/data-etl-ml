# outputs.tf — the values you need after `terraform apply`.

output "stream_name" {
  description = "The full resource name of the Datastream stream."
  value       = google_datastream_stream.main.name
}

output "stream_id" {
  description = "The id of the Datastream stream."
  value       = google_datastream_stream.main.stream_id
}

output "network_config_name" {
  description = "The Datastream network config name."
  value       = google_datastream_network_config.network.name
}

output "source_connection_profile" {
  description = "The MySQL connection profile name."
  value       = google_datastream_mysql_connection_profile.source.name
}

output "destination_connection_profile" {
  description = "The BigQuery connection profile name."
  value       = google_datastream_bigquery_connection_profile.destination.name
}

output "ip_allocation_name" {
  description = "The IP allocation name — this is the address the source database must allow."
  value       = google_datastream_network_config_ip_allocations.range.name
}

output "verify_command" {
  description = "The command that lists the streams in the project."
  value       = "gcloud datastream streams list --location=${var.region} --project=${var.project_id}"
}

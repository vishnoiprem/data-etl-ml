# variables.tf — inputs for the Datastream Terraform module.

variable "project_id" {
  description = "The GCP project id that hosts the Datastream resources."
  type        = string
}

variable "region" {
  description = "The region for the Datastream cluster. Keep it the same as the BigQuery dataset region."
  type        = string
  default     = "us-central1"
}

variable "network_id" {
  description = "The full resource path of the VPC network, e.g. projects/PROJECT/global/networks/default."
  type        = string
  default     = "projects/YOUR_PROJECT_ID/global/networks/default"
}

variable "private_range_cidr" {
  description = "The CIDR range reserved for the Datastream private services connection."
  type        = string
  default     = "10.0.0.0/28"
}

variable "static_ip_address" {
  description = "The static IP address Datastream uses to reach the source database."
  type        = string
  default     = "10.0.0.2"
}

variable "netmask" {
  description = "The netmask for the static IP allocation."
  type        = string
  default     = "255.255.255.240"
}

variable "network_config_name" {
  description = "The name of the Datastream network config."
  type        = string
  default     = "network-config"
}

variable "stream_id" {
  description = "The id of the Datastream stream."
  type        = string
  default     = "stream"
}

variable "stream_display_name" {
  description = "The human-readable name of the Datastream stream."
  type        = string
  default     = "Course stream"
}

variable "source_config_id" {
  description = "The id of the MySQL source config."
  type        = string
  default     = "mysql-source"
}

variable "source_connection_profile_id" {
  description = "The id of the MySQL connection profile."
  type        = string
  default     = "mysql-connection"
}

variable "destination_config_id" {
  description = "The id of the BigQuery destination config."
  type        = string
  default     = "bigquery-destination"
}

variable "destination_connection_profile_id" {
  description = "The id of the BigQuery connection profile."
  type        = string
  default     = "bigquery-connection"
}

variable "mysql_hostname" {
  description = "The hostname or IP of the MySQL instance being captured."
  type        = string
  default     = "10.0.0.3"
}

variable "mysql_port" {
  description = "The MySQL port."
  type        = number
  default     = 3306
}

variable "mysql_username" {
  description = "The Datastream replication user."
  type        = string
  default     = "datastream_user"
}

variable "mysql_password" {
  description = "The password for the replication user. Supply it from a secret store, never in code."
  type        = string
  sensitive   = true
  default     = ""
}

variable "datastream_service_account" {
  description = "The service account Datastream uses to write into BigQuery."
  type        = string
  default     = "YOUR_PROJECT_ID-datastream@YOUR_PROJECT_ID.iam.gserviceaccount.com"
}

variable "included_tables" {
  description = "The tables to capture."
  type        = list(string)
  default     = ["inventory.customers"]
}

variable "excluded_tables" {
  description = "The tables to skip."
  type        = list(string)
  default     = []
}

variable "read_consistency_window" {
  description = "The read consistency window, in seconds. Larger = more consistent, more latency."
  type        = string
  default     = "5s"
}

variable "source_schema_name" {
  description = "The fully-qualified source table, e.g. inventory.customers."
  type        = string
  default     = "inventory.customers"
}

variable "target_table_name" {
  description = "The fully-qualified BigQuery destination table."
  type        = string
  default     = "datastream.customers"
}

variable "bigquery_dataset_id" {
  description = "The BigQuery dataset id."
  type        = string
  default     = "datastream"
}

variable "merge_keys" {
  description = "The merge key columns. These identify a row uniquely in the destination."
  type        = list(string)
  default     = ["customer_id"]
}

variable "enable_backfill" {
  description = "Whether to backfill the existing table contents before streaming."
  type        = bool
  default     = true
}

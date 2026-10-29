// main.tf — Google Cloud Datastream infrastructure for the course.
//
// This Terraform module creates the minimum viable Datastream setup:
//
//   * a Datastream cluster (network config + IP allocation)
//   * a Kafka stream (the "stream" that holds the discovered source objects)
//   * a MySQL source (the CDC source config)
//   * a BigQuery destination with a merge-key mapping
//
// Everything is parameterised by variables.tf and outputs.tf.
//
// Usage:
//   cd project/terraform
//   terraform init
//   terraform plan -var="project_id=my-project" -var="region=us-central1"
//   terraform apply -var="project_id=my-project" -var="region=us-central1"

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

# --------------------------------------------------------------------------
# Enable the APIs Datastream needs
# --------------------------------------------------------------------------

resource "google_project_service" "datastream" {
  project            = var.project_id
  service            = "datastream.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "bigquery" {
  project            = var.project_id
  service            = "bigquery.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  project            = var.project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# --------------------------------------------------------------------------
# Network config
# --------------------------------------------------------------------------

resource "google_service_networking_connection" "private_range" {
  network                 = var.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [var.private_range_cidr]
}

# The VPC peering Datastream needs. It is created before the cluster,
# because the cluster's network config references it by name.
resource "google_datastream_network_config" "network" {
  location = var.region
  name     = var.network_config_name

  network {
    network_attachment = google_service_networking_connection.private_range.network
  }
}

resource "google_datastream_network_config_ip_allocations" "range" {
  location = var.region
  name     = var.network_config_name

  ip_address    = var.static_ip_address
  netmask       = var.netmask
  purpose      = "SHARED"
}

# --------------------------------------------------------------------------
# The stream
# --------------------------------------------------------------------------

resource "google_datastream_stream" "main" {
  location     = var.region
  stream_id    = var.stream_id
  display_name = var.stream_display_name
  force_destroy = true

  source_config {
    source_connection_profile {
      name = var.source_connection_profile_id
    }
  }

  destination_config {
    destination_connection_profile {
      name = var.destination_connection_profile_id
    }
  }

  dynamic "backfill_all" {
    for_each = var.enable_backfill ? [1] : []
    content {
      source_connection_profile = google_datastream_mysql_connection_profile.source.name
    }
  }

  dynamic "backfill_none" {
    for_each = var.enable_backfill ? [] : [1]
    content {}
  }
}

# --------------------------------------------------------------------------
# Source: MySQL
# --------------------------------------------------------------------------

resource "google_datastream_mysql_connection_profile" "source" {
  location     = var.region
  connection_profile_id = var.source_connection_profile_id
  display_name = var.source_connection_profile_id
  force_destroy = true

  hostname  = var.mysql_hostname
  port      = var.mysql_port
  username  = var.mysql_username
  password  = var.mysql_password
  network   = google_datastream_network_config.network.name

  mysql_config {
    ip_address = google_datastream_network_config_ip_allocations.range.name
  }
}

resource "google_datastream_mysql_source_config" "source" {
  location = var.region
  source_id = var.source_config_id

  source_connection_profile_id = google_datastream_mysql_connection_profile.source.connection_profile_id

  mysql_source_config {
    include_tables {
      table_included = var.included_tables
    }

    exclude_tables {
      table_excluded = var.excluded_tables
    }

    # The read consistency window. A larger window gives Datastream more
    # time to reconcile parallel transactions, at the cost of latency.
    read_from_transaction {
      read_from_transaction {
        read_consistency_window = var.read_consistency_window
      }
    }
  }
}

# --------------------------------------------------------------------------
# Destination: BigQuery
# --------------------------------------------------------------------------

resource "google_datastream_bigquery_connection_profile" "destination" {
  location     = var.region
  connection_profile_id = var.destination_connection_profile_id
  display_name = var.destination_connection_profile_id
  force_destroy = true

  credential {
    service_account = var.datastream_service_account
  }
}

resource "google_datastream_bigquery_destination_config" "destination" {
  location = var.region
  destination_id = var.destination_config_id

  destination_connection_profile_id = google_datastream_bigquery_connection_profile.destination.connection_profile_id

  bigquery_destination_config {
    source_tables {
      table {
        source_table = var.source_schema_name
        target_table = var.target_table_name
      }

      # Merge keys. This is the single most important field in the whole
      # configuration: it tells Datastream how to turn a stream of changes
      # back into a table. Wrong merge keys means wrong data, silently.
      primary_key {
        merge_keys {
          merge_key = var.merge_keys
        }
      }
    }

    single_target_dataset {
      dataset_id = var.bigquery_dataset_id
    }
  }
}

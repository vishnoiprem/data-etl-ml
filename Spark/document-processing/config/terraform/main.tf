# config/terraform/main.tf
# Terraform configuration for Azure infrastructure

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource group
resource "azurerm_resource_group" "doc_processing" {
  name     = "rg-doc-processing-${var.environment}"
  location = var.location
  tags     = var.tags
}

# Storage account
resource "azurerm_storage_account" "doc_storage" {
  name                     = "stgdoc${var.environment}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.doc_processing.name
  location                 = azurerm_resource_group.doc_processing.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
  }

  tags = var.tags
}

# Storage containers
resource "azurerm_storage_container" "containers" {
  for_each = toset([
    "incoming-documents",
    "bronze-layer",
    "silver-layer",
    "gold-layer",
    "dead-letter-queue"
  ])

  name                  = each.key
  storage_account_name  = azurerm_storage_account.doc_storage.name
  container_access_type = "private"
}

# Azure Document Intelligence
resource "azurerm_cognitive_account" "doc_intelligence" {
  name                = "cog-doc-${var.environment}"
  location            = azurerm_resource_group.doc_processing.location
  resource_group_name = azurerm_resource_group.doc_processing.name
  kind                = "FormRecognizer"
  sku_name            = "S0"

  tags = var.tags
}

# Databricks workspace
resource "azurerm_databricks_workspace" "workspace" {
  name                = "dbw-doc-processing-${var.environment}"
  resource_group_name = azurerm_resource_group.doc_processing.name
  location            = azurerm_resource_group.doc_processing.location
  sku                 = "premium"

  custom_parameters {
    no_public_ip = true
  }

  tags = var.tags
}

# Databricks cluster configuration
resource "databricks_cluster" "processing_cluster" {
  cluster_name = "doc-processing-${var.environment}"
  spark_version = databricks_spark_version.latest.id
  node_type_id  = data.databricks_node_type.smallest.id
  autoscale {
    min_workers = 2
    max_workers = 10
  }

  spark_conf = {
    "spark.databricks.delta.preview.enabled" = "true"
    "spark.databricks.io.cache.enabled" = "true"
  }

  autotermination_minutes = 30
}

# Random suffix for unique names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Variables
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    "Application" = "DocumentProcessing"
    "ManagedBy"   = "Terraform"
  }
}
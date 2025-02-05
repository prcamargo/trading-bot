terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.1.0"
    }
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
   features {
    resource_group {
        prevent_deletion_if_contains_resources = false
    }
   }
}
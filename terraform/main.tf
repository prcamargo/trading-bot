terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "trading_bot" {
  name     = "trading-bot-rg"
  location = "eastus"
}

resource "azurerm_container_group" "bot" {
  name                = "trading-bot-container"
  location            = azurerm_resource_group.trading_bot.location
  resource_group_name = azurerm_resource_group.trading_bot.name
  ip_address_type     = "Public"
  os_type             = "Linux"

  container {
    name   = "trading-bot"
    image  = "${azurerm_container_registry.acr.login_server}/trading-bot:latest"
    cpu    = "1"
    memory = "2"

    ports {
      port     = 80
      protocol = "TCP"
    }

    environment_variables = {
      BINANCE_API_KEY    = var.binance_api_key
      BINANCE_API_SECRET = var.binance_api_secret
    }
  }
}

resource "azurerm_container_registry" "acr" {
  name                = "tradingBotRegistry"
  resource_group_name = azurerm_resource_group.trading_bot.name
  location            = azurerm_resource_group.trading_bot.location
  sku                 = "Basic"
  admin_enabled       = true
}
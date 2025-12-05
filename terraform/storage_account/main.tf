resource "random_pet" "rg_name" {
  prefix = var.resource_group_name_prefix
}

resource "azurerm_resource_group" "rg" {
  location = var.resource_group_location
  name     = random_pet.rg_name.id
}

resource "random_pet" "azurerm_kubernetes_cluster_name" {
  prefix = "cluster"
}

# Azure Storage Account
resource "azurerm_storage_account" "storage" {
  name                     = "appstorageaccountmetube"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  shared_access_key_enabled = true
  # Enable large file shares
  large_file_share_enabled = true
}

# Azure File Share
resource "azurerm_storage_share" "share" {
  name                 = "aksshare"
  storage_account_name = azurerm_storage_account.storage.name
  quota                = 10
}
output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "storage_account_key" {
  value     = azurerm_storage_account.storage.primary_access_key
  sensitive = true
}

output "storage_account_name" {
  value     = azurerm_storage_account.storage.name
  sensitive = true
}
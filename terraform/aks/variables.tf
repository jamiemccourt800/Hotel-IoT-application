variable "resource_group_location" {
  type        = string
  default     = "westeurope"
  description = "Location of the resource group."
}

variable "resource_group_name_prefix" {
  type        = string
  default     = "rg"
  description = "Prefix of the resource group name that's combined with a random ID so name is unique in your Azure subscription."
}

variable "node_count" {
  type        = number
  description = "The initial quantity of nodes for the node pool."
  default     = 2
}

variable "msi_id" {
  type        = string
  description = "The Managed Service Identity ID. Set this value if you're running this example using Managed Identity as the authentication method."
  default     = null
}

variable "username" {
  type        = string
  description = "The admin username for the new cluster."
  default     = "azureadmin"
}

variable "subscription_id" {
  type        = string
  description = "The Azure subscription ID."
  # default     = "00000000-0000-0000-0000-000000000000"
}

variable "kubeconfig_output_path" {
  type        = string
  description = "The file path to output the kubeconfig file."
  default     = "./kubeconfig"
}

variable "storage_account_name" {
  type        = string
  description = "The storage account name for the cluster."
}

variable "storage_account_key" {
  type        = string
  description = "The storage account key for the cluster."
}

variable "grafana_disk_id" {
  type        = string
  description = "The Managed Disk ID for Grafana data disk."
  default     = null
}

variable "mongo_data_pv" {
  type        = string
  description = "The Managed Disk ID for MongoDB data disk."
  default     = null
}


variable "vm_data_pv" {
  type        = string
  description = "The Managed Disk ID for MongoDB data disk."
  default     = null
}


variable "mosquito_data_pv" {
  type        = string
  description = "The Managed Disk ID for MongoDB data disk."
  default     = null
}

variable "argocd_image_updater_token" {
  type = string
  description = "The token for ArgoCD Image Updater to access private container registry."
  default = ""
}
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

resource "random_pet" "azurerm_kubernetes_cluster_dns_prefix" {
  prefix = "dns"
}

resource "azurerm_kubernetes_cluster" "k8s" {
  location            = azurerm_resource_group.rg.location
  name                = random_pet.azurerm_kubernetes_cluster_name.id
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = random_pet.azurerm_kubernetes_cluster_dns_prefix.id

  identity {
    type = "SystemAssigned"
  }

  default_node_pool {
    name       = "agentpool"
    vm_size    = "Standard_D2_v2"
    node_count = var.node_count
  }
  linux_profile {
    admin_username = var.username

    ssh_key {
      key_data = azapi_resource_action.ssh_public_key_gen.output.publicKey
    }
  }
  network_profile {
    network_plugin    = "kubenet"
    load_balancer_sku = "standard"
  }
}

provider "kubernetes" {
  host = azurerm_kubernetes_cluster.k8s.kube_config.0.host

  client_certificate     = base64decode(azurerm_kubernetes_cluster.k8s.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.k8s.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.k8s.kube_config.0.cluster_ca_certificate)
}

resource "kubernetes_secret" "azure_file_credentials" {
  metadata {
    name      = "azure-storage-secret"
    namespace = "app-microservices"
  }

  data = {
    # use data for base64 encoded values
    azurestorageaccountname = var.storage_account_name
    azurestorageaccountkey  = var.storage_account_key
  }

  type = "Opaque"

  depends_on = [
    azurerm_kubernetes_cluster.k8s
  ]
}


# Modify the kustomization_build data source
data "kustomization_build" "manifests_crds" {
  path = "${path.module}/../../deployment/crds"
  kustomize_options {
    enable_helm = true
    helm_path = "helm"
  }
}

resource "kustomization_resource" "pc0" {
  for_each = data.kustomization_build.manifests_crds.ids_prio[0]
  manifest = data.kustomization_build.manifests_crds.manifests[each.value]
  # depends_on = [null_resource.kustomization_patch]
}

resource "kustomization_resource" "pc1" {
  for_each   = data.kustomization_build.manifests_crds.ids_prio[1]
  manifest   = data.kustomization_build.manifests_crds.manifests[each.value]
  depends_on = [kustomization_resource.pc0]
}

resource "kustomization_resource" "pc2" {
  for_each   = data.kustomization_build.manifests_crds.ids_prio[2]
  manifest   = data.kustomization_build.manifests_crds.manifests[each.value]
  depends_on = [kustomization_resource.pc1]
}

# Modify the kustomization_build data source
data "kustomization_build" "manifests" {
  path = "${path.module}/../../deployment/prod"
  kustomize_options {
    enable_helm = true
    helm_path = "helm"
  }
}

resource "kustomization_resource" "p0" {
  for_each = data.kustomization_build.manifests.ids_prio[0]
  manifest = data.kustomization_build.manifests.manifests[each.value]
  depends_on = [
    data.kustomization_build.manifests_crds,
    kustomization_resource.pc0,
    kustomization_resource.pc1,
    kustomization_resource.pc2
  ]
}

resource "kustomization_resource" "p1" {
  for_each   = data.kustomization_build.manifests.ids_prio[1]
  manifest   = data.kustomization_build.manifests.manifests[each.value]
  depends_on = [
    kustomization_resource.p0,
    data.kustomization_build.manifests_crds,
    kustomization_resource.pc0,
    kustomization_resource.pc1,
    kustomization_resource.pc2
  ]
}

resource "kustomization_resource" "p2" {
  for_each   = data.kustomization_build.manifests.ids_prio[2]
  manifest   = data.kustomization_build.manifests.manifests[each.value]
  depends_on = [
    kustomization_resource.p1,
    data.kustomization_build.manifests_crds,
    kustomization_resource.pc0,
    kustomization_resource.pc1,
    kustomization_resource.pc2
  ]
}

resource "local_file" "kubeconfig_file" {
  # This should be the full path where you want the file saved
  filename = var.kubeconfig_output_path

  # The content comes from the Terraform output containing the kubeconfig data.
  # Replace 'module.aks.kubeconfig_raw' with your actual output variable.
  content = azurerm_kubernetes_cluster.k8s.kube_config_raw

  # Set file permissions to ensure only the owner can read/write the secret file
  file_permission = "0600"
}
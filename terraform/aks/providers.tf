terraform {
  required_version = ">=1.0"

  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "~>1.5"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "0.9.1"
    }
    kustomization = {
      source  = "kbst/kustomization"
      version = "0.9.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.36.0"
    }
    helm = {
      source = "hashicorp/helm"
      version = "3.1.1"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  subscription_id = var.subscription_id
}

provider "kustomization" {
  # one of kubeconfig_path, kubeconfig_raw or kubeconfig_incluster must be set

  # kubeconfig_path = "/.kube/config"
  # can also be set using KUBECONFIG_PATH environment variable

  # kubeconfig_raw = data.template_file.kubeconfig.rendered
  kubeconfig_raw = azurerm_kubernetes_cluster.k8s.kube_config_raw

  # kubeconfig_incluster = true
}

provider "helm" {
  kubernetes = {
    host                   = local.kubeconfig_host
    client_certificate     = local.client_certificate
    client_key             = local.client_key
    cluster_ca_certificate = local.cluster_ca_certificate
  }
}

provider "kubernetes" {
  host = local.kubeconfig_host
  client_certificate = local.client_certificate
  client_key         = local.client_key
  cluster_ca_certificate = local.cluster_ca_certificate
}
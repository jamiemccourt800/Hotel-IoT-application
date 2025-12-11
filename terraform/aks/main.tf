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
    vm_size    = "Standard_F2s_v2"
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
  lifecycle {
    ignore_changes = [
      default_node_pool[0],
    ]
  }
}

resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
  }
}

locals {
  kubeconfig_host        = azurerm_kubernetes_cluster.k8s.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.k8s.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.k8s.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.k8s.kube_config.0.cluster_ca_certificate)
}

# resource "kubernetes_config_map" "argocd_cm" {
#     metadata {
#         name      = "argocd-cm"
#         namespace = kubernetes_namespace.argocd.metadata[0].name
#       labels = {
#         "app.kubernetes.io/name" = "argocd-cm"
#         "app.kubernetes.io/part-of" = "argocd"
#       }
#     }
#
#     data = {
#         "kustomize.buildOptions" = "--enable-helm"
#     }
#     depends_on = [
#       kubernetes_namespace.argocd,
#       helm_release.argocd
#     ]
# }

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = kubernetes_namespace.argocd.metadata[0].name
  version    = "v8.2.6"

  values = [
    yamlencode({
      crds = {
        install = true
      }

      server = {
        service = {
          type = "LoadBalancer"
        }
      }

      configs = {
        cm = {
          # becomes data.kustomize.buildOptions in argocd-cm
          "kustomize.buildOptions" = "--enable-helm"
          "accounts.image-updater" = "apiKey"
        }

        rbac = {
          # this becomes data.policy.csv in argocd-rbac-cm
          "policy.csv" = <<-EOT
            p, role:image-updater, applications, get, *, allow
            p, role:image-updater, applications, list, *, allow
            p, role:image-updater, applications, update, *, allow
            p, role:image-updater, applications, sync, *, allow

            g, image-updater, role:image-updater
          EOT

          # optional, but chart likes having scopes defined
          "scopes" = "[groups, email]"
        }
      }
    })
  ]

  depends_on = [
    azurerm_kubernetes_cluster.k8s,
    kubernetes_namespace.argocd
  ]
}


data "kubernetes_service_v1" "argocd_server" {
  metadata {
    name      = "argocd-server"
    namespace = kubernetes_namespace.argocd.metadata[0].name
  }

  depends_on = [helm_release.argocd]
}

data "kubernetes_secret_v1" "argocd_initial_admin" {
  metadata {
    name      = "argocd-initial-admin-secret"
    namespace = "argocd"
  }

  depends_on = [helm_release.argocd]
}

locals {
  argocd_admin_password = (
    data.kubernetes_secret_v1.argocd_initial_admin.data["password"]
  )
}

resource "kubernetes_manifest" "argocd_cluster_crds_app" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name      = "cluster-crds"
      namespace = "argocd"
      annotations = {
        "argocd.argoproj.io/sync-options" = "ServerSideApply=true"
      }
    }
    spec = {
      project = "default"
      source = {
        repoURL        = "https://gitlab.comp.dkit.ie/D00271292/devops-project-gitops.git"
        targetRevision = "main"
        path           = "infra/crds"
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = "argocd"
      }
      syncPolicy = {
        automated = {
          prune    = false
          selfHeal = false
        }
        syncOptions = ["ServerSideApply=true"]
      }
    }
  }

  depends_on = [
    kubernetes_namespace.argocd,
    data.kubernetes_service_v1.argocd_server,
    helm_release.argocd,
    azurerm_kubernetes_cluster.k8s,
  ]
}

# resource "kubernetes_manifest" "argocd_infra_app" {
#   manifest = {
#     apiVersion = "argoproj.io/v1alpha1"
#     kind       = "Application"
#     metadata = {
#       name      = "infra"
#       namespace = "argocd"
#       finalizers = [
#         "resources-finalizer.argocd.argoproj.io"
#       ]
#     }
#     spec = {
#       project = "default"
#       source = {
#         repoURL        = "https://gitlab.comp.dkit.ie/D00271292/devops-project-gitops.git"
#         targetRevision = "main"
#         path           = "infra"
#       }
#       destination = {
#         server    = "https://kubernetes.default.svc"
#         namespace = "infra"
#       }
#       syncPolicy = {
#         automated = {
#           prune    = true
#           selfHeal = true
#         }
#         syncOptions = [
#           "CreateNamespace=true"
#         ]
#       }
#     }
#   }
#
#   depends_on = [
#     kubernetes_manifest.argocd_cluster_crds_app,
#     helm_release.argocd
#   ]
# }

resource "kubernetes_manifest" "argocd_iot_hotel_chain_app" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name      = "iot-hotel-chain"
      namespace = "argocd"
      finalizers = [
        "resources-finalizer.argocd.argoproj.io"
      ]
      annotations = {
        "argocd-image-updater.argoproj.io/image-list"        = "command=dkitdevops/central-command:latest,app-frontend=dkitdevops/central-app-frontend:latest,hotel-kafka-to-mqtt=dkitdevops/hotel-kafka-to-mqtt:latest,hotel-mqtt-to-kafka=dkitdevops/hotel-mqtt-to-kafka:latest,temperature-sensor=dkitdevops/hotel-temperature-sensor:latest,light-actuator=dkitdevops/hotel-light-actuator:latest,alert-agent=dkitdevops/hotel-alert-agent:latest,booking-api=dkitdevops/booking_api:v1.0"
        "argocd-image-updater.argoproj.io/update-strategy"   = "digest"
        "argocd-image-updater.argoproj.io/write-back-method" = "argocd"
      }
    }
    spec = {
      project = "default"
      source = {
        repoURL        = "https://gitlab.comp.dkit.ie/D00271292/devops-project-gitops.git"
        targetRevision = "main"
        path           = "environments/prod"
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = "prod"
      }
      syncPolicy = {
        automated = {
          prune    = true
          selfHeal = true
        }
        syncOptions = [
          "CreateNamespace=true"
        ]
      }
    }
  }

  depends_on = [
    kubernetes_manifest.argocd_cluster_crds_app,
    helm_release.argocd
  ]
}

resource "kubernetes_secret" "argocd_image_updater" {
  metadata {
    name      = "argocd-image-updater-secret"
    namespace = "argocd"
  }

  data = {
    "argocd.token" = var.argocd_image_updater_token
  }

  type = "Opaque"
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
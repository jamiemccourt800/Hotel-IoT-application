terraform init
terraform plan -target=azurerm_kubernetes_cluster.k8s -var-file=dev.tfvars -out plan
terraform apply "plan"
terraform plan -var-file=dev.tfvars -out plan
terraform apply "plan"
terraform destroy -var-file=dev.tfvars 
terraform init
terraform plan -var-file=dev.tfvars -out plan
terraform apply "plan"
terraform destroy -var-file=dev.tfvars 
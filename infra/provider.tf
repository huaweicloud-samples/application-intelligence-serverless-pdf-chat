terraform {
  required_version = ">= 1.5.0"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "= 1.96.0"
    }
  }
}

# Credentials are read from the environment (HW_ACCESS_KEY / HW_SECRET_KEY /
# HW_REGION_NAME) and must NOT be hard-coded. See terraform.tfvars.example.
provider "huaweicloud" {
  region = var.region
}

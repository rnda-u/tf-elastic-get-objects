terraform {
  required_version = ">= 1.3.0"

  required_providers {
    elasticstack = {
      source  = "elastic/elasticstack"
      version = "~>0.11.14"
    }

    vault = {
      source  = "hashicorp/vault"
      version = "4.6.0"
    }
  }

}

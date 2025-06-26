variable "env_code" {
  type = string
}

variable "env_name" {
  type = string
}

variable "app_name" {
  type = string
}

variable "elasticsearch__api_key" {
  description = "API key to etablish connection with Elasticsearch"
  type        = string
  sensitive   = true
}

variable "kibana_cluster_id" {
  description = "API key to etablish connection with Elasticsearch"
  type        = string
  sensitive   = true
}


variable "elasticsearch_cluster_id" {
  description = "ID of the Elastic cluster"
  type        = string
  sensitive   = true
}

variable "list_of_indinces_patterns" {
  description = "Liste des patterns qui seront utilisés pour l'extration des informations sur les indices"
  type = list(string)
  default = [ "logs" ]
}
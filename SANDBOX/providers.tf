
provider "elasticstack" {
  elasticsearch {
    api_key   = var.elasticsearch__api_key
    endpoints = [var.elasticsearch_cluster_id]
    # Attention il faudra ituliser vault pour stocker la data 
  }
  kibana {
    endpoints = [var.kibana_cluster_id]
    api_key   = var.elasticsearch__api_key
    # Attention il faudra ituliser vault pour stocker la data 
  }
}
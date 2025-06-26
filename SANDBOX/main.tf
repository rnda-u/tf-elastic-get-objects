data "elasticstack_elasticsearch_indices" "elastic_indices" {
    for_each = { for idx, pattern in var.list_of_indinces_patterns : pattern => pattern }
    
    target = each.value
}


output "Elasticsearch_indices" {
  value = [
      for pattern in data.elasticstack_elasticsearch_indices.elastic_indices : {
        index_pattern = pattern.id 
        indexes = [ 
            for indice in pattern.indices :  {
                    index_name = indice.name
                    index_mode           =  try(jsondecode(indice.settings_raw)["index.mode"] , "N/A")
                    index_ilm                = try(jsondecode(indice.settings_raw)["index.lifecycle.name"] , "N/A")
                    index_creation_date  = try(jsondecode(indice.settings_raw)["index.creation_date"] , "N/A")

                    host_name_fieldsType =  try(jsondecode(indice.mappings).properties.host.properties.host.properties.build.type , "N/A")  
                }
            ]
      }
    ]
}
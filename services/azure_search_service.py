import requests
import json
from core.settings import Azure_Search_Index_Key ,Azure_Search_Index_version,Azure_Search_Index_Url

def search_azure_ai_index(shipping_mark: str,country_id:str,shipment_id:str=""):
    
    shipping_mark_cleaned:str = shipping_mark.replace("SO/", "")
    service_name:str = "aisearchshipmentcl"
    index_name:str="brasil-documents-index"
    url = f"https://{service_name}.search.windows.net/indexes/{index_name}/docs"    
 
    filter_conditions = [f"country_id eq '{country_id}'"]
    if shipment_id:
        filter_conditions.append(f"shipment_id eq '{shipment_id}'")

    params = {
        "api-version": Azure_Search_Index_version,
        "search": shipping_mark_cleaned,
        "$top": 7,
        "$filter": " and ".join(filter_conditions)
    }
    if shipment_id:
        params["$filter"] = f"country_id eq '{country_id}' and shipment_id eq '{shipment_id}'"

    headers = {
        "Content-Type": "application/json",
        "api-key": Azure_Search_Index_Key
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8"))
        
    else:
        raise Exception(f"Search failed: {response.status_code} - {response.text}")


def remove_empty_fields(data):
     
    if isinstance(data, dict):
        return {
            key: remove_empty_fields(value)
            for key, value in data.items()
            if value not in [None, "", []] and remove_empty_fields(value) != {}
        }
    elif isinstance(data, list):
        return [remove_empty_fields(item) for item in data if item not in [None, "", []]]
    else:
        return data

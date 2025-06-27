
import io
import json
import uuid
import time
from rq.job import Job
from typing import List,Tuple,Dict,Any
from schemas.general_dto import ResponseDocumentDto,UploadedFileDto
from schemas.general_enum import EmailType,APIAction
from core.load_json import get_json_schema
from services.cargologik_service import upload_document_by_shipment,update_shipment_cl
from services.gmail_service import gmail_send_reply_email_raw
from services.outlook_service import outlook_send_reply_email
from services.email_service import create_body_html_reponse_documents
from services.doc_process_business_rule import create_response_validate_requiered_documents
from services.open_ai_service import embed_text, push_documents_to_index_azure,generate_payload_update_shipment
from services.azure_search_service import search_azure_ai_index


def upload_documents(files:List[UploadedFileDto],shipment_id:str,email_type:str,token:str,message_id:str,list_documents: list[tuple[str, str, str, bool]],list_doc_response:list[Dict],shipment_id_uuid4:str,shipping_mark:str,country_id:str):
    list_files_unloaded: List[str] = []
    #upload documents
    for file in files:        
        result: ResponseDocumentDto = upload_document_by_shipment(file,shipment_id_uuid4)
        if not result.is_related:
            list_files_unloaded.append(file.file_name)
    #embed content
    vectorize_content(list_doc_response,shipment_id,shipping_mark,country_id,shipment_id_uuid4,token,message_id)                           
    reply_content:str = create_response_validate_requiered_documents(list_documents,list_doc_response,list_files_unloaded,shipment_id)                    
    #send reply
    if email_type == EmailType.microsoft:
        outlook_send_reply_email(token, reply_content, message_id,"") 
    if email_type == EmailType.google:
        gmail_send_reply_email_raw(token,message_id,reply_content)

def vectorize_content(list_doc_response:list[Dict],shipment_id:str,shipping_mark:str,country_id:str,shipment_id_uuid4:str,access_token: str, message_id: str):
    brasil_master = get_json_schema(APIAction.brasil_master)
    clean_vector: Dict={}
    for item in list_doc_response:
        clean_vector = {}
        new_item = map_json_to_master_schema(item,brasil_master)
        clean_vector.update(new_item)
        clean_vector = remove_empty_fields(clean_vector)
        flattened_text:str =  prepare_text_for_embedding(clean_vector)
        embeded_text = embed_text(flattened_text)
        clean_vector["embedding"] = embeded_text
        clean_vector["id"] = str(uuid.uuid4())
        clean_vector["shipment_id"] = shipment_id
        clean_vector["country_id"] = "BR"
        push_documents_to_index_azure(clean_vector)    
    update_shipment(shipping_mark,country_id,shipment_id,shipment_id_uuid4,access_token, message_id)

def remove_empty_fields(data: Dict[Any, Any]) -> Dict[Any, Any]:
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if clean(v) not in [None, "", {}, []]}
        elif isinstance(value, list):
            cleaned_list = [clean(v) for v in value if clean(v) not in [None, "", {}, []]]
            return cleaned_list if cleaned_list else None
        return value

    return {k: clean(v) for k, v in data.items() if clean(v) not in [None, "", {}, []]}


def extract_flat_fields(input_data: dict, brasil_master: dict) -> dict:
    doc_type = input_data.get("doc_type_code")
    doc_prefix = f"{doc_type}_"
    flat_source = input_data.get("all_fields", {})

    result = {}

    for key in brasil_master.get("properties", {}):
        if key.startswith(doc_prefix):
            field_key = key.replace(doc_prefix, "")
            if field_key in flat_source:
                result[key] = flat_source[field_key]

    return result

def map_json_to_master_schemav1(input_data: dict, brasil_master: dict) -> dict:
    output = {}

    # Get document type prefix
    doc_type = input_data.get("doc_type_code")  # e.g., "brasil_commercial_invoice"
    doc_prefix = f"{doc_type}_"

    # All fields are directly under all_fields now
    flat_source = input_data.get("all_fields", {})

    # Iterate over all schema properties and map matching keys
    for prop in brasil_master.get("properties", {}):
        if prop.startswith(doc_prefix):
            field_key = prop.replace(doc_prefix, "")
            if field_key in flat_source:
                output[prop] = flat_source[field_key] 
    return output


def format_array_field(field_name: str, value_list: list) -> str:
 
    formatted_items = []
    for i, item in enumerate(value_list):
        if isinstance(item, dict):
            parts = [f"{key}: {item[key]}" for key in item]
            formatted_items.append(f"item:{i + 1} - " + " - ".join(parts))
        else:
            # fallback if item is not a dict
            formatted_items.append(f"item:{i + 1} - {str(item)}")
    return " | ".join(formatted_items)


def map_json_to_master_schema(input_data: dict, brasil_master: dict) -> dict:
    output = {}

    # Get document type prefix (adjusted to use "doc_type_code" if available)
    doc_type = input_data.get("doc_type_code")
    doc_prefix = f"{doc_type}_"

    # All fields are under "all_fields"
    flat_source = input_data.get("all_fields", {})

    for prop in brasil_master.get("properties", {}):
        if prop.startswith(doc_prefix):
            field_key = prop.replace(doc_prefix, "")
            if field_key in flat_source:
                value = flat_source[field_key]

                # Detect and format arrays of dicts
                if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                    output[prop] = format_array_field(field_key, value)
                else:
                    output[prop] = value

    return output

def prepare_text_for_embedding(data: dict, max_chars: int = 8000) -> str:
    """Convert flat JSON dict into a clean, readable text block."""
    lines = []
    for key, value in data.items():
        if value is not None:
            # Normalize key and value
            key_text = key.replace("_", " ").strip()
            value_text = str(value).replace("\n", " ").strip()
            lines.append(f"{key_text}: {value_text}")
    text = "\n".join(lines)
    return text[:max_chars]


def update_shipment(shiping_mark: str,country_id:str,shipment_id:str,shipment_id_uuid4:str,access_token: str, message_id: str):
    result_search =  search_azure_ai_index(shiping_mark,country_id,shipment_id)
    search_cleaned = remove_empty_fields(result_search)
    update_shipmene_payload = generate_payload_update_shipment(search_cleaned)
    update_shipmene_payload["_id"] = shipment_id_uuid4
    update_shipment_cl(json.dumps(update_shipmene_payload),shipment_id,access_token,message_id)


def background_job(doc_id):
    print(f"startt document {doc_id}")
    time.sleep(10)
    print(f"Processed document {doc_id}")
    return f"Result for {doc_id}"


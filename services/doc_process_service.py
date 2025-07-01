import requests
import io
import json
from typing import Dict,Tuple,List,Any
from core.settings import Ocr_DocumentProcess_Key,Ocr_DocumentProcess_Url
from core.load_json import get_json_schema
from schemas.general_enum import APIAction,DocumentType
from  schemas.general_dto import CreateDocumentDto,UploadedFileDto
from services.gmail_service import get_gmail_attachment_bytes
from services.email_service import create_reponse_missing_documents,create_complete_reponse_documents
from services.doc_process_business_rule import get_isf_doc,validate_create_shipment
from services.cargologik_service import create_shipment 
from services.open_ai_service import call_openai,build_gpt_payload_shipment_cl
from mapper.brasil_isf_create_shipment import mapping_create_shipment
from services.background_tasks.handle_task_service import handle_upload_documents

def ocr_process_document(message_id:str,thread_Id:str,list_attachments:list[dict[str, str]],token:str,email_type:str,shipping_mark:str)->str:       
    list_documents = list_document_by_country(3)
    if len(list_attachments)==len(list_documents):
        list_result_docs:list[Dict] =[]
        isf_doc_json:dict = {}
        html_response = CreateDocumentDto()
        list_files_uploaded: List[UploadedFileDto] = []
        for attachment in list_attachments:
            attachmentId = attachment["attachmentId"]
            #is_isf_doc:bool = False            
            if not attachmentId :
                raise Exception(f"Unsupported file type")
            document_bytes = get_gmail_attachment_bytes(message_id, attachmentId, token)
            file_bytesIO = io.BytesIO(document_bytes)            
            ocr_document_result = call_ocr(str(attachment["filename"]),str(attachment["mimeType"]),file_bytesIO,3) # coyntru by default is 3 = Brasil                          
            #is_doc_shipping_mark:bool = check_shipping_mark(ocr_document_result,shipping_mark)
            is_doc_shipping_mark:bool = True
            if is_doc_shipping_mark:
                get_isf_doc(ocr_document_result,isf_doc_json)              
                list_result_docs.append(ocr_document_result)
                list_files_uploaded.append(UploadedFileDto(str(attachment["filename"]), document_bytes, str(attachment["mimeType"])))
        need_create_shipment = validate_create_shipment(list_documents,list_result_docs)
        if need_create_shipment==True:
            schema_create_shipment:dict = get_json_schema(APIAction.create_shipment)
            cl_create_shipment_payload:str = mapping_create_shipment(isf_doc_json,schema_create_shipment)
            html_response:CreateDocumentDto = create_shipment(cl_create_shipment_payload)
            handle_upload_documents(list_files_uploaded,html_response.shipment_id,email_type,token,message_id,list_documents,list_result_docs,html_response.shipment_id_uuid4,shipping_mark,"BR")
        else:
            html_response = CreateDocumentDto(create_reponse_missing_documents(len(list_documents),shipping_mark),"")
        return html_response.html
    else:
        return create_reponse_missing_documents(len(list_documents),shipping_mark)

def check_shipping_mark(ocr_document_result: dict[str, Any], shipping_mark: str) -> bool:
    doc_type = ocr_document_result.get("doc_type_code")

    # Direct match on shipping_mark for known doc types
    if doc_type in {
        DocumentType.brasil_certificate_of_analysis,
        DocumentType.brasil_certificate_of_origin,
        DocumentType.brasil_commercial_invoice,
        DocumentType.brasil_packing_list,
    }:
        return ocr_document_result["all_fields"]["shipping_mark"] == shipping_mark

    # Match on health certificate
    if doc_type == DocumentType.brasil_health_certificate:
        return ocr_document_result["all_fields"]["shipping_marks"] == shipping_mark

    # Match in marks_and_numbers within container_cargo_table
    if doc_type == DocumentType.brasil_master_bill_of_lading:
        container_data = ocr_document_result["all_fields"]["container_cargo_table"]

        # Parse if stringified JSON
        if isinstance(container_data, str):
            try:
                container_data = json.loads(container_data)
            except json.JSONDecodeError:
                return False

        if isinstance(container_data, list):
            return find_in_marks_and_numbers(container_data, shipping_mark)
    if doc_type == DocumentType.brasil_isf:
        return True
    
    return False
    

def find_in_marks_and_numbers(container_cargo_table: list[dict], value_to_find: str) -> bool:
    for item in container_cargo_table:
        if item.get("marks_and_numbers") and value_to_find in item["marks_and_numbers"]:
            return True
    return False

def  call_ocr(file_name:str,mime_type:str,file:io.BytesIO,country_id:int)-> Dict:
  
    new_file = [('file',(file_name,file,mime_type))]
    url = f"{Ocr_DocumentProcess_Url}ocr/upload?countryId={country_id}"
    headers = {
        'x-api-key': Ocr_DocumentProcess_Key
        } 
    response = None  
    try:
        response = requests.post(url, headers=headers, files=new_file, timeout=5000)
        if response.status_code == 200: 
            return json.loads(response.content.decode("utf-8")) 
        else:            
            raise Exception(f"HTTP {response.status_code} error in call_ocr: {response.text}")
    except Exception as e:
        import traceback
        traceback.print_exc()   
        raise Exception(f"FIleName: {file_name} Request failed: {e}\nStatus: {getattr(response, 'status_code', 'No status')}\nContent: {getattr(response, 'text', 'No text')}")
        

 

def  list_document_by_country(country_id:int) -> list[tuple[str, str, str, bool]]:
    try: 
        url = f"{Ocr_DocumentProcess_Url}document/list-documents?countryId={country_id}"
        headers = {
            'x-api-key': Ocr_DocumentProcess_Key
            }             
        response = requests.get(url, headers=headers)         
        if response.status_code == 200:
           
            return json.loads(response.content.decode("utf-8")) 
        else: 
            raise Exception(f"HTTP {response.status_code} error list_document_by_country: {response.text}")           
          
    except requests.RequestException as e:
        raise Exception(f"Request error while creating quote: {e}")

    except Exception as e:
        raise Exception(f"Unexpected error while creating quote: {e}")
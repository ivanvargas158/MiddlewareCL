import requests
import io
import json
from typing import Dict
from core.settings import Ocr_DocumentProcess_Key,Ocr_DocumentProcess_Url,Openai_Api_Key
from core.load_json import get_json_schema
from core.custom_exceptions import ValidationError
from schemas.general_enum import APIAction,DocumentType
from services.gmail_service import get_gmail_attachment_bytes
from services.email_service import create_reponse_missing_documents,create_complete_reponse_documents
from services.doc_process_business_rule import get_isf_doc,validate_requiered_documents
from services.cargologik_service import create_shipment 
from services.open_ai_service import call_openai,build_gpt_payload_shipment_cl
from services.jobs.background_job_service import upload_files
from mapper.brasil_isf_create_shipment import mapping_create_shipment

def ocr_process_document(message_id:str,thread_Id:str,list_attachments:list[dict[str, str]],token:str)->str:       
    list_documents = list_document_by_country(3)
    if len(list_attachments)==len(list_documents):
        list_result_docs:list[Dict] =[]
        isf_doc_json:dict = {}
        html_response:str=""
        for attachment in list_attachments:
            attachmentId = attachment["attachmentId"]
            #is_isf_doc:bool = False            
            if not attachmentId :
                raise ValidationError(errors=f"Unsupported file type")
            document_bytes = get_gmail_attachment_bytes(message_id, attachmentId, token)
            file_bytesIO = io.BytesIO(document_bytes)
            ocr_document_result = call_ocr(str(attachment["filename"]),str(attachment["mimeType"]),file_bytesIO,3) # coyntru by default is 3 = Brasil              
            get_isf_doc(ocr_document_result,isf_doc_json)  
            
            list_result_docs.append(ocr_document_result)  
            #print(attachmentId)           

        html_body_response_documents,need_create_shipment = validate_requiered_documents(list_documents,list_result_docs)

        if need_create_shipment==True:
            schema_create_shipment:dict = get_json_schema(APIAction.create_shipment)
            cl_create_shipment_payload:str = mapping_create_shipment(isf_doc_json,schema_create_shipment)
            html_response = create_shipment(cl_create_shipment_payload,html_body_response_documents)
            upload_files(1,2)
        else:
            html_response = create_complete_reponse_documents(html_body_response_documents)
        return html_response
    else:
        return create_reponse_missing_documents(len(list_documents))             

    


def  call_ocr(file_name:str,mime_type:str,file:io.BytesIO,country_id:int)-> Dict:
  
    new_file = [('file',(file_name,file,mime_type))]
    url = f"{Ocr_DocumentProcess_Url}ocr/upload?countryId={country_id}"
    headers = {
        'x-api-key': Ocr_DocumentProcess_Key
        }             
    response = requests.post(url, headers=headers, files=new_file,timeout=60)         
    if response.status_code == 200: 
        return json.loads(response.content.decode("utf-8")) 
    else:            
        raise ValidationError(f"HTTP {response.status_code} error in call_ocr: {response.text}")


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
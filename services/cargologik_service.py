import requests
import json
import io
from typing import Tuple,List
from schemas.general_dto import CreateDocumentDto,ResponseDocumentDto,UploadedFileDto
from core.settings import Cargologik_Url,Cargologik_Username,Cargologik_Password
from services.email_service import create_new_shipment_reponse,generate_update_shipment_html,create_complete_reponse_documents
from services.gmail_service import gmail_send_reply_email_raw

def create_token()->str:
    headers = {
        'Content-Type': 'application/json'
        }
    payload = json.dumps({
    "email": Cargologik_Username,
    "password": Cargologik_Password
    })
    response = requests.request("POST", f'{Cargologik_Url}users/login', headers=headers, data=payload)
    if response.status_code == 200:
        result = json.loads(response.content.decode("utf-8"))
        return result["data"]["token"]
    else:            
        return f"{response.status_code}:{ response.text}" 
    
def create_shipment(payload:str)->CreateDocumentDto:

    token:str = create_token()

    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
    }

    response = requests.request("POST", f'{Cargologik_Url}shipments/create', headers=headers, data=payload)
             
    if response.status_code == 200:
        return create_new_shipment_reponse(json.loads(response.content.decode("utf-8"))) 
    else:            
        return CreateDocumentDto(f"{response.status_code}:{ response.text}","") 
 


def upload_document_by_shipment(file:UploadedFileDto,shipment_id:str)->ResponseDocumentDto:

    token:str = create_token()
    payload = {}
    headers = {
    'Authorization': f'Bearer {token}'
    }

    new_file = [('files',(file.file_name, io.BytesIO(file.file_obj),file.mime_type))]
    response = requests.request("POST", f'{Cargologik_Url}upload', headers=headers, data=payload,files=new_file)
             
    if response.status_code == 200:
        response_upload = json.loads(response.content.decode("utf-8"))
        doc_uploaded = response_upload["data"]
        return create_document(doc_uploaded[0].get('_id'),doc_uploaded[0].get('url'),shipment_id,token) 
    else:            
        return ResponseDocumentDto(False,f"{response.status_code}:{ response.text}") 
 

def create_document(file_id:str,url:str,shipment_id:str,token:str)->ResponseDocumentDto:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
        }
    payload=json.dumps({
        "url": url,
        "file": file_id,
        "category": "shipment",
        "isPublic": "1",
        "shipment": shipment_id,
        "teamPermisions": []
    })
    response = requests.request("POST", f'{Cargologik_Url}document/create', headers=headers, data=payload)
                
    if response.status_code == 200:
        return ResponseDocumentDto(True,"Document Assignment Successfully")
    else:
        return ResponseDocumentDto(False,f"{response.status_code}:{ response.text}") 
    



def update_shipment_cl(payload:str,shipment_id:str,access_token: str, message_id: str):

    token:str = create_token()

    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
    }

    response = requests.request("PUT", f'{Cargologik_Url}shipments/update', headers=headers, data=payload)
    shipment_updated:str=""         
    if response.status_code == 200:
        shipment_updated = generate_update_shipment_html(json.loads(payload),shipment_id)
        reply_content = create_complete_reponse_documents(shipment_updated)
        gmail_send_reply_email_raw(access_token,message_id,reply_content.html)       
    else:
        shipment_updated = f"The shipment {shipment_id} was not update."
        reply_content = create_complete_reponse_documents(shipment_updated)
        gmail_send_reply_email_raw(access_token,message_id,reply_content.html)
 
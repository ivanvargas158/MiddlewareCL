import requests
import json

from pathlib import Path
from typing import Any
from core.settings import Cargologik_Url,Cargologik_Username,Cargologik_Password
from core.load_html import get_html
from utils.global_resources import generate_greetings
from schemas.general_enum import APICargologik_html   
from services.email_service import create_new_shipment_reponse

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
    
def create_shipment(payload:str,html_body_response_documents:str)->str:

    token:str = create_token()

    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
    }

    response = requests.request("POST", f'{Cargologik_Url}shipments/create', headers=headers, data=payload)
             
    if response.status_code == 200:
        return create_new_shipment_reponse(json.loads(response.content.decode("utf-8")),html_body_response_documents) 
    else:            
        return f"{response.status_code}:{ response.text}" 
 



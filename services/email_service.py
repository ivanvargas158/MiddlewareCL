import psycopg2
import re
from typing import Any , Tuple
from core.settings import DB_Host, DB_Name, DB_pwd, DB_User,Gpt_Trainer_Beaer_Key_Category_Classify,Gpt_UUID_Category_Classify
from core.load_html import get_html
from services.chat_gpt_service import create_request 
from typing import List
from schemas.email_category_classification_enum import HumanMessageCategory
from schemas.general_enum import APICargologik_html
from services.postgresql_db import update_last_human_email_category_content
from datetime import datetime, timezone, timedelta 
from services.gmail_service import *
from utils.global_resources import generate_greetings
from services.jobs.background_job_service import upload_files
def ensure_valid_token(email_address: str) -> tuple[str, str,str, str,str,str]:
    try:     
        with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
            with conn.cursor() as cursor:   
                cursor.execute(
                    """
                        SELECT access_token, refresh_token, token_expires,folder_id,folder_spam_id,folder_internal_email_id,email_type
                        FROM email_controller_emailcredentials
                        WHERE email = %s
                    """,
                    (email_address,),
                )
                result = cursor.fetchone()
 
                if result is None:
                    raise Exception("Email credentials not found.")                         
                
                access_token, refresh_token, token_expires,folder_id,folder_spam_id,folder_internal_email_id,email_type = result                             

                # Ensure token_expires is a datetime object
                if isinstance(token_expires, str):
                    token_expires = datetime.fromisoformat(token_expires)
                
                # Check if the token is about to expire in less than 10 minutes
                if token_expires - timedelta(minutes=10) < datetime.now(tz=timezone.utc):
                    new_access_token, new_refresh_token = '',''
                    new_access_token, new_refresh_token  = generate_gmail_access_refresh_token(refresh_token,email_address)
                    #new_access_token, new_refresh_token = generate_outlook_access_refresh_token(refresh_token, email_address)
                    access_token = new_access_token
                    refresh_token = new_refresh_token 

                if folder_id is None:
                    folder_id = gmail_check_if_label_exists(access_token,Outlook_Folder_to_Move_Email)
                    if(not folder_id or folder_id==''):
                        folder_id = gmail_create_label(access_token,email_address,Outlook_Folder_to_Move_Email)
                    else:
                        update_folder_id(folder_id,email_address,Outlook_Folder_to_Move_Email)
                
                if folder_spam_id is None:
                    folder_spam_id = gmail_check_if_label_exists(access_token,Outlook_Folder_to_Move_Spam_Email)
                    if(not folder_spam_id or folder_spam_id==''):
                        folder_spam_id = gmail_create_label(access_token,email_address,Outlook_Folder_to_Move_Spam_Email)
                    else:
                        update_folder_id(folder_spam_id,email_address,Outlook_Folder_to_Move_Spam_Email)

                # if folder_internal_email_id is None:
                #     folder_internal_email_id = outlook_check_if_exists_processedfolder(access_token,Outlook_Folder_to_Move_Internal_Emails)
                #     if(not folder_internal_email_id or folder_internal_email_id==''):
                #         folder_internal_email_id = outlook_create_folder(access_token,email_address,Outlook_Folder_to_Move_Internal_Emails)
                #     else:
                #         update_folder_id(folder_internal_email_id,email_address,Outlook_Folder_to_Move_Internal_Emails)
                upload_files(1,2)
                return access_token, refresh_token,folder_id,folder_spam_id,folder_internal_email_id,email_type
    except Exception as e:
        raise Exception(f"Error ensuring valid token: {str(e)}")




def email_category_classification(email_content: str, email_attachment: str, message_id: str):
   
    current_customer_message:str = ''
    if email_content:
        current_customer_message = email_content.replace('**Customer:**','')
    # Include attachment in the current message if present
    if email_attachment:
        current_customer_message += "\n" + email_attachment
    try:
        #current_customer_message = reduce_tokens_email(current_customer_message)            
        gtp_response_category = create_request(current_customer_message,Gpt_Trainer_Beaer_Key_Category_Classify,Gpt_UUID_Category_Classify)
        category = ''
        list_category = extract_categories(gtp_response_category)
        if len(list_category)>1:
            category = HumanMessageCategory.COMBINE_REQUEST.value
        else:
            category = list_category[0]
        if message_id:
            update_last_human_email_category_content(last_category=category, last_content=current_customer_message or "", message_id=message_id) 
    except Exception as excep:   
       raise Exception(f'{excep} / Category: {gtp_response_category}')
    return category,current_customer_message

def extract_categories(content: str) -> List[str]:
    list_category = []
    categories = [category.value for category in HumanMessageCategory]
    for item in categories:
        if item in content:
            list_category.append(item)
    return list_category



def create_new_shipment_reponse(content_response:dict,html_body_response_documents:str)->str:

    data = content_response.get("data", {})
    shipment_id = data.get("shipmentId", "Shipment Details")

    def render_value(value: Any) -> str:
        if isinstance(value, dict):
            return "<br>".join(
                f"<strong>{k}:</strong> {render_value(v)}"
                for k, v in value.items()
                if not is_uuid_like(v) and not k.startswith("_")
            )
        elif isinstance(value, list):
            return "<br>".join(render_value(v) for v in value if not is_uuid_like(v))
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif is_uuid_like(value):
            return ""  # Exclude UUID-like values
        else:
            return str(value) if value not in [None, ""] else "—"

    html_body_create_shipment:str = f"""<div class="title">Shipment ID: {shipment_id}</div><table><tr><th>Field</th><th>Value</th></tr>"""



    for key, value in content_response.items():
        if key in ["status", "_id"] or is_uuid_like(value):
            continue

        pretty_key = key.replace('_', ' ').capitalize()
        rendered_value = render_value(value)

        if rendered_value.strip():  # skip empty
            html_body_create_shipment += f"<tr><td class='label'>{pretty_key}</td><td>{rendered_value}</td></tr>"
    html_body_create_shipment += """</table>"""    

    html_body_create_shipment += html_body_response_documents

    greeting = generate_greetings()

    template_new_shipment = get_html(APICargologik_html.create_shipment)
    
    html =  template_new_shipment.replace("{greetting}",greeting)
    html = html.replace("{data_shipment}",html_body_create_shipment)
    return html

def is_uuid_like(value: Any) -> bool:   
    return isinstance(value, str) and re.fullmatch(r"[a-f\d]{24}", value) is not None


def create_reponse_missing_documents(count_docs:int)->str:
    return f"Dear user, there must be at least {count_docs} attached documents to continue the process."




def create_complete_reponse_documents(body_html_response:str)->str:

    
    greeting = generate_greetings()

    template_shipment = get_html(APICargologik_html.create_shipment)

    html_content:str =  template_shipment.replace("{greetting}",greeting)

    html_content =  html_content.replace("{data_shipment}",body_html_response)

    return html_content

def create_body_html_reponse_documents(
    response: List[Tuple[str, str, str]],
    missing_doc_types: List[Tuple[str, str]] = []
) -> str:
    table_rows = ""


    for doc_type, doc_type_code, file_name in response:
            is_missing = doc_type in missing_doc_types
            row_style:str = ' style="background-color: #FFD6D6;"' if is_missing else ""
            processed_info:str = "unprocessed" if row_style else "processed"
            table_rows += f"""
            <tr{row_style}>
                <td>{doc_type}</td>
                <td>{file_name}</td>
                <td>{processed_info}</td>
            </tr>
            """
 

    html_body_documents:str = f"""
       <div class="title">Document List Status</div>
            <table>
                <thead>
                    <tr>
                        <th>Document Type</th>
                        <th>File Name</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            <p style="color: #C62828;"><strong>Red rows indicate missing or invalid documents.</strong></p>
        </div>
            """  
    return html_body_documents

 



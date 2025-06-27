import psycopg2
import re
from typing import Any , Tuple
from core.settings import DB_Host, DB_Name, DB_pwd, DB_User,Gpt_Trainer_Beaer_Key_Category_Classify,Gpt_UUID_Category_Classify
from core.load_html import get_html
from services.chat_gpt_service import create_request 
from typing import List
from schemas.email_category_classification_enum import HumanMessageCategory
from schemas.general_enum import APICargologik_html
from schemas.general_dto import ProcessedDoc
from schemas.general_dto import CreateDocumentDto
from services.postgresql_db import update_last_human_email_category_content
from datetime import datetime, timezone, timedelta 
from services.gmail_service import *
from utils.global_resources import generate_greetings
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
                    folder_id = gmail_check_if_label_exists(access_token,Outlook_Folder_to_Move_Email_CL)
                    if(not folder_id or folder_id==''):
                        folder_id = gmail_create_label(access_token,email_address,Outlook_Folder_to_Move_Email_CL)
                    else:
                        update_folder_id(folder_id,email_address,Outlook_Folder_to_Move_Email_CL)
                
                # if folder_spam_id is None:
                #     folder_spam_id = gmail_check_if_label_exists(access_token,Outlook_Folder_to_Move_Spam_Email)
                #     if(not folder_spam_id or folder_spam_id==''):
                #         folder_spam_id = gmail_create_label(access_token,email_address,Outlook_Folder_to_Move_Spam_Email)
                #     else:
                #         update_folder_id(folder_spam_id,email_address,Outlook_Folder_to_Move_Spam_Email)

                if folder_internal_email_id is None:
                    folder_internal_email_id = gmail_check_if_label_exists(access_token,Outlook_Folder_to_Move_Email_Unprocessed_CL)
                    if(not folder_internal_email_id or folder_internal_email_id==''):
                        folder_internal_email_id = gmail_create_label(access_token,email_address,Outlook_Folder_to_Move_Email_Unprocessed_CL)
                    else:
                        update_folder_id(folder_id,email_address,Outlook_Folder_to_Move_Email_Unprocessed_CL)
 
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



def create_new_shipment_reponse(content_response:dict)->CreateDocumentDto:

    data = content_response.get("data", {})
    shipment_id = data.get("shipmentId", "")
    shipment_id_uuid4 = data.get("_id", "")
    result: Tuple[str,str]

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

    greeting = generate_greetings()

    template_new_shipment = get_html(APICargologik_html.create_shipment)
    
    html =  template_new_shipment.replace("{greetting}",greeting)
    html = html.replace("{data_shipment}",html_body_create_shipment)
    return CreateDocumentDto(html,shipment_id,shipment_id_uuid4)

def is_uuid_like(value: Any) -> bool:   
    return isinstance(value, str) and re.fullmatch(r"[a-f\d]{24}", value) is not None


def create_reponse_missing_documents(count_docs:int,shipping_mark:str)->str:

    message:str = f"To proceed with the process, you must attach at least {count_docs} documents.</br>The registered shipping mark is {shipping_mark}. Please verify that the attached documents match this shipping mark."
    response:CreateDocumentDto = create_complete_reponse_documents(message)
    return response.html
    
def create_complete_reponse_documents(body_html_response:str)->CreateDocumentDto:
    
    greeting = generate_greetings()

    template_shipment = get_html(APICargologik_html.create_shipment)

    html_content:str =  template_shipment.replace("{greetting}",greeting)

    html_content =  html_content.replace("{data_shipment}",body_html_response)

    return CreateDocumentDto(html_content,"")

def create_body_html_reponse_documents(
    list_docs: List[ProcessedDoc],
    missing_doc_types: List[str] = [],shipment_id:str=""
) -> str:
    table_rows = ""


    for item in list_docs:
            is_missing = item.doc_type_code in missing_doc_types
            row_style:str = ' style="background-color: #FFD6D6;"' if is_missing else ""            
            table_rows += f"""
            <tr{row_style}>
                <td>{item.doc_type}</td>
                <td>{item.file_name}</td>
                <td>{item.message}</td>
            </tr>
            """
 

    html_body_documents:str = f"""
       <div class="title">Shipment ID: {shipment_id}   - Document List Status </div>
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

 
def generate_update_shipment_html(shipment: dict,shipment_id:str) -> str:
    def is_valid(value):
        return value not in (None, "", [], {})

    def render_row(label, value):
        return f"<tr><td class='label'>{label}</td><td>{value}</td></tr>"

    html = f"""    
        <div class="title">Update Shipment Info {shipment_id}</div>
    """

    # Flat fields
    general_fields = [
        ("_id", shipment.get("_id")),
        ("Reference Name", shipment.get("referenceName")),
        ("Internal Reference", shipment.get("internalReference")),
        ("Notes", shipment.get("notes")),
        ("ETA", shipment.get("eta")),
        ("ETD", shipment.get("etd")),
        ("Pickup Date", shipment.get("pickupDate")),
        ("Delivery Address", shipment.get("deliveryAddress")),
        ("Payment Terms", shipment.get("paymentTerms")),
        ("Config Tracking", shipment.get("configTracking")),
        ("Total Weight", shipment.get("totalWeight")),
        ("Total Volume", shipment.get("totalVolume")),
    ]
    rows = [render_row(label, value) for label, value in general_fields if is_valid(value)]
    if rows:
        html += "<table><tr><th colspan='2'>General Information</th></tr>" + "".join(rows) + "</table>"

    # packagesInfo
    packages = shipment.get("packagesInfo") or []
    if is_valid(packages):
        html += "<table><tr><th colspan='2'>Packages Info</th></tr>"
        for i, p in enumerate(packages):
            html += f"<tr><td class='label'>Package #{i+1}</td><td><ul>"
            for key, val in p.items():
                if is_valid(val):
                    html += f"<li><strong>{key}</strong>: {val}</li>"
            html += "</ul></td></tr>"
        html += "</table>"

    # Carrier
    carrier = shipment.get("carrier")
    if isinstance(carrier, dict):
        if is_valid(carrier):
            rows = []
            if is_valid(carrier.get("name")):
                rows.append(render_row("Name", carrier["name"]))
            if is_valid(carrier.get("scac")):
                rows.append(render_row("SCAC", ", ".join(carrier["scac"])))
            if rows:
                html += "<table><tr><th colspan='2'>Carrier</th></tr>" + "".join(rows) + "</table>"

    # Shipper
    shipper = shipment.get("shipper")
    if isinstance(shipper, dict):
        if is_valid(shipper):
            rows = []
            for label in ["name", "email", "address"]:
                if is_valid(shipper.get(label)):
                    rows.append(render_row(label.capitalize(), shipper[label]))
            if rows:
                html += "<table><tr><th colspan='2'>Shipper</th></tr>" + "".join(rows) + "</table>"

    # Consignee
    consignee = shipment.get("consignee")
    if isinstance(consignee, dict):
        if is_valid(consignee):
            rows = []
            for label in ["name", "email", "address"]:
                if is_valid(consignee.get(label)):
                    rows.append(render_row(label.capitalize(), consignee[label]))
            if rows:
                html += "<table><tr><th colspan='2'>Consignee</th></tr>" + "".join(rows) + "</table>"

    html += "</body></html>"
    return html

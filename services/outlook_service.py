import logging
import requests
import psycopg2
from datetime import datetime, timezone, timedelta
import json
import base64
from utils.email_utils import filter_emails_from_agents,add_final_text
from core.settings import *
from services.gmail_service import *
from services.postgresql_db import get_internal_emails,get_last_conversation
from schemas.email_category_classification_enum import HumanMessageCategory,target_categories
from utils.global_resources import generate_greetings,replace_newline,get_first_key_by_value,clean_response,get_id_by_display_name


with open(f'{Path.cwd()}/schemas/html/rate_email_reply.html', encoding="utf-8") as file:
    rate_email_reply =file.read()

with open(f'{Path.cwd()}/schemas/html/combine_email_reply.html', encoding="utf-8") as file:
    combine_rate_email_reply =file.read() 


def fetch_outlook_new_emails(email_address: str, access_token: str, folder_spam_id:str, folder_internal_email_id:str,fetch_limit: int = 10) -> list:
    if not access_token:
        logging.error('Access Token is not valid')
        return []
    
    msapi_url_endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$filter=isRead eq false&$top={fetch_limit}"
    msapi_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    msapi_response = requests.get(url=msapi_url_endpoint, headers=msapi_headers)

    if msapi_response.status_code != 200:
        raise Exception(f'Fetch new emails MS Graph API is not working {str(msapi_response.content)}') 
    else:
        list_internal_emails = get_internal_emails()
        emails = msapi_response.json().get("value", [])
        parse_emails = []
        exists_document:bool = False
        for i, email in enumerate(emails):
            message_id = email.get('id') #actual email received
            conversation_Id = email.get('conversationId') #actual conversation
            email_from = email.get('from').get('emailAddress').get('address')
            result_internal_email = next((item for item in list_internal_emails if item[0].lower() == email_from), None)
            if result_internal_email: 
                outlook_move_email(access_token,message_id,folder_internal_email_id,'','')
            elif email.get('subject') in Filter_Spam_Emails:
                create_outlook_label(access_token,HumanMessageCategory.SPAM.value,message_id)        
                outlook_move_email(access_token,message_id,'',HumanMessageCategory.SPAM.value,folder_spam_id)
            else:
                list_thread_emails = fetch_thread_emails_outlook(thread_id=conversation_Id, access_token=access_token)
                list_thread_emails = filter_emails_from_agents(list_thread_emails,Agent_Emails)
                full_conversation = []
                last_conversation_datetime_str = get_last_conversation(conversation_Id)

                for thread_email in list_thread_emails:
                    add_text = True
                    exists_document = False
                    if last_conversation_datetime_str:
                        receivedDateTime = datetime.strptime(thread_email.get('receivedDateTime'), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        last_conversation_datetime:datetime = datetime.strptime(last_conversation_datetime_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        add_text = receivedDateTime > last_conversation_datetime
                    if add_text == True:                        
                        email_html_content = thread_email.get("body", {}).get("content", "")
                        parsed_email_body = add_final_text(email_html_content)
                        if parsed_email_body != '':                            
                            full_conversation.append(parsed_email_body)      
                # Combine all conversation parts
                full_conversation_text = "\n---\n".join(full_conversation)
                # parsed_email_body = extract_conversation_from_email_body(html_content=email_html_content)
                is_attachment = email.get('hasAttachments')
                email_html_content=''
                email_attachment_text=''
                if list_thread_emails:
                    email_html_content  = list_thread_emails[-1].get("body", {}).get("content", "")
                    #email_attachment_text,exists_document = parse_email_image_attachment(message_id=message_id, email_html_content=email_html_content, access_token=access_token, is_attachment=is_attachment)
                
            
                if full_conversation_text == '' and email_attachment_text == '':
                    create_outlook_label(access_token,HumanMessageCategory.SPAM.value,message_id)        
                    outlook_move_email(access_token,message_id,'',HumanMessageCategory.SPAM.value,folder_spam_id)
                elif exists_document==True:
                    create_outlook_label(access_token,HumanMessageCategory.HI_COMPLEX_REQUEST.value,message_id) 
                    outlook_mark_email_as_read(access_token,message_id)
                else:
                    if full_conversation_text:
                        full_conversation_text = f"{full_conversation_text}\n sender: {email_from}"
                    if email_attachment_text:
                        email_attachment_text = f"{email_attachment_text}\n sender: {email_from}"
                    parse_email = {
                        "message_id": message_id,
                        "conversation_Id": conversation_Id,
                        "body": full_conversation_text,
                        "attachment_text": email_attachment_text,
                        "subject":email.get('subject')
                    }
                    parse_emails.append(parse_email)
                
        return parse_emails



    
def generate_outlook_access_refresh_token(refresh_token: str, email_address: str) -> tuple[str, str]:

    msapi_token_endpoint = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

    payload = {
        "client_id": Azure_Cliente_Id,
        "client_secret": Azure_Cliente_Secret,
        "scope": Outlook_Business_Refresh_Token_Scopes if email_address in Agent_Emails else Outlook_Personal_Refresh_Token_Scopes,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "tenant": "common",
    }

    msapi_token_response = requests.post(msapi_token_endpoint, data=payload)

    if msapi_token_response.status_code != 200:
        raise Exception(f'Failed to generate refresh outlook access token, {str(msapi_token_response.content)}')
    
    token_data = msapi_token_response.json()

    if "error" in token_data:
        raise Exception(f'Failed to generate refresh outlook access token, {str(msapi_token_response.content)}')
    
    try:
        new_access_token = token_data['access_token']
        new_refresh_token = token_data['refresh_token']
        new_expires_in:str = get_expire_date(token_data['expires_in'])
    except Exception as e:
        raise Exception(f'Failed to extract new access and refresh token, {str(e)}')
    try:
        with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                        UPDATE email_controller_emailcredentials
                        SET access_token = %s, refresh_token = %s, token_expires = %s
                        WHERE email = %s
                    """,
                    (new_access_token, new_refresh_token, new_expires_in, email_address),
                )
                conn.commit()
        return new_access_token, new_refresh_token
    except Exception as e:
        raise Exception(f'Update Email Credential Failed, {str(e)}')
  
def create_outlook_label(access_token: str, category_label: str, message_id: str):
    try:
        if category_label:
            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            categories_list = [cat.strip() for cat in category_label.split(',') if cat.strip()!='' and cat.strip() != HumanMessageCategory.COMBINE_REQUEST.value]
            if len(categories_list)>=1:
                payload = {"categories": categories_list}
                response = requests.patch(url, headers=headers, json=payload)
                if not response.status_code in [200, 201]:                
                    raise Exception(f"Failed create_outlook_label. Status code: {response.status_code}")                
    except Exception as e:
        raise Exception(f"Failed create_outlook_label: {str(e)}")

def outlook_send_reply_email(access_token: str, reply_content: str, message_id: str, source:str):
    #url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/replyAll" #Use replyAll,to reply directly to end user 
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/createReply"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    if source not in {"quote", "error_quote"}:
        if reply_content:
            reply_content = reply_content.replace("*", "")
            formatted_reply_content = str(reply_content).replace("\n", "<br>")
            formatted_reply_content = str(formatted_reply_content).replace("<br><br><br>", "<br><br>")

            html_content = f"""
                <html>
                    <body>
                        <div style="font-family: Arial, sans-serif; color: #333;">
                            <div dir="ltr">

                                <div style="display: none">*****Service Message*****</div>
                                <p style="font-size: 14px;">{formatted_reply_content}</p>
                            </div>
                            <br>
                        </div>

                    </body>
                </html>
            """
            body = {
                "comment": html_content,
            }
            response = requests.post(url, headers=headers, json=body)
            if response.status_code != 202 and response.status_code != 201 and response.status_code == 200:
                raise Exception(f'Error outlook_send_reply_email: {response.status_code} / {response.text}')
        
    else:
        if reply_content:
            greeting = generate_greetings()
            reply_content = replace_newline(reply_content)

            html_content =  rate_email_reply.replace("{greetting}",greeting)
            html_content = html_content.replace("{formatted_reply_content}", reply_content)     

            body = {
                "comment": html_content,
            }

            response = requests.post(url, headers=headers, json=body)        
            if response.status_code != 202 and response.status_code != 201 and response.status_code == 200:
                raise Exception(f'Error outlook_send_reply_email: {response.status_code}/{response.text}')   
    
    
def outlook_send_reply_email_combine(access_token: str, reply_content: str, message_id: str):
    #url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/replyAll" #Use replyAll,to reply directly to end user 
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/createReply"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    result:bool = True
    
    greeting = generate_greetings()
 

    html_content =  combine_rate_email_reply.replace("{greetting}",f'<p>{greeting}</p></br>')

    contentGeneralInquiry =  get_first_key_by_value(reply_content,'General Inquiry')
    if contentGeneralInquiry is None:        
        html_content =  html_content.replace("{General Inquiry}",'')
    else:
        html_content =  html_content.replace("{General Inquiry}",clean_response(contentGeneralInquiry))  

    contentTrackingRequest=  get_first_key_by_value(reply_content,'Tracking Request')
    if contentTrackingRequest is None:        
        html_content =  html_content.replace("{Tracking Request}",'')
    else:
        html_content =  html_content.replace("{Tracking Request}",clean_response(contentTrackingRequest))    

    contentQuoteRequest =  get_first_key_by_value(reply_content,'Quote Request')
    if contentQuoteRequest is None:        
        html_content =  html_content.replace("{Quote Request}",'')
    else:
        html_content =  html_content.replace("{Quote Request}",clean_response(contentQuoteRequest))

 
    body = {
        "comment": html_content,
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 202 or response.status_code == 201 or response.status_code == 200:
        result = True
    else:
        result = False
        
    return result



def outlook_send_email(access_token: str, subject: str, body: str, original_email_address: str, target_email_address: str, session_uuid: str, attachment_path: str = "sample-invoice.pdf"):
        
    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }  
    
    html_content = f"""
        <html>
            <body>
                <div style="font-family: Arial, sans-serif; color: #333;">
                    <div dir="ltr">

                        <div style="display: none">*****Service Message*****</div>
                        <div style="display: none">*****Session UUID: {session_uuid}*****</div>

                        <p style="font-size: 14px;">{body}</p>
                    </div>
                    <br>
                </div>

            </body>
        </html>
    """
    # Define the email content
    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "html",
                "content": html_content
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": target_email_address
                    }
                }
            ]
        }
    }

    if attachment_path:
        try:
            with open(attachment_path, "rb") as file:
                file_content = file.read()
                encoded_file_content = base64.b64encode(file_content).decode("utf-8")
            
            email_data["message"]["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": "sample.pdf",  # Name of the attachment file
                    "contentBytes": encoded_file_content
                }
            ]
        except Exception as e:
            logging.error(f"Failed to read attachment file: {e}")
            return False

    # Send the email
    response = requests.post(url, headers=headers, json=email_data)
    
    if response.status_code == 202 or response.status_code == 201 or response.status_code == 200:
        logging.info("Email sent successfully!")
        return True
    else:
        logging.error(f"Failed to send email. Status Code: {response.status_code}")
        logging.error(response.json())
        return False
   
def outlook_move_email(access_token: str, message_id: str,folder_id:str,target_category:str,folder_spam_id:str):
    try:
        #Rules to move the email 
        folder_to_move:str = ''
        if target_category in target_categories:
            outlook_mark_email_as_read(access_token,message_id)
        else:
            if HumanMessageCategory.SPAM.value==target_category:
                folder_to_move = folder_spam_id
            else:
                folder_to_move = folder_id
            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/move"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            data = {"destinationId":folder_to_move}        
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 202 and response.status_code != 201 and response.status_code != 200:             
                raise  Exception(f"Failed to moving the email. Status Code:  {response.status_code}")       

    except requests.RequestException as e: 
        error_content  = e.response.content.decode('utf-8') if e.response and e.response.content else "No response content"
        raise Exception(f"Error Response content  moving to Folder: {error_content}")

    except Exception as e: 
        raise Exception(f"Unexpected error moving to Folder {access_token}: {type(e).__name__}: {e}")

 


def outlook_check_if_exists_processedfolder(access_token: str,folder:str ): 
    try:    
        url = f"https://graph.microsoft.com/v1.0/me/mailFolders"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 202 or response.status_code == 201 or response.status_code == 200:
            contentJson =  json.loads(response.content.decode("utf-8"));           
            folder_id = get_id_by_display_name(contentJson,folder)
            return folder_id
        else:
            raise  Exception(f"Failed checking if exists Folder:  {response.status_code}")
    except requests.RequestException as e: 
        error_content  = e.response.content.decode('utf-8') if e.response and e.response.content else "No response content"
        raise Exception(f"Error Response content checking if exists Folder: {error_content}")
    except Exception as e: 
        raise Exception(f"Unexpected error, checking if exists Folder  {access_token}: {type(e).__name__}: {e}")
 
def find_all_display_names(data):
    if "value" in data and isinstance(data["value"], list):
        return [folder["displayName"] for folder in data["value"] if "displayName" in folder]
    return []



def outlook_create_folder(access_token: str,  email_address: str,folder:str):
    try: 

        url = f"https://graph.microsoft.com/v1.0/me/mailFolders"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        data = {"displayName":folder}    
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 202 or response.status_code == 201 or response.status_code == 200:
            responseContent = json.loads(response.content)
            folder_id = responseContent["id"]           
            update_folder_id(folder_id,email_address,folder)
            return folder_id
        else:
            raise  Exception(f"Failed creating a new folder: {response.status_code} / {response.text}")
    except requests.RequestException as e:
        error_content  = e.response.content.decode('utf-8') if e.response and e.response.content else "No response content"
        raise Exception(f"Error Response content creating a new folder: {error_content}")

    except Exception as e: 
        raise Exception(f"Unexpected error while creating a new folder  {access_token}: {type(e).__name__}: {e}")
    


def outlook_mark_email_as_read(access_token: str, message_id: str):
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {"isRead": True}

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        return True
    else:
        return False
    
def outlook_mark_red_flag(access_token: str, message_id: str):
    try:
        # Construct the URL to update the email's flag status
        flag_url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        flag_data = {"flag": {"flagStatus": "flagged"}}

        # Send the PATCH request to mark the email as flagged
        response = requests.patch(flag_url, headers=headers, json=flag_data)

        response.raise_for_status()  # Raise an exception for HTTP error responses
        return True
    except requests.RequestException as e:        
        return False
    except Exception as e:
        return False
    


def fetch_thread_emails_outlook(thread_id: str, access_token: str) -> list:
    """
    Fetch all emails in a thread using thread_id.
    """
    msapi_url_endpoint = f"https://graph.microsoft.com/v1.0/me/messages?$filter=conversationId eq '{thread_id}'&top=60"
    msapi_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    msapi_response = requests.get(url=msapi_url_endpoint, headers=msapi_headers)
    
    if msapi_response.status_code != 200:
        logging.error(f'Fetch thread emails MS Graph API is not working {str(msapi_response.content)}')
        return []
    else:
        return msapi_response.json().get("value", [])
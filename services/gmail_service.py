import requests
import psycopg2
import base64
import logging
from datetime import datetime, timezone, timedelta
from core.settings import *
from utils.global_resources import get_expire_date,is_valid_shipping_mark,extract_shipping_mark
from services.postgresql_db import update_folder_id,get_last_conversation
from utils.email_utils import add_final_text
from email.mime.text import MIMEText

def fetch_gmail_new_emails(access_token: str,folder_internal_email_id:str,fetch_limit: int = 1) -> list:
    #folder_internal_email_id = UnprocessedCL
    #folder_internal_email_id = UnprocessedCL
    if not access_token:
        logging.error('Access token is not valid')
        return []

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    # Step 1: List unread message IDs
    list_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread+label:inbox&maxResults={fetch_limit}"
    list_response = requests.get(list_url, headers=headers)

    if list_response.status_code != 200:
        raise Exception(f'Fetch new emails MS Graph API is not working {str(list_response.content)}') 
    else:
        message_items = list_response.json().get("messages", [])
        parse_emails = []
        exists_document:bool = False
        list_attachmentId:list[dict] = []
        for msg in message_items:        
            message_id = msg.get("id")
            thread_Id =  msg.get("threadId")
            if not message_id:
                continue
            
            list_attachmentId = []
            message_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}?format=full"
            msg_response = requests.get(message_url, headers=headers)

            if msg_response.status_code == 200:
                full_message = msg_response.json()
                headers_list = full_message.get("payload", {}).get("headers", [])
                payload = full_message.get("payload", {})

                subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "")
                sender = next((h["value"] for h in headers_list if h["name"] == "From"), "")
                #body = extract_gmail_message_body(payload)

                #message_id = email.get('id') #actual email received
                #conversation_Id = email.get('conversationId') #actual conversation
                email_from = sender
                if not is_valid_shipping_mark(subject):
                    #gmail_create_label(access_token,HumanMessageCategory.SPAM.value,message_id)        
                    gmail_move_email(access_token,message_id,folder_internal_email_id)
                else:
                    shipping_mark:str = extract_shipping_mark(subject)
                    list_thread_emails = fetch_thread_emails_gmail(thread_id=thread_Id, access_token=access_token)
                    full_conversation = []
                    last_conversation_datetime_str = get_last_conversation(thread_Id)

                    for thread_email in list_thread_emails:
                        add_text = True
                        exists_document = False
                        if last_conversation_datetime_str:
                            receivedDateTime = datetime.strptime(thread_email.get('receivedDateTime'), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            last_conversation_datetime:datetime = datetime.strptime(last_conversation_datetime_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            add_text = receivedDateTime > last_conversation_datetime
                        if add_text == True: 
                            thread_payload = thread_email.get("payload", {})
                            parsed_email_body = get_email_body(thread_payload)
                            parsed_email_body = add_final_text(parsed_email_body)
                            if parsed_email_body != '':                            
                                full_conversation.append(parsed_email_body)      
                    # Combine all conversation parts
                    full_conversation_text = "\n---\n".join(full_conversation)
                    # parsed_email_body = extract_conversation_from_email_body(html_content=email_html_content)
                    list_attachmentId = get_attachment_metadata(payload)
                    email_html_content=''
                    #email_attachment_text=''
                    # if list_thread_emails:
                    #     email_html_content  = list_thread_emails[-1].get("body", {}).get("content", "")
                    #     #email_attachment_text,exists_document = parse_email_image_attachment(message_id=message_id, email_html_content=email_html_content, access_token=access_token, is_attachment=is_attachment)
                    
                
                    if full_conversation_text == '' and len(list_attachmentId) == 0:
                        test = "2"
                        # gmail_create_label(access_token,HumanMessageCategory.SPAM.value,message_id)        
                        # gmail_move_email(access_token,message_id,'',HumanMessageCategory.SPAM.value)
                    elif exists_document==True:
                        test = "3"
                        # gmail_create_label(access_token,HumanMessageCategory.HI_COMPLEX_REQUEST.value,message_id) 
                        # gmail_mark_email_as_read(access_token,message_id)
                    else:
                        if full_conversation_text:
                            full_conversation_text = f"{full_conversation_text}\n sender: {email_from}"
                        # if email_attachment_text:
                        #     email_attachment_text = f"{email_attachment_text}\n sender: {email_from}"
                        parse_email = {
                            "message_id": message_id,
                            "thread_Id": thread_Id,
                            "body": full_conversation_text,
                            "shipping_mark":shipping_mark,
                            "list_attachmentId":list_attachmentId
                        }
                        parse_emails.append(parse_email)
                
        return parse_emails
    

def generate_gmail_access_refresh_token(refresh_token:str,email_address:str):
    url = "https://oauth2.googleapis.com/token"

    payload = {
            'client_id': Google_Client_Id,
            'scope': ' '.join(Google_Auth_Scopes),
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'client_secret': Google_Client_Secret_Key,
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            raise Exception(f'Failed to generate refresh google access token, {str(response.content)}')
        else:
            token_data = response.json()
            if 'error' in token_data:
              raise Exception(f'Failed to generate refresh google access token, {str(response.content)}')
            new_access_token = token_data['access_token']       
            new_expires_in:str = get_expire_date(token_data['expires_in'])
            with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                            UPDATE email_controller_emailcredentials
                            SET access_token = %s, token_expires = %s
                            WHERE email = %s
                        """,
                        (new_access_token, new_expires_in, email_address),
                    )
                conn.commit()
        return new_access_token, refresh_token
    except Exception as e:
         raise Exception(f'{str(e.args)}')
    


def gmail_check_if_label_exists(access_token: str, label_name: str):
    try:
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers)

        if response.status_code in [200, 201, 202]:
            content_json = response.json()
            labels = content_json.get("labels", [])

            # Search for label by name
            for label in labels:
                if label.get("name") == label_name:
                    return label.get("id")  # Return the label ID if found

            return None  # Label not found

        else:
            raise Exception(f"Failed checking if label exists: {response.status_code} {response.text}")

    except requests.RequestException as e:
        error_content = e.response.content.decode('utf-8') if e.response and e.response.content else "No response content"
        raise Exception(f"Request error checking label: {error_content}")
    except Exception as e:
        raise Exception(f"Unexpected error checking Gmail label: {type(e).__name__}: {e}")
    


def gmail_create_label(access_token: str, email_address: str, label_name: str):
    try:
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        data = {
            "name": label_name,
            "labelListVisibility": "labelShow",        # Show in label list
            "messageListVisibility": "show"            # Show in message list
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code in [200, 201]:
            response_content = response.json()
            label_id = response_content["id"]
            update_folder_id(label_id, email_address, label_name)  # Replace with your logic
            return label_id
        else:
            raise Exception(f"Failed to create label: {response.status_code} / {response.text}")

    except requests.RequestException as e:
        error_content = e.response.content.decode('utf-8') if e.response and e.response.content else "No response content"
        raise Exception(f"Error response creating label: {error_content}")
    except Exception as e:
        raise Exception(f"Unexpected error creating Gmail label {label_name}: {type(e).__name__}: {e}")

 
def gmail_move_email(access_token: str, message_id: str, label_id_to_add: str, label_id_to_remove: str = "INBOX"):
    try:
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        data = {
            "addLabelIds": [label_id_to_add],
            "removeLabelIds": [label_id_to_remove] if label_id_to_remove else []
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code not in [200, 201, 204]:
            raise Exception(f"Failed to move email. Status Code: {response.status_code}, Message: {response.text}")

    except requests.RequestException as e:
        error_content = e.response.content.decode('utf-8') if e.response and e.response.content else "No response content"
        raise Exception(f"Request error moving email: {error_content}")
    except Exception as e:
        raise Exception(f"Unexpected error moving email {message_id}: {type(e).__name__}: {e}")
 

def gmail_mark_email_as_read(access_token: str, message_id: str) -> bool:
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "removeLabelIds": ["UNREAD"]
    }

    response = requests.post(url, headers=headers, json=data)

    return response.status_code == 200
 

def fetch_thread_emails_gmail(thread_id: str, access_token: str) -> list:
   
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return []
    else:
        data = response.json()
        return data.get("messages", [])



def get_body_and_attachment_status(payload: dict) -> tuple[str, bool]:
    """
    Extracts the email body and detects if there are attachments.

    Returns:
        body (str): Email text or HTML content.
        has_attachment (bool): True if attachments exist.
    """
    email_body = ""
    has_attachment = False

    if not payload:
        return "", False

    # Fallback: body in top-level
    if payload.get("body", {}).get("data"):
        email_body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        return email_body.strip(), False

    # Recursively process parts
    parts = payload.get("parts", [])
    for part in parts:
        mime_type = part.get("mimeType")
        filename = part.get("filename", "")
        body_data = part.get("body", {}).get("data")

        # Check for readable content
        if mime_type in ["text/plain", "text/html"] and body_data:
            email_body += base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

        # Check for attachment (non-empty filename)
        if filename:
            has_attachment = True

        # Check nested parts (some Gmail messages are deeply nested)
        if part.get("parts"):
            nested_body, nested_attachment = get_body_and_attachment_status(part)
            email_body += nested_body
            has_attachment = has_attachment or nested_attachment

    return email_body.strip(), has_attachment

def get_email_body(payload: dict) -> str:
    """
    Extracts the email body content (text/plain or text/html) from the Gmail message payload.
    
    Returns:
        str: Decoded email body.
    """
    if not payload:
        return ""

    # Top-level body
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore").strip()

    body = ""

    parts = payload.get("parts", [])
    for part in parts:
        mime_type = part.get("mimeType")
        body_data = part.get("body", {}).get("data")

        if mime_type in ["text/plain", "text/html"] and body_data:
            body += base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

        # Recursively check nested parts
        if part.get("parts"):
            body += get_email_body(part)

    return body.strip()



def has_email_attachments(payload: dict) -> bool:
  
    if not payload:
        return False

    if payload.get("filename"):
        return bool(payload["filename"].strip())

    parts = payload.get("parts", [])
    for part in parts:
        filename = part.get("filename", "")
        if filename:
            return True

        # Recursively check nested parts
        if part.get("parts") and has_email_attachments(part):
            return True

    return False


def get_attachment_ids(payload: dict) -> list[str]:
 
    attachment_ids = []

    if not payload:
        return []

    parts = payload.get("parts", [])
    for part in parts:
        filename = part.get("filename", "")
        body = part.get("body", {})

        # If this part is an attachment
        if filename and body.get("attachmentId"):
            attachment_ids.append(body["attachmentId"])

        # Recurse into nested parts
        if part.get("parts"):
            attachment_ids.extend(get_attachment_ids(part))

    return attachment_ids



def get_attachment_metadata(payload: dict) -> list[dict]:

    attachments = []

    if not payload:
        return []

    parts = payload.get("parts", [])
    for part in parts:
        filename = part.get("filename", "")
        mime_type = part.get("mimeType", "")
        body = part.get("body", {})

        if filename and body.get("attachmentId"):
            attachments.append({
                "attachmentId": body["attachmentId"],
                "filename": filename,
                "mimeType": mime_type
            })

        # Recurse into nested parts
        if part.get("parts"):
            attachments.extend(get_attachment_metadata(part))

    return attachments



def get_gmail_attachment_bytes(message_id: str, attachment_id: str, access_token: str) -> bytes:
    
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/attachments/{attachment_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        attachment_data = response.json().get('data')
        if not attachment_data:
            raise Exception("No attachment data found in response.")
        return base64.urlsafe_b64decode(attachment_data)
    else:
        raise Exception(f"Failed to fetch attachment: {response.status_code} - {response.text}")
    

def gmail_send_reply_email_raw(access_token: str, message_id: str, reply_content: str):
    # Step 1: Get the original message
    get_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}?format=metadata"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(get_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch message: {response.status_code} / {response.text}")

    data = response.json()
    headers_list = data.get("payload", {}).get("headers", [])
    thread_id = data.get("threadId")

    # Step 2: Extract headers safely
    def get_header(name: str) -> str:
        for h in headers_list:
            if h["name"].lower() == name.lower():
                return h["value"]
        return ""

    to = get_header("From") or "unknown@example.com"
    subject = get_header("Subject") or ""
    in_reply_to = get_header("Message-ID")
    references = get_header("References")
    if in_reply_to:
        references = (references + " " + in_reply_to).strip()

    # Step 3: Construct MIME email
    mime_msg = MIMEText(reply_content, "html")
    mime_msg["To"] = to
    mime_msg["Subject"] = subject
    if in_reply_to:
        mime_msg["In-Reply-To"] = in_reply_to
    if references:
        mime_msg["References"] = references

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()

    # Step 4: Send message
    send_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    send_body = {
        "raw": raw,
        "threadId": thread_id
    }

    send_response = requests.post(send_url, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }, json=send_body)

    if send_response.status_code not in [200, 202]:
        raise Exception(f"Failed to send reply: {send_response.status_code} / {send_response.text}")

    return send_response.json()
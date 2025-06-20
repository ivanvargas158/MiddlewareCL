import json
import logging
import azure.functions as func
from services.outlook_service import fetch_outlook_new_emails
from services.gmail_service import fetch_gmail_new_emails
from utils.global_resources import create_record_azure_insight
from schemas.general_enum import EmailType
def fetch_emails(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a getting new emails from Outlook EMail')

    try:
        req_body = req.get_json()
        access_token = req_body.get("access_token")
        email_address = req_body.get("email_address")
        folder_spam_id = req_body.get("folder_spam_id")
        folder_internal_email_id = req_body.get("folder_internal_email_id")
        email_type = req_body.get("email_type")
        
        if email_type == EmailType.microsoft:
            emails = fetch_outlook_new_emails(email_address,access_token,folder_spam_id,folder_internal_email_id,fetch_limit=10)
        else:
            emails = fetch_gmail_new_emails(email_address,access_token,folder_spam_id,folder_internal_email_id,fetch_limit=1)
        
        return func.HttpResponse(
            json.dumps({"emails": emails, "email_count": len(emails)}),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        create_record_azure_insight(e,"there isn't a run_id",'receive_new_outlook_emails')      
        return func.HttpResponse(f'Error getting_new_outlook_emails: {str(e)}', status_code=400)

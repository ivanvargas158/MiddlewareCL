import json
import logging
import azure.functions as func
from services.email_service import ensure_valid_token
from utils.global_resources import create_record_azure_insight

def generate_oauth2_refresh_access_token(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Starting Generate oauth2 refresh & access token for outlook email operation")
    try:
        req_body = req.get_json()
        email_address = req_body.get("email_address")
        new_access_token, new_refresh_token,folder_id,folder_spam_id,folder_internal_email_id,email_type = ensure_valid_token(email_address=email_address)
        if not new_access_token or not new_refresh_token:
            return func.HttpResponse(f'Generate New Outlook OAuth2 Token is Failed', status_code=400)    
        return func.HttpResponse(
            json.dumps({"access_token": new_access_token, 
                        "refresh_token": new_refresh_token,
                        "folder_id": folder_id,
                        "folder_spam_id":folder_spam_id,
                        "folder_internal_email_id":folder_internal_email_id,
                        "email_type": email_type
                        }),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        create_record_azure_insight(e,'generate_oauth2_refresh_access_token','generate_oauth2_refresh_access_token')  
        return func.HttpResponse(f'Post API payload is not valid in generate_oauth2_refresh_access_token, {str(e)}', status_code=400)
    


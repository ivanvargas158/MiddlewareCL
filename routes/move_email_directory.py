import logging
import azure.functions as func
from services.outlook_service import outlook_move_email,outlook_mark_email_as_read,outlook_mark_red_flag
from services.gmail_service import gmail_move_email
from services.postgresql_db import save_email_exception
from utils.global_resources import create_record_azure_insight
from schemas.general_enum import EmailType

def move_email_folder(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function to move email")
    try:
        req_body = req.get_json()
        access_token = req_body.get("access_token")        
        message_id = req_body.get("message_id")
        folder_id = req_body.get("folder_id")
        folder_spam_id = req_body.get("folder_spam_id")
        target_category = req_body.get("target_category")
        run_id = req_body.get("run_id")  
        email_type = req_body.get("email_type")
        if email_type == EmailType.microsoft:
            outlook_move_email(access_token, message_id,folder_id,target_category,folder_spam_id)
        if email_type == EmailType.google:
            gmail_move_email(access_token, message_id,folder_id)
        return func.HttpResponse("Email move folder successfully.", status_code=200)       
    except Exception as e:
        if run_id:
            try:
                create_record_azure_insight(e,run_id,'outlook_move_email_folder')              
                save_email_exception(message_id,str(e),run_id)
            except Exception as excep_alt:
                save_email_exception(message_id,'outlook_move_email_folder',run_id) 
            outlook_mark_email_as_read(access_token,message_id)
            outlook_mark_red_flag(access_token,message_id)
        return func.HttpResponse(f'Error outlook_move_email_folder: {str(e)}', status_code=400)
    
      
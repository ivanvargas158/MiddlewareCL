import logging
import azure.functions as func
from services.outlook_service import outlook_send_reply_email,outlook_mark_email_as_read,outlook_mark_red_flag
from services.gmail_service import gmail_send_reply_email_raw
from services.postgresql_db import save_email_exception
from utils.global_resources import create_record_azure_insight
from schemas.general_enum import EmailType

def reply_email(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function to send reply email")

    try:
        req_body = req.get_json()
        access_token = req_body.get("access_token")
        reply_content = req_body.get("response")
        message_id = req_body.get("message_id")
        source = req_body.get("source")
        run_id = req_body.get("run_id")  
        email_type = req_body.get("email_type")        
        if email_type == EmailType.microsoft:
            outlook_send_reply_email(access_token, reply_content, message_id,source) 
        if email_type == EmailType.google:
            gmail_send_reply_email_raw(access_token,message_id,reply_content)
               
        return func.HttpResponse("Email reply sent successfully.", status_code=200)


    except Exception as e:
        if run_id:
            try:
                create_record_azure_insight(e,run_id,'outlook_reply_email')              
                save_email_exception(message_id,str(e),run_id)
            except Exception as excep_alt:
                save_email_exception(message_id,'outlook_reply_email',run_id)  
            outlook_mark_email_as_read(access_token,message_id)
            outlook_mark_red_flag(access_token,message_id)
        return func.HttpResponse(f'Error outlook_reply_email: {str(e)}', status_code=400)
      
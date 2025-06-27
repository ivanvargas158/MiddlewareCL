import json
import logging
import azure.functions as func
from services.postgresql_db import save_email_exception
from services.outlook_service import outlook_mark_email_as_read,outlook_mark_red_flag,create_outlook_label
from schemas.email_category_classification_enum import HumanMessageCategory
from utils.global_resources import create_record_azure_insight
from services.doc_process_service import ocr_process_document
from core.custom_exceptions import ValidationError 

def ocr_process_document_request(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function to Quote') 
    try:
        req_body = req.get_json()       
        message_id = req_body.get('message_id') 
        thread_Id = req_body.get('thread_Id')
        list_attachmentId = req_body.get('list_attachmentId')
        access_token = req_body.get("access_token") 
        run_id = req_body.get("run_id")
        email_type = req_body.get("email_type")
        shipping_mark = req_body.get("shipping_mark")
        new_shipment_reponse:str = ocr_process_document(message_id,thread_Id,list_attachmentId,access_token,email_type,shipping_mark)
        return func.HttpResponse(
            json.dumps({""
                     "response": new_shipment_reponse
                        }),
            mimetype="application/json",
            status_code=200,
        )   
    except ValidationError as ve:
        logging.warning(f"Validation error occurred: {ve}")
        if run_id:
            create_record_azure_insight(ve, run_id, 'cl_shipment_request')
            save_email_exception(message_id, str(ve), run_id)
            outlook_mark_email_as_read(access_token, message_id)
            outlook_mark_red_flag(access_token, message_id)
        return func.HttpResponse(
            json.dumps({"ValidationError": str(ve)}),
            mimetype="application/json",
            status_code=422,
        )
    except Exception as e:
        if run_id:
            try:   
                create_record_azure_insight(e,run_id,'cl_shipment_request')     
                save_email_exception(message_id,str(e),run_id)
            except Exception as excep_alt:
                save_email_exception(message_id,'cl_shipment_request',run_id)      
            outlook_mark_email_as_read(access_token,message_id)
            outlook_mark_red_flag(access_token,message_id)
        return func.HttpResponse(f'Handling quote request Failed.{str(e)}', status_code=400)
    
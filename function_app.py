import azure.functions as func
import logging
from routes.generate_oauth2_access_refresh_token import generate_oauth2_refresh_access_token
from routes.fetch_emails import fetch_emails
from routes.doc_process_request import ocr_process_document_request
from routes.move_email_directory import move_email_folder
from routes.reply_email import reply_email
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="http_trigger_outlook_refresh_access_token")
def http_trigger_outlook_refresh_access_token(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function http_trigger_outlook_refresh_access_token')
    return generate_oauth2_refresh_access_token(req)

@app.route(route="http_trigger_receive_new_outlook_emails")
def http_trigger_receive_new_outlook_emails(req: func.HttpRequest) -> func.HttpResponse:
     logging.info('Python HTTP trigger function http_trigger_receive_new_outlook_emails')
     return fetch_emails(req)   

@app.route(route="http_trigger_ocr_process_document_request")
def http_trigger_ocr_process_document_request(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function http_trigger_ocr_process_document_request')
    return ocr_process_document_request(req)

@app.route(route="http_trigger_outlook_move_email_folder")
def http_trigger_outlook_move_email_folder(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function http_trigger_outlook_move_email_folder')
    return move_email_folder(req)

@app.route(route="http_trigger_outlook_send_reply_email")
def http_trigger_outlook_send_reply_email(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function http_trigger_outlook_send_reply_email')
    return reply_email(req)

@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')


    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
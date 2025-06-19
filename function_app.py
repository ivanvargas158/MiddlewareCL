import azure.functions as func
import logging
from routes.outlook_generate_oauth2_access_refresh_token import generate_oauth2_refresh_access_token
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="http_trigger_outlook_refresh_access_token")
def http_trigger_outlook_refresh_access_token(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function http_trigger_outlook_refresh_access_token')
    return generate_oauth2_refresh_access_token(req)

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
import logging
import re
from zoneinfo import ZoneInfo
from datetime import datetime
from azure.monitor.opentelemetry import configure_azure_monitor
from core.settings import Azure_Middleware_InstrumentationKey
from opentelemetry import trace
from datetime import datetime, timezone, timedelta


class global_azure_monitor:
    def __init__(self):
        configure_azure_monitor(
            connection_string= f"InstrumentationKey={Azure_Middleware_InstrumentationKey}"
        )

azure_monitor = global_azure_monitor()
# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Get OpenTelemetry tracer
tracer = trace.get_tracer(__name__)

def create_record_azure_insight(error: Exception,run_id:str,function_name:str):
    logger.error(f'End point: {function_name}: {error} \n run_id: {run_id}', exc_info=True)
    span = tracer.start_span(function_name)
    span.record_exception(error)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(f'{error} / {run_id}')))    
    span.end()        


def get_expire_date(expire_in_seconds:int)->str:
    return (datetime.now(tz=timezone.utc) + timedelta(seconds=expire_in_seconds)).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00"

def convert_to_datetime(date_str:str)->datetime:
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def generate_greetings(): 

    # Get current time in Central Time (Midwest)
    central_time = datetime.now(ZoneInfo("America/Chicago"))
    #central_time = datetime.now()
    current_hour = central_time.hour

    # Determine the greeting based on the hour
    if 0 <= current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    return greeting



def replace_newline(content:str)->str:
    content = content.replace("\n", "")
    content = content.replace("\\", "")
    return content



def get_first_key_by_value(dictionary, search_value):
    for key, value in dictionary.items():
        if key == search_value:
            return value
    return None

def clean_response(reply_content):
    reply_content = replace_newline(reply_content)
    return reply_content



def get_id_by_display_name(data, display_name):
    
    if "value" in data and isinstance(data["value"], list):
        for folder in data["value"]:
            if "displayName" in folder and folder["displayName"] == display_name:
                return folder["id"]
    return None  # Return None if no matching folder is found


def get_currentdate():
    return datetime.now(ZoneInfo("America/Chicago"))
    #return datetime.now()


    
def clean_payload_structure(schema):
    def extract(properties):
        result = {}
        for key, value in properties.items():
            if value.get("type") == "object":
                result[key] = extract(value.get("properties", {}))
            elif value.get("type") == "array":
                item_schema = value.get("items", {})
                if item_schema.get("type") == "object":
                    result[key] = [extract(item_schema.get("properties", {}))]
                else:
                    result[key] = []
            else:
                result[key] = value.get("default", "")
        return result

    return extract(schema.get("properties", {}))



def remove_empty_fields(data):
    if isinstance(data, dict):
        clean_dict = {}
        for key, value in data.items():
            cleaned_value = remove_empty_fields(value)
            if cleaned_value not in ("", None, [], {}, "undefined"):
                clean_dict[key] = cleaned_value
        return clean_dict

    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            cleaned_item = remove_empty_fields(item)
            # Only include item if it has meaningful content
            if cleaned_item not in ("", None, [], {}, "undefined"):
                cleaned_list.append(cleaned_item)
        return cleaned_list if cleaned_list else None

    else:
        return data


def is_valid_shipping_mark(subject: str) -> bool:
    pattern = r"SO/\d{4}-\d{1,2}[A-Z]?"
    return re.search(pattern, subject) is not None

def extract_shipping_mark(subject: str) -> str:
    pattern = r"SO/\d{4}-\d{1,2}[A-Z]?"
    match = re.search(pattern, subject)
    if match:
        return match.group(0)
    else:
        return ""

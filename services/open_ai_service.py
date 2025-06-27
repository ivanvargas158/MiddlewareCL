
import requests
import json
import os
import contextlib
from openai import AzureOpenAI,OpenAI
from core.settings import Openai_Base_Model,Openai_Base_Url,Openai_Api_Key_azure_embedded,Openai_url_azure_embedded,Azure_Search_Index_Key,Azure_Search_Index_Url,Azure_Search_Index_version,Openai_Api_Key,Openai_Base_Model
from schemas.general_enum import APIAction
from core.load_json import get_json_schema
from core.custom_exceptions import ValidationError 
def call_openai(Openai_Api_Key:str,payload):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Openai_Api_Key}",
    }
    try:
        "https://api.openai.com/v1"
        response = requests.post(
            f"{Openai_Base_Url}/chat/completions", headers=headers, json=payload
        )
        response.raise_for_status() 
        response_content = response.json()["choices"][0]["message"]["content"]
        return response_content
    except requests.exceptions.RequestException as e:
        raise Exception(f"{e.args}")
    # finally:
    #     save_payload(json.dumps(payload),"request_prompt_openai_makeformatrate")
    #     save_payload(json.dumps(response_content),"response_openai_rate")



def build_gpt_payload_for_extracting_payload(content, json_schema):
    """
    Builds the payload for GPT-4 API request.
    Ensures the request is well-structured to prompt GPT-4 to return valid JSON output with correct data types.
    """

    json_structure_str = json.dumps(json_schema, indent=2)
    # Define the user prompt, instructing GPT-4 to generate a valid JSON based on the provided structure
    human_content = f"""
    You are an AI assistant specialized in extracting complex shipping and logistics data from emails into a specific JSON format.

    Task: Carefully extract relevant details from the provided email content and populate the JSON structure accordingly.

    Guidelines:
    1. Extract values present in the email content.
    2. For missing values:
    - Use the default value provided in the JSON schema if available.
    - If no default value is specified in the schema:
        - Use an empty string for strings
        - Use null for missing objects
        - Use 0 for numbers
        - Use false for booleans
        - Use [] for empty arrays
    3. Ensure all fields are populated with the appropriate data types as specified in the JSON schema.
    4. Maintain the correct JSON structure and hierarchy, including all required fields.
    5. Pay special attention to nested objects and arrays, ensuring they are correctly formatted.
    6. Ensure date-time fields use the ISO 8601 format.
    7. For duplicate fields take the last value from Email Content.
    8. For address fields like pickup and delivery take the country and postal code or the city. For example
       - US Chicago,IL 60601: country:US, city:Chicago,state:IL,postal code:60601.
       - 60601, 32003, 32034, etc. : 
            - Assign them as postal code 
            - Find the country, use the ISO format 2-character and assign it as country  
       - Lake worth Fl 33467 US: country:US, city:Lake worth,state:Fl,postal code:33467.
       - Airport codes: ATL,BCN,CCS,DXB,GRU,JFK,MIA,SUB,VVI,YYZ,JRZ,PTY etc. assign them as city.
       - Cities: Luanda,Buenos Aires,Cordoba,Boundary Bend,Beirut,Surry Hills, etc. assign them as city.
       - UNLOCODE: VEBLA,JPTYO,JPOSA,UAIEV,PELIM,CRSJO,AUTOG,BOSRZ, etc. assign them as city.           
    Email Content:
    \"{content}\"

    JSON structure to populate (ensure strict adherence to the schema):

    {json_structure_str}

    Provide the extracted data in a valid JSON format that precisely follows the given structure. Include all required fields, maintain the hierarchy of the JSON schema, and use default values where appropriate for missing information.
    """

    # Return the payload formatted for the GPT-4 API request
    return {
        "model": Openai_Base_Model,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant expert in extracting complex shipping and logistics data from emails into precise JSON format, using schema defaults for missing values.",
            },
            {"role": "user", "content": human_content},
        ],
        "temperature": 0, 
    }


def build_gpt_payload_shipment_cl(input_json, json_shipment_cl):
    instruction_template = f"""
    You are an advanced document-understanding agent, optimized for shipping & logistics workflows.

    Take the following JSON file as your source data:

    {input_json}

    Your task:
    - Map each relevant field from the source JSON to the target schema below, following the field names and structure exactly.
    - Output a valid, minified JSON object that matches the target schema for the API call.
    - If any field in the target schema is missing or cannot be mapped from the source, set its value to null.
    - Do not invent, transform, or interpret data. Use only the values from the source JSON.
    - Do not include any extra commentary, markup, or formatting—output only the minified JSON.

    Target schema for API payload:

    {json_shipment_cl}

    Output only the resulting JSON payload, nothing else.
    """

    return {
        "model": Openai_Base_Model,
        "messages": [
            {"role": "user", "content": instruction_template},
        ],
        "temperature": 0, 
    }



@contextlib.contextmanager
def azure_openai_context():
    
    client = AzureOpenAI(
            api_key=Openai_Api_Key_azure_embedded,
            api_version="2024-12-01-preview",
            azure_endpoint=Openai_url_azure_embedded
    )

    yield client

    client.close

@contextlib.contextmanager
def openai_client():
    
    client = OpenAI(
        api_key = Openai_Api_Key,
    )

    yield client

    client.close



def embed_text(text:str):
    with azure_openai_context() as openai_connection:
        result = openai_connection.embeddings.create(
            input=text,
            model="text-embedding-3-small", 
            encoding_format="float"
        )
        return result.data[0].embedding
    
def push_documents_to_index_azure(document: dict):

    payload = {
    "value": [{"@search.action": "upload", **document}]
    }

    url = Azure_Search_Index_Url
    headers = {
        "Content-Type": "application/json",
        "api-key": Azure_Search_Index_Key
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise ValidationError(f'Unable to updated documents to Azure Index, {str(response.content)}')
        

def generate_payload_update_shipment(schema_result_azure_search)->dict:
    update_shipment_schema:str = get_json_schema(APIAction.update_shipment)
       
    try:  

        shipment_mapper_prompt = """
            You are “ShipmentMapper”, a precise JSON-transformation assistant.

            **Job**

            1. Input #1 ('azureSearchDocs`) is an array containing one or more documents returned by Azure AI Search.  
            2. Input #2 (`updateShipmentSchema`) is the JSON-Schema that the destination objects MUST validate against.  
            3. Create **one** `UpdateShipment` object for every unique `shipment_id` found in `azureSearchDocs`.  
            • Group all Azure docs that share the same `shipment_id`.  
            • If a field is duplicated across group members, prefer the one whose Azure document has the highest `@search.score`.  
            4. Return **ONLY** a JSON,  whose items conform 100 % to `updateShipmentSchema`.  
            • Do **NOT** wrap the output in Markdown or any extra keys.  
            • If a value is unknown or missing, omit that property entirely (do **not** output `null`).  
            • Strings must be trimmed; numbers and dates normalised as shown below.  

            azureSearchDocs

            {azureSearchDocs_schema}    

            updateShipmentSchema

            {updateShipmentSchema_schema}    
            
            **Field-mapping rules**

            | UpdateShipment field | Azure field(s) & transformation rules |
            |----------------------|----------------------------------------|
            | `_id`                | don't update it |
            | `referenceName`      | `shipment_id` |
            | `internalReference`  | `brasil_master_bill_of_lading_booking_ref` or fallback to `brasil_master_bill_of_lading_bill_of_lading_no` |
            | `notes`              | Concatenate (with “ | ”) any of:
            • `brasil_master_bill_of_lading_description_of_packages_and_goods`
            • `brasil_certificate_of_origin_goods_description` |
            | `eta`                | If a doc contains `brasil_certificate_of_origin_destination` AND a valid arrival date (ISO or “dd-MMM-yyyy”), convert to `YYYY-MM-DD`. Otherwise omit. |
            | `etd`                | Parse `brasil_master_bill_of_lading_shipped_on_board_date` → `YYYY-MM-DD`. |
            | `deliveryAddress`    | `brasil_master_bill_of_lading_place_of_delivery` |
            | `packagesInfo[]`     | For each container listed in:
                - `brasil_master_bill_of_lading_container_cargo_table` OR  
                - `brasil_certificate_of_origin_container_details`:  
                - `packageType`: `"CT"` unless a more specific term appears before the first “-”  
                - `amount`: integer carton count  
                - `weight`: numeric (strip "kgs", "KGS", and thousands separators)  
                - `weightMetric`: `"kg"`  
                - `volume`: numeric (strip "cu. m.")  
                - `volumeMetric`: `"m3"` |
            | `totalWeight`        | Convert `brasil_master_bill_of_lading_total_gross_weight` to number (kg). |
            | `totalVolume`        | Convert `brasil_master_bill_of_lading_measurement` to number (m³). |
            | `paymentTerms`       | `brasil_commercial_invoice_payment_terms` |
            | `carrier.name`       | Prefer `brasil_master_bill_of_lading_agent`; else use `brasil_master_bill_of_lading_vessel_and_voyage_no` |
            | `carrier.scac[]`     | If a SCAC code (4 letters) appears anywhere in `brasil_master_bill_of_lading_agent`, extract and output as one-element array |
            | `shipper.name`       | `brasil_master_bill_of_lading_shipper` |
            | `shipper.address`    | If `brasil_packing_list_importer_details` contains “FORT” and looks like an address, use it. Else omit. |
            | `consignee.name`     | `brasil_master_bill_of_lading_consignee` fallback `brasil_certificate_of_origin_importer` |
            | `consignee.address`  | From `brasil_packing_list_importer_details` if it matches consignee name |

            **Data-normalisation helpers**

            * Remove thousands separators but keep decimals (`27,671.930 KGS` → `27671.93`)
            * Kg↔tonnes conversions are NOT required—keep kilograms
            * Dates: accept “20-Apr-2025” or ISO strings; always emit `YYYY-MM-DD`
            * Ignore commas inside numeric strings when parsing
            * Titles in names (Mr., Inc., S.A.) should remain as given
            """


        openai_prompt = shipment_mapper_prompt.format(azureSearchDocs_schema=schema_result_azure_search, updateShipmentSchema_schema=update_shipment_schema)

        with openai_client() as client:
            response = client.chat.completions.create(
                model =Openai_Base_Model,
                messages = [
                    {"role": "user", "content": openai_prompt},
                ],
                temperature = 0.0,
                response_format={ "type": "json_object" }

            ) 

        content = response.choices[0].message.content

        response_data = json.loads(str(content))        

        return response_data

    except json.JSONDecodeError as e:
        raise ValidationError(errors=f"Error: Failed to parse JSON from LLM response for memory extraction(generate_payload_update_shipment): {e}")
    except Exception as e:
        raise ValidationError(errors=f"Error during memory extraction(generate_payload_update_shipment): {e}")
    

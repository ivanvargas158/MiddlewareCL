
import requests
import json
from core.settings import Openai_Base_Model,Openai_Base_Url

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
import requests
import json

def create_chat_session(bearer:str,uuui:str):
    try:
            url = f"https://app.gpt-trainer.com/api/v1/chatbot/{uuui}/session/create"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer}",
            }

            response = requests.post(url, headers=headers)

            if response.status_code == 200:
                try:
                    session_data = response.json()
                    return session_data["uuid"]
                except json.JSONDecodeError as e:
                    raise Exception(f"JSON decoding error: {e}")
            else:
                raise Exception(f"Failed to create chat session. Status code: {response.status_code}, Response: {response.text}")                

    except requests.RequestException as e:
       raise Exception({e})
    except KeyError as e:
        raise Exception({e})
    except Exception as e:
        raise Exception({e})
    
def create_request(content:str,bearer:str,uuui:str):
    session_uuid = create_chat_session(bearer,uuui)
   
    url_endpoint = f"https://app.gpt-trainer.com/api/v1/session/{session_uuid}/message/stream"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
    }
    payload = {"query": content}

    response = requests.post(url_endpoint, headers=headers, json=payload, stream=True)
    return  response.text  
   
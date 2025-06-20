import re
import base64
import io
import requests
import html
import logging
from bs4 import BeautifulSoup
from core.settings import Openai_Api_Key_Vision,Openai_Base_Model,Error_text_email

def filter_emails_from_agents(data, agent_emails):
    filtered_emails = [
        email for email in data
        if email["from"]["emailAddress"]["address"] not in agent_emails
    ]
    return filtered_emails

def add_final_text(email_html_content:str)->str:
    result=''
    parsed_email_body = extract_conversation_from_email_body(html_content=email_html_content)
    parsed_email_body = parsed_email_body.strip()
    if Error_text_email not in parsed_email_body and parsed_email_body!='**Customer:**':
          result = parsed_email_body
    return result


valid_formats = ["JPEG", "PNG", "BMP", "PDF", "TIFF"]
def extract_conversation_from_email_body(html_content: str) -> str:
    # Parse the HTML content
    html_content = html.unescape(html_content) 
    soup = BeautifulSoup(html_content, 'html.parser')
    updated_body:str=''
    # Extract the body tag
    body = soup.find('body')
    try:
        #updated_body = body.get_text(separator='\n')
        if body is not None:
            updated_body = body.get_text(separator='\n')
    except:
        updated_body = html_content

    # Remove excessive newlines
    updated_body = re.sub(r'\n{2,}', '\n', updated_body).strip()

    updated_body = updated_body.replace("\xa0", " ")

    updated_body = clean_content(updated_body)    

    formatted_message:str = ''
    if '*****Service Message*****' in updated_body:
        label = "Service"
        formatted_message = f"**{label}:** {updated_body[25:]}"  # Bold the label


    else:
        label = "Customer"
        formatted_message = f"**{label}:** {updated_body}"  # Bold the label

    formatted_message = formatted_message.replace("\n", " ")

    return formatted_message

def clean_content(content:str)->str:
    cleaned_lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip lines that match unwanted patterns
        if re.search(r'(regards|thank you|survey|original message|subject:|from:|to:|sent:|sincerely|Phone|Email|dear team|good morning|Thanks|bestregards|tax|tel +|fax|whatsapp|wechat|web:)', line, re.IGNORECASE):
            continue
        if re.search(r'\bwww\.\S+|\S+@\S+|\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}', line, re.IGNORECASE):
            continue
        if re.search(r'(senior|account specialist|unishippers)', line, re.IGNORECASE):
            continue
        if re.search(r'(asia atlantic|wca id|id \d+)', line, re.IGNORECASE):
            continue
        if re.search(r'samae dam subdistrict.*bangkok\s*\d+', line, re.IGNORECASE):
            continue
        cleaned_lines.append(line)
    "\n".join(cleaned_lines)
    return "\n".join(cleaned_lines)
  
import psycopg2
import logging
import functools
import re
from core.settings import DB_User, DB_pwd, DB_Host, DB_Name,Outlook_Folder_to_Move_Spam_Email,Outlook_Folder_to_Move_Internal_Emails
from typing import Tuple
from utils.global_resources import get_currentdate
special_chars = r"[\"',;:!@#$%^&*()<>?/\\|{}[\]~`]"  # Define characters to replace
   
@functools.cache            
def get_internal_emails()-> list[Tuple[str, ...]]:
    with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                    """select email from public.internal_emails 
                    """,
            )
            result = cursor.fetchall()
            return result
        
@functools.cache            
def get_freight_class()-> list[Tuple[str, ...]]:
    with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                    """SELECT freight_class,density_ini,density_end FROM  public.freight_class order by id
                    """,
            )
            result = cursor.fetchall()
            return result
            

def update_last_human_email_category_content(message_id: str, last_category: str, last_content: str):
    try:
        with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
            with conn.cursor() as cursor:
                # SQL query to update or insert with automatic 'updated_at' value
                query = """
                    INSERT INTO email_controller_emaildatabase (email_id, last_category_status, last_category_content, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (email_id) 
                    DO UPDATE SET last_category_status = %s, last_category_content = %s, updated_at = NOW()
                """
                cursor.execute(
                    query,
                    (message_id, last_category, last_content, last_category, last_content)
                )
                conn.commit()
                return True
    except Exception as e:
        logging.error(f'Error updating or inserting last human message category content: {str(e)}')
        raise Exception(f'Error updating or inserting last human message category content: {str(e)}')
    

def update_folder_id(folder_id:str,email_address:str,folder:str):
    field_name = 'folder_id'
    if folder == Outlook_Folder_to_Move_Spam_Email:
        field_name = 'folder_spam_id'
    if folder == Outlook_Folder_to_Move_Internal_Emails:
        field_name = 'folder_internal_email_id'
    with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                    UPDATE email_controller_emailcredentials
                    SET {field_name} = %s
                    WHERE email = %s
                """,
                    (folder_id, email_address),
            )
        conn.commit()


def get_last_conversation(conversation_id:str) -> str|None:
     with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
        with conn.cursor() as cursor:
                cursor.execute(
                    """
                        SELECT created_at
                        FROM public.emails_storage_messages
                        WHERE conversation_id = %s 
                        order by id desc
                        LIMIT 1;
                    """,
                    (conversation_id,)
                )
                result = cursor.fetchone()
                if result: #exists conversation with a old request
                    return result[0]
                else:
                    return None
        

def save_email_exception(message_id:str,message:str,runId:str):
    if message_id and message_id!='None':
        message = re.sub(special_chars, " ", message)
        current_datetime = get_currentdate()
        with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO public.email_exceptions(message_id, message, created_at,run_id) VALUES('{message_id}','{message}','{current_datetime}','{runId}')"
                )
                conn.commit()


                
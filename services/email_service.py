def ensure_valid_token(email_address: str) -> tuple[str, str,str, str,str,str]:
    try:     
        with psycopg2.connect(host=DB_Host, dbname=DB_Name, user=DB_User, password=DB_pwd) as conn:
            with conn.cursor() as cursor:   
                cursor.execute(
                    """
                        SELECT access_token, refresh_token, token_expires,folder_id,folder_spam_id,folder_internal_email_id,email_type
                        FROM email_controller_emailcredentials
                        WHERE email = %s
                    """,
                    (email_address,),
                )
                result = cursor.fetchone()
 
                if result is None:
                    raise Exception("Email credentials not found.")                         
                
                access_token, refresh_token, token_expires,folder_id,folder_spam_id,folder_internal_email_id,email_type = result                             

                # Ensure token_expires is a datetime object
                if isinstance(token_expires, str):
                    token_expires = datetime.fromisoformat(token_expires)
                
                # Check if the token is about to expire in less than 10 minutes
                if token_expires - timedelta(minutes=10) < datetime.now(tz=timezone.utc):
                    new_access_token, new_refresh_token = '',''
                    new_access_token, new_refresh_token  = generate_gmail_access_refresh_token(refresh_token,email_address)
                    #new_access_token, new_refresh_token = generate_outlook_access_refresh_token(refresh_token, email_address)
                    access_token = new_access_token
                    refresh_token = new_refresh_token 

                if folder_id is None:
                    folder_id = gmail_check_if_label_exists(access_token,Outlook_Folder_to_Move_Email)
                    if(not folder_id or folder_id==''):
                        folder_id = gmail_create_label(access_token,email_address,Outlook_Folder_to_Move_Email)
                    else:
                        update_folder_id(folder_id,email_address,Outlook_Folder_to_Move_Email)
                
                if folder_spam_id is None:
                    folder_spam_id = gmail_check_if_label_exists(access_token,Outlook_Folder_to_Move_Spam_Email)
                    if(not folder_spam_id or folder_spam_id==''):
                        folder_spam_id = gmail_create_label(access_token,email_address,Outlook_Folder_to_Move_Spam_Email)
                    else:
                        update_folder_id(folder_spam_id,email_address,Outlook_Folder_to_Move_Spam_Email)

                # if folder_internal_email_id is None:
                #     folder_internal_email_id = outlook_check_if_exists_processedfolder(access_token,Outlook_Folder_to_Move_Internal_Emails)
                #     if(not folder_internal_email_id or folder_internal_email_id==''):
                #         folder_internal_email_id = outlook_create_folder(access_token,email_address,Outlook_Folder_to_Move_Internal_Emails)
                #     else:
                #         update_folder_id(folder_internal_email_id,email_address,Outlook_Folder_to_Move_Internal_Emails)
                return access_token, refresh_token,folder_id,folder_spam_id,folder_internal_email_id,email_type
    except Exception as e:
        raise Exception(f"Error ensuring valid token: {str(e)}")

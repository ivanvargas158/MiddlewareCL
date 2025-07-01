import os
from pathlib import Path
from pydantic import field_validator,fields,Field

#Prod
# DB_Host = "c-synapsevue-prod.ligp6eniqvdyez.postgres.cosmos.azure.com"
# DB_Name = "emailagent"
# DB_User = "citus"
# DB_pwd = "C2C079D2-CA97-4995-ADED-1B46ADF1EBB0"

#Dev
DB_Host = "c-synapsevuedatabase.b6un2utbpmag4r.postgres.cosmos.azure.com"
DB_Name = "citus"
DB_User = "citus"
DB_pwd = "aV7Uccsj37TdmtA"


Azure_Cliente_Id = "df6095a7-39cc-4b92-877d-60a6347a00f8"
Azure_Cliente_Secret = Field(validation_alias="AZURE_CLIENTE_SECRET")

Outlook_Personal_Refresh_Token_Scopes = ["offline_access", "Mail.ReadWrite", "Mail.Send", "Mail.Read", "User.read"]
Outlook_Business_Refresh_Token_Scopes = "https://graph.microsoft.com/.default"
Outlook_Folder_to_Move_Email = "Processed SV"
Outlook_Folder_to_Move_Spam_Email = "AI Spam Filter"
Outlook_Folder_to_Move_Internal_Emails = "Internal Emails"

Outlook_Folder_to_Move_Email_CL = "Processed CL"
Outlook_Folder_to_Move_Email_Unprocessed_CL = "Unprocessed CL"

Agent_Emails = {}

Openai_Api_Key_new =  os.getenv("OPENAI_API_KEY_NEW") 
Openai_Base_Url = "https://api.openai.com/v1"
Openai_Base_Model = "gpt-4.1-mini"

Gpt_Trainer_Beaer_Key_Category_Classify = Field(validation_alias="GPT_TRAINER_BEAER_KEY_CATEGORY_CLASSIFY")
Gpt_UUID_Category_Classify = "04ebc0b2909f489dbac31dccd74bc3e9"

Cargologik_Username = "michael+amc@cargologik.com"
Cargologik_Password = "Cargologiktest999"
Cargologik_Url = "https://acmemanucompany.cargologik.app/api/v2/"

Google_Service_Account_File = f'{Path.cwd()}/shared/jsons/googlesheet_credentials.json'
Google_Sheet_Scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]


Azure_Middleware_InstrumentationKey = "39ebfea2-59f5-403d-a60a-7b0c4cb73d1a"
Error_text_email = "Oops..looks like we need a little more info to move forward"
Max_Tokens_text = 3500 

Filter_Spam_Emails = ':: System Warning :: Notification had no recipients'

Max_Weight_FCL = 170000


Google_Auth_Scopes = ['https://mail.google.com/', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile','https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.labels']
Google_Client_Id = os.getenv("GOOGLE_CLIENT_ID")
Google_Client_Secret_Key = os.getenv("GOOGLE_CLIENT_SECRET_KEY") 

Ocr_DocumentProcess_Url = "https://middlewaredocmanagement-agefhxfjafgwgjh8.centralus-01.azurewebsites.net/api/v1/"
Ocr_DocumentProcess_Key = "FEF85438-D360-4BC9-8265-7C0EC9F256C5"

Redis_Host = "RedisJobs.redis.cache.windows.net"
Redis_Port = 6380
Redis_Key = os.getenv("REDIS_KEY") 

Openai_Api_Key_azure_embedded = os.getenv("OPENAI_API_KEY_AZURE_EMBEDDED") 
Openai_url_azure_embedded = "https://jsonembedding.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-05-15"

Azure_Search_Index_Key = os.getenv("AZURE_SEARCH_INDEX_KEY") 
Azure_Search_Index_Url = "https://aisearchshipmentcl.search.windows.net/indexes/brasil-documents-index/docs/index?api-version=2024-03-01-Preview"
Azure_Search_Index_version = "2024-03-01-Preview"
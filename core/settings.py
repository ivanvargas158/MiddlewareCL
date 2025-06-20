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
Azure_Cliente_Secret = Field(validation_alias="Azure_Cliente_Secret")

Outlook_Personal_Refresh_Token_Scopes = ["offline_access", "Mail.ReadWrite", "Mail.Send", "Mail.Read", "User.read"]
Outlook_Business_Refresh_Token_Scopes = "https://graph.microsoft.com/.default"
Outlook_Folder_to_Move_Email = "Processed SV"
Outlook_Folder_to_Move_Spam_Email = "AI Spam Filter"
Outlook_Folder_to_Move_Internal_Emails = "Internal Emails"

Agent_Emails = {}

Openai_Api_Key =  Field(validation_alias="Openai_Api_Key") 
Openai_Base_Url = "https://api.openai.com/v1"
Openai_Base_Model = "gpt-4.1-mini"

Openai_Api_Key_Vision = Field(validation_alias="Openai_Api_Key_Vision") 

Gpt_Trainer_Beaer_Key = Field(validation_alias="Gpt_Trainer_Beaer_Key") 
Gpt_UUID = "8aa67d30b71648a295407f00f916548d"


Gpt_Trainer_Beaer_Key_Category_Classify = Field(validation_alias="Gpt_Trainer_Beaer_Key_Category_Classify")
Gpt_UUID_Category_Classify = "04ebc0b2909f489dbac31dccd74bc3e9"

Cargologik_Username = "amarom245@gmail.com"
Cargologik_Password = "Freightsync1!"
Cargologik_Url = "https://fuzgltest.cargologik.app/api/v2/"

Google_Service_Account_File = f'{Path.cwd()}/shared/jsons/googlesheet_credentials.json'
Google_Sheet_Scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]


Azure_Middleware_InstrumentationKey = "39ebfea2-59f5-403d-a60a-7b0c4cb73d1a"
Error_text_email = "Oops..looks like we need a little more info to move forward"
Max_Tokens_text = 3500 

Filter_Spam_Emails = ':: System Warning :: Notification had no recipients'

Max_Weight_FCL = 170000


Google_Auth_Scopes = ['https://mail.google.com/', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile','https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.labels']
Google_Client_Id:str = Field(validation_alias="Google_Client_Id")
Google_Client_Secret_Key:str =  Field(validation_alias="Google_Client_Secret_Key") 

Ocr_DocumentProcess_Url = "https://docmanagement1-h7dgaretesewcggt.eastus-01.azurewebsites.net/api/v1/"
Ocr_DocumentProcess_Key = "FEF85438-D360-4BC9-8265-7C0EC9F256C5"
from pathlib import Path

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
Azure_Cliente_Secret = "zKm8Q~T4fAjRDLlAlN854mrwklQ4nOoXb7CNdbr0"

Outlook_Personal_Refresh_Token_Scopes = ["offline_access", "Mail.ReadWrite", "Mail.Send", "Mail.Read", "User.read"]
Outlook_Business_Refresh_Token_Scopes = "https://graph.microsoft.com/.default"
Outlook_Folder_to_Move_Email = "Processed SV"
Outlook_Folder_to_Move_Spam_Email = "AI Spam Filter"
Outlook_Folder_to_Move_Internal_Emails = "Internal Emails"

Agent_Emails = {}

Openai_Api_Key = Openai_API_Key = "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"
Openai_Base_Url = "https://api.openai.com/v1"
Openai_Base_Model = "gpt-4.1-mini"

Openai_Api_Key_Vision = "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"

Gpt_Trainer_Beaer_Key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczOTI5NDMzMiwianRpIjoiNDVmYWQwYjctYmY1Yy00Nzg3LTkwODEtM2FmODA0OGRlZGI4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJhcGlfa2V5IjoiNTZiNGRlOTYxYTA3M2I3ZmRlM2NmNmY2ZjY5NGYyN2ZlOGFjNzExN2Q2MTcyOGRmMmExY2ZiOWY2ZmMzZDcwOCJ9LCJuYmYiOjE3MzkyOTQzMzJ9.hJrh4xaKiKDGaoCto_OKkVG27g6j1kxsetN3TrlMNf0"
Gpt_UUID = "8aa67d30b71648a295407f00f916548d"

Gpt_Trainer_Beaer_Key_Format_Error = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MDIzMjA3NSwianRpIjoiNzJlODkxNDQtY2Y2NS00NDRjLTgyZWEtNjU0MGMxNTI5MGE0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJhcGlfa2V5IjoiNDdmMGQ2ODhhZDljMjNiNGM5M2M2MWRkNjYxNzMwNTA1ZTA5ODgxYTBjMTE3NTYzYTRiYTFmNWU4Y2IyZTEyOCJ9LCJuYmYiOjE3NDAyMzIwNzV9.5n9P7p43TKFBS7oEArceY_hW-QaZ98WW04lSMMAk9KU"
Gpt_UUID_Format_Error = "eff609c338d64904a780449a7b83fa82"

Gpt_Trainer_Beaer_Key_Category_Classify = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MDMyODk1NSwianRpIjoiMWU5MmFkMzItZGQ3Yi00M2IzLThiOGMtNTczZDE1NDBmZmFkIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJhcGlfa2V5IjoiYzc5OTIyMzAyNGZiMjNlNGI2NWQ4OTA1ZDFiNWU5YWI1NjVlMjMyODcwNjY3YTI1MTgwOTA4MGM0ZTk5ZmE5ZiJ9LCJuYmYiOjE3NDAzMjg5NTV9.ve9XUf-VfJhh63axB_3ay1mGytjR1h7C-RPc_4gRAM4"
Gpt_UUID_Category_Classify = "04ebc0b2909f489dbac31dccd74bc3e9"

Gpt_Trainer_Beaer_Key_Combine = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MzAxMDM4NCwianRpIjoiNDc2YTU5ZmEtY2ZjYi00MjdmLTgzNWYtNzkwMmI1ODI3MDUwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJhcGlfa2V5IjoiMjAyOGU4OWNmY2NmMzE4NWM4YTFjZThlYjU2YWY0ZWRmNWJkMzhkNDY4MmYzYzZkOWI0YjM4YjY3N2RhYTJlYiJ9LCJuYmYiOjE3NDMwMTAzODR9.fVHV6xZtTh0LLoghnbpSO-LhJ7adB6eJS1hM-2SK2So"
Gpt_UUID_Combine = "b345ade5bd4542a2adf3dd712a145560"

Cargologik_Username = "amarom245@gmail.com"
Cargologik_Password = "Freightsync1!"
Cargologik_Refresh_Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZW5hbnQiOiI2NmEyN2JlNzNhZGNkM2RhMTIzN2Y5MTMiLCJjb21wYW55IjoiNjZhMjdiZTczYWRjZDNkYTEyMzdmOTA3IiwidWlkIjoiNjZhMzA4NTY2OTdhM2FhY2NhNWU4YWYyIiwicm9sZSI6ImFkbWluIiwiZG9taW5pbyI6ImNhcmdvbG9naWsuYXBwIiwidXJsIjoiZnV6Z2x0ZXN0LmNhcmdvbG9naWsuYXBwIiwiY29tcGFueVR5cGUiOiJsc3AiLCJkaXJlY3RvcnlCdWNrZXQiOiJmdXpnbHRlc3QtY2FyZ29sb2dpay1hcHAiLCJjb21wYW55TmFtZSI6IkZVWiBHbG9iYWwgTG9naXN0aWNzIiwiaXNEZW1vIjp0cnVlLCJpYXQiOjE3MjQ2NTg1MTQsImV4cCI6MTcyNTI2MzMxNH0.lFQu4jVrB01rfdMKH0iuos25n5izu--BNJkrRou9svI"
Cargologik_Url = "https://fuzgltest.cargologik.app/api/v2/"

Google_Service_Account_File = f'{Path.cwd()}/shared/jsons/googlesheet_credentials.json'
Google_Sheet_Scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

Exfreight_Username = "mike@synapsevue.ai"
Exfreight_Partner_Id= "2a7ef8a8-e4a3-4933-b3cb-4915e5b5f4b6"
Exfreight_Token = "28bb8b5af18b0b99"
Exfreight_Base_Url="https://exfreight.flipstone.com/"

Azure_Middleware_InstrumentationKey = "39ebfea2-59f5-403d-a60a-7b0c4cb73d1a"
Error_text_email = "Oops..looks like we need a little more info to move forward"
Max_Tokens_text = 3500 

Filter_Spam_Emails = ':: System Warning :: Notification had no recipients'

Max_Weight_FCL = 170000


Google_Auth_Scopes = ['https://mail.google.com/', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
Google_Client_Id:str = "216487988564-rstjpjae627f1i5qrg9ruf6vk1841u3p.apps.googleusercontent.com"
Google_Client_Secret_Key:str = "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"

Ocr_DocumentProcess_Url = "https://docmanagement1-h7dgaretesewcggt.eastus-01.azurewebsites.net/api/v1/"
Ocr_DocumentProcess_Key = "FEF85438-D360-4BC9-8265-7C0EC9F256C5"
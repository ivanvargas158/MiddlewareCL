import threading
from typing import List,Dict 
from rq.job import Job
from schemas.general_dto import UploadedFileDto
from services.background_tasks.task_service  import background_job
from core.redis_app import redis_queue,redis_client
from services.background_tasks.task_service import upload_documents

def handle_upload_documents(files:List[UploadedFileDto],shipment_id:str,email_type:str,token:str,message_id:str,list_documents: list[tuple[str, str, str, bool]],list_doc_response:list[Dict],shipment_id_uuid4:str,shipping_mark:str,country_id:str):
    threading.Thread(target=upload_documents, args=(files,shipment_id,email_type,token,message_id,list_documents,list_doc_response,shipment_id_uuid4,shipping_mark,country_id,)).start()     
    print(f"Queued handle_upload_documents")

def handle_request():
     threading.Thread(target=background_job, args=("1",)).start()     
     print(f"Queued DOC1001 as job")   
    

def get_job(job_id:str):
    job = Job.fetch(job_id, connection=redis_client)
    print("Status:", job.get_status())     # 'finished', 'queued', or 'failed'
    print("Result:", job.result)             # None if failed or not finished
    print("Exception:", job.exc_info)      # Stack trace if failed
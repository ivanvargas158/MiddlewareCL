from typing import Dict,List
from schemas.general_enum import DocumentType
from schemas.general_dto import ProcessedDoc
from .email_service import create_body_html_reponse_documents

def get_isf_doc(ocr_document_result:dict,isf_doc_json:dict):
    if ocr_document_result.get("doc_type_code") == DocumentType.brasil_isf:
        isf_doc_json.clear()
        isf_doc_json.update(ocr_document_result)    



def validate_create_shipment(list_documents: list[tuple[str, str, str, bool]],list_doc_response:list[Dict])->bool:

    doc_invoice = next(
            (doc for doc in list_doc_response if doc.get("doc_type_code") == DocumentType.brasil_commercial_invoice and doc.get("required_coa")==True),
            None
        )    
   
    optional_docs = [doc for doc in list_documents if doc[3] is False]

    list_processed_docs:list[tuple[str,str,str]]=[]
    list_missing_docs:list[tuple[str,str]]=[]

    for id, doc_type, doc_type_code,is_requiered in list_documents:
        match_doc = next(
            (doc for doc in list_doc_response if doc.get("doc_type_code") == doc_type_code),
            None
        )
        if match_doc:
           file_name:str = match_doc.get("file_name","")
           list_processed_docs.append((doc_type,doc_type_code,file_name))
        else:
            list_missing_docs.append((doc_type,doc_type_code,))
    
    if  doc_invoice and doc_invoice.get("required_coa")==True:
        if len(list_documents) == len(list_processed_docs):
            return True
        else:
            return False
    else:
        if len(list_documents)-len(optional_docs) == len(list_processed_docs):
           return True
        else:
           return False
    


def validate_create_shipmentv2(list_documents: list[tuple[str, str, str, bool]],list_doc_response:list[Dict])->bool:

    doc_invoice = next(
            (doc for doc in list_doc_response if doc.get("doc_type_code") == DocumentType.brasil_commercial_invoice and doc.get("required_coa")==True),
            None
        )
    
    doc_isf = next(
            (doc for doc in list_doc_response if doc.get("doc_type_code") == DocumentType.brasil_isf),
            None
        )    
    
    # optional_docs = [doc for doc in list_documents if doc[3] is False]

    # list_processed_docs:list[tuple[str,str,str]]=[]
    # list_missing_docs:list[tuple[str,str]]=[]

    # for id, doc_type, doc_type_code,is_requiered in list_documents:
    #     match_doc = next(
    #         (doc for doc in list_doc_response if doc.get("doc_type_code") == doc_type_code),
    #         None
    #     )
    #     if match_doc:
    #        file_name:str = match_doc.get("file_name","")
    #        list_processed_docs.append((doc_type,doc_type_code,file_name))
    #     else:
    #         list_missing_docs.append((doc_type,doc_type_code,))
    
    if  doc_isf and doc_invoice and doc_invoice.get("required_coa")==True:
        doc_coa = next(
            (doc for doc in list_doc_response if doc.get("doc_type_code") == DocumentType.brasil_certificate_of_analysis),
            None
        )
        if doc_coa:
            return True
        else:
            return True
    elif doc_isf:        
           return True
    else:
           return False
        





def create_response_validate_requiered_documents(list_documents: list[tuple[str, str, str, bool]],list_doc_response:list[Dict],list_docs_unprocessed: List[str],shipment_id:str)->str:

    list_docs:list[ProcessedDoc]=[]
    list_missing_docs:list[str]=[]
    for id, doc_type, doc_type_code,is_requiered in list_documents:
        match_doc = next(
            (doc for doc in list_doc_response if doc.get("doc_type_code") == doc_type_code),
            None
        )
        if match_doc:# File is attached into email
            file_name:str = match_doc.get("file_name","")
            if file_name in list_docs_unprocessed: #Verify if the file uploaded to the new shipment
                list_docs.append(ProcessedDoc(doc_type,doc_type_code,file_name,"Document could not be uploaded to shipment"))    
                list_missing_docs.append(doc_type_code)        
            else:
                list_docs.append(ProcessedDoc(doc_type,doc_type_code,file_name,"Processed"))
        else:
            list_docs.append(ProcessedDoc(doc_type,doc_type_code,"Document not attached into email","Unprocessed")) 
            list_missing_docs.append(doc_type_code)     
    
    return create_body_html_reponse_documents(list_docs,list_missing_docs,shipment_id)
    

    
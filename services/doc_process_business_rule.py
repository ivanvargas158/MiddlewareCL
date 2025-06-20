from typing import Dict
from schemas.general_enum import DocumentType
from .email_service import create_body_html_reponse_documents

def get_isf_doc(ocr_document_result:dict,isf_doc_json:dict):
    if ocr_document_result.get("doc_type") == DocumentType.brasil_isf:
        isf_doc_json.clear()
        isf_doc_json.update(ocr_document_result)    


def validate_requiered_documents(list_documents: list[tuple[str, str, str, bool]],list_doc_response:list[Dict])->tuple[str,bool]:

    doc_invoice = next(
            (doc for doc in list_doc_response if doc.get("doc_type") == DocumentType.brasil_commercial_invoice and doc.get("required_coa")==True),
            None
        )
    
    optional_docs = [doc for doc in list_documents if doc[3] is False]

    list_processed_docs:list[tuple[str,str,str]]=[]
    list_missing_docs:list[tuple[str,str]]=[]

    for id, doc_type, doc_type_code,is_requiered in list_documents:
        match_doc = next(
            (doc for doc in list_doc_response if doc.get("doc_type") == doc_type_code),
            None
        )
        if match_doc:
           file_name:str = match_doc.get("file_name","")
           list_processed_docs.append((doc_type,doc_type_code,file_name))
        else:
            list_missing_docs.append((doc_type,doc_type_code,))
    
    if  doc_invoice and doc_invoice.get("required_coa")==True:
        if len(list_documents) == len(list_processed_docs):
            return create_body_html_reponse_documents(list_processed_docs,list_missing_docs),True
        else:
            return create_body_html_reponse_documents(list_processed_docs,list_missing_docs),False
    else:
        if len(list_documents)-len(optional_docs) == len(list_processed_docs):
           return create_body_html_reponse_documents(list_processed_docs,list_missing_docs),True
        else:
           return create_body_html_reponse_documents(list_processed_docs,list_missing_docs),False
    

    
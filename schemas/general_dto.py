import io
from dataclasses import dataclass

@dataclass
class CreateDocumentDto:
    html: str = ""
    shipment_id: str = ""
    shipment_id_uuid4:str = ""

@dataclass
class ResponseDocumentDto:
    is_related: bool = False
    message: str = ""


@dataclass
class ProcessedDoc:
    doc_type: str
    doc_type_code: str
    file_name: str
    message:str

@dataclass
class UploadedFileDto:
    file_name: str
    file_obj: bytes
    mime_type: str
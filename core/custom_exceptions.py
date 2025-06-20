
class ValidationError(Exception):
    def __init__(self, errors,doc_type=None,ocr_mapped_fields = None):
        self.errors = errors
        self.doc_type = doc_type
        self.ocr_mapped_fields = ocr_mapped_fields or []

        message_parts = [f"Validation failed"]
        if doc_type:
            message_parts.append(f"for document'{doc_type}'")
        if errors:
            message_parts.append(f"{errors}")
        if ocr_mapped_fields:
            message_parts.append(f"[OCR mapped fields: {', '.join(ocr_mapped_fields)}]")
      
        
        message = " ".join(message_parts)
        super().__init__(message)

    def to_dict(self):
        return {
            "errors": self.errors,
            "doc_type": self.doc_type,
            "ocr_mapped_fields": self.ocr_mapped_fields,          
        }

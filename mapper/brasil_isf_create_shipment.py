import json
from utils.global_resources  import clean_payload_structure,remove_empty_fields

def mapping_create_shipment(ocr_document_result,schema_create_shipment:dict)->str:

    payload_create_shipment = clean_payload_structure(schema_create_shipment)

    if ocr_document_result['all_fields']['commodity_description']:
        payload_create_shipment['commodity'] = ocr_document_result['all_fields']['commodity_description']

    if ocr_document_result['all_fields']['seller_name_address']:
        seller_details = ocr_document_result['all_fields']['seller_name_address'].split("\n")
        payload_create_shipment['shipper']['name'] = seller_details[0]
        payload_create_shipment['shipper']['address'] = ", ".join(seller_details[1:])
        payload_create_shipment['origin']['address'] = ", ".join(seller_details[1:])
        payload_create_shipment['origin']['countryCode'] = "BR"  

    if ocr_document_result['all_fields']['buyer_name_address']:
        seller_details = ocr_document_result['all_fields']['buyer_name_address'].split("\n")
        payload_create_shipment['destination']['address'] = ", ".join(seller_details[1:])
        payload_create_shipment['destination']['countryCode'] = "BR"

    if ocr_document_result['all_fields']['consolidator_stuffer']:
        payload_create_shipment['carrier']['name'] =  ocr_document_result['all_fields']['consolidator_stuffer']

    if ocr_document_result['all_fields']['consignee']:
        seller_details = ocr_document_result['all_fields']['consignee'].split("\n")
        payload_create_shipment['consignee']['name'] =  seller_details[0]
        payload_create_shipment['consignee']['address'] = ", ".join(seller_details[1:])

    if ocr_document_result['all_fields']['importer_of_record']:
        payload_create_shipment['internalReference'] =  ocr_document_result['all_fields']['importer_of_record']

    if ocr_document_result['all_fields']['bill_of_lading_number']:
        payload_create_shipment['mbl'] = ocr_document_result['all_fields']['bill_of_lading_number']
    
    if ocr_document_result['all_fields']['etd']:
        payload_create_shipment['etd'] = ocr_document_result['all_fields']['etd']

    if ocr_document_result['all_fields']['eta']:
        payload_create_shipment['eta'] = ocr_document_result['all_fields']['eta']

    payload_create_shipment = remove_empty_fields(payload_create_shipment)
    #if payload_create_shipment:
    return  json.dumps(payload_create_shipment) 
 
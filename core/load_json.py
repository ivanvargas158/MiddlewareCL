import json
from schemas.general_enum import APIAction
from pathlib import Path
schema_files = {
    APIAction.create_shipment: "create_shipment.json",
    APIAction.update_shipment: "update_shipment.json",
}

# Load all schemas into a dictionary at startup
schema_dir = Path.cwd() / "schemas/json_schemas"
loaded_schemas = {}

for doc_type, file_name in schema_files.items():
    file_path = schema_dir / file_name
    try:
        with open(file_path, "r") as file:
            loaded_schemas[doc_type] = json.load(file)
    except FileNotFoundError:
        raise Exception(f"Schema file not found: {file_path}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON in schema file: {file_path}")

def get_json_schema(doc_type: APIAction):
    return loaded_schemas.get(doc_type, "")

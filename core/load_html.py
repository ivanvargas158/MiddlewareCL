import json
from schemas.general_enum import APICargologik_html
from pathlib import Path

html_files = {
    APICargologik_html.create_shipment: "cl_create_shipment.html"
}

# Load all schemas into a dictionary at startup
html_dir = Path.cwd() / "schemas/html/"
loaded_html = {}

for doc_type, file_name in html_files.items():
    file_path = html_dir / file_name
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            loaded_html[doc_type] = file.read()
    except FileNotFoundError:
        raise Exception(f"Schema file not found: {file_path}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON in schema file: {file_path}")

def get_html(doc_type: APICargologik_html):
    return loaded_html.get(doc_type, "")

from pandas_ods_reader import read_ods
import os
import requests
import json
from typing import Dict, List, Tuple, Optional

TABLES_FOLDER = './tables'
COLORS = ["INCOLOR", "VERDE", "FUME"]
CATEGORY = "VIDRO-TEMPERADO"
API_URL = 'http://localhost:8080/verly-service/products'
BEARER_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJtYXR0IiwiZXhwIjoxNzYwNDg1NDM1fQ.QvRNMqr1QYMpezFBb2xC7CW9UN8KJ8e3XyuROZGbTy0-cMdtDyaX8kSW1cx1A003v_b8TM5iw1gK8Kxd1nCn9Q'
FILE_PATTERNS_TO_REMOVE = ["janela_", ".ods", "box_", "porta_", "open", "_4f", "_2f"]


def extract_sheet_name(filename: str) -> int:
    sheets = filename
    for pattern in FILE_PATTERNS_TO_REMOVE:
        sheets = sheets.replace(pattern, "")

    sheets = sheets.upper().replace("_", "").replace("F", "")

    if not sheets or sheets == "BASCULA":
        sheets = "1"

    return int(sheets)


def extract_product_type(filename: str) -> str:
    product_type = filename.replace("_4f.ods", "").replace("_2f.ods", "") \
                          .replace(".ods", "").replace("_open", "").upper()
    return product_type


def swap_dimensions_if_needed(width: str, height: str, product_type: str,
                               sheets: int) -> Tuple[str, str]:
    if product_type in ["PORTA", "JANELA"]:
        return height, width

    return width, height


def parse_dimensions(dimension_string: str) -> Tuple[str, str]:
    width = dimension_string[0:3].replace("x", "")
    height = dimension_string[4:7]
    return width, height


def create_product_dict(category: str, product_type: str, sheets: int,
                       width: str, height: str, color: str) -> Dict:
    product_key = f"{category}-{product_type}-{sheets}-{color}-{width}-{height}"

    return {
        "category": category,
        "type": product_type,
        "sheets": sheets,
        "width": width,
        "height": height,
        "color": color,
        "key": product_key
    }


def post_product_to_api(product: Dict) -> Optional[int]:
    headers = {
        'Content-type': 'application/json',
        'Accept': 'text/plain',
        'Authorization': f'Bearer {BEARER_TOKEN}'
    }

    try:
        response = requests.post(API_URL, data=json.dumps(product), headers=headers)
        print(product)
        print("-" * 50)
        print(f"Status: {response.status_code}")
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error posting product: {e}")
        return None


def process_dimension_value(dimension_value: str, filename: str) -> None:
    sheets = extract_sheet_name(filename)
    product_type = extract_product_type(filename)

    if "bascula" in filename.lower():
        product_type = "JANELA"
        sheets = 1

    width, height = parse_dimensions(dimension_value)

    final_width, final_height = swap_dimensions_if_needed(
        width, height, product_type, sheets
    )

    for color in COLORS:
        product = create_product_dict(
            CATEGORY, product_type, sheets,
            final_width, final_height, color
        )
        post_product_to_api(product)


def read_and_process_file(filename: str) -> None:
    file_path = os.path.join(TABLES_FOLDER, filename)

    try:
        data = read_ods(file_path, columns=["A"])
        data_dict = data.to_dict()

        for column_key in data_dict.keys():
            column_values = data_dict.get(column_key)
            for dimension_value in column_values.values():
                process_dimension_value(dimension_value, filename)

    except Exception as e:
        print(f"Error processing file {filename}: {e}")


def get_ods_files_from_folder(folder_path: str) -> List[str]:
    files = []
    for directory, subdirs, file_list in os.walk(folder_path):
        for file in file_list:
            files.append(file)
    return files


def main():
    print(f"Starting ODS product reader from folder: {TABLES_FOLDER}")
    print(f"Target API: {API_URL}")
    print("-" * 50)

    files = get_ods_files_from_folder(TABLES_FOLDER)

    print(f"Found {len(files)} file(s) to process")
    print("-" * 50)

    for file in files:
        print(f"\nProcessing file: {file}")
        read_and_process_file(file)

    print("\nProcessing complete!")


if __name__ == '__main__':
    main()

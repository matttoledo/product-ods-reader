from pandas_ods_reader import read_ods
import os
import asyncio
import aiohttp
import json
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import time

TABLES_FOLDER = './tables'
COLORS = ["INCOLOR", "VERDE", "FUME"]
CATEGORY = "VIDRO-TEMPERADO"
API_URL = 'https://api.verlyvidracaria.com/verly-service/products'
BEARER_TOKEN = os.getenv('VERLY_API_TOKEN', '')  # Token via environment variable
FILE_PATTERNS_TO_REMOVE = ["janela_", ".ods", "box_", "porta_", "open", "_4f", "_2f"]

# Performance settings
MAX_CONCURRENT_REQUESTS = 50  # Adjust based on your API rate limits
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


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


async def post_product_to_api(session: aiohttp.ClientSession, product: Dict,
                              semaphore: asyncio.Semaphore,
                              progress_bar: tqdm) -> Tuple[Optional[int], Dict]:
    """
    Post product to API with retry logic and concurrency control
    """
    headers = {
        'Content-type': 'application/json',
        'Accept': 'text/plain',
        'Authorization': f'Bearer {BEARER_TOKEN}'
    }

    async with semaphore:  # Limit concurrent requests
        for attempt in range(MAX_RETRIES):
            try:
                async with session.post(
                    API_URL,
                    json=product,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                ) as response:
                    status = response.status

                    if status == 200 or status == 201:
                        progress_bar.update(1)
                        return status, product
                    elif status >= 500:
                        # Server error - retry
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                            continue
                    else:
                        # Client error - don't retry
                        progress_bar.update(1)
                        print(f"\n❌ Error {status} for product: {product['key']}")
                        return status, product

            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    print(f"\n⚠️  Timeout for {product['key']}, retrying ({attempt + 1}/{MAX_RETRIES})...")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    print(f"\n❌ Timeout after {MAX_RETRIES} attempts: {product['key']}")
                    progress_bar.update(1)
                    return None, product

            except aiohttp.ClientError as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"\n⚠️  Connection error for {product['key']}, retrying ({attempt + 1}/{MAX_RETRIES})...")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    print(f"\n❌ Connection error after {MAX_RETRIES} attempts: {product['key']} - {e}")
                    progress_bar.update(1)
                    return None, product

        progress_bar.update(1)
        return None, product


def process_dimension_value(dimension_value: str, filename: str) -> List[Dict]:
    """
    Process a dimension value and return a list of products to post
    """
    sheets = extract_sheet_name(filename)
    product_type = extract_product_type(filename)

    if "bascula" in filename.lower():
        product_type = "JANELA"
        sheets = 1

    width, height = parse_dimensions(dimension_value)

    final_width, final_height = swap_dimensions_if_needed(
        width, height, product_type, sheets
    )

    products = []
    for color in COLORS:
        product = create_product_dict(
            CATEGORY, product_type, sheets,
            final_width, final_height, color
        )
        products.append(product)

    return products


def read_and_process_file(filename: str) -> List[Dict]:
    """
    Read ODS file and extract all products
    """
    file_path = os.path.join(TABLES_FOLDER, filename)
    all_products = []

    try:
        data = read_ods(file_path, columns=["A"])
        data_dict = data.to_dict()

        for column_key in data_dict.keys():
            column_values = data_dict.get(column_key)
            for dimension_value in column_values.values():
                products = process_dimension_value(dimension_value, filename)
                all_products.extend(products)

    except Exception as e:
        print(f"\n❌ Error processing file {filename}: {e}")

    return all_products


def get_ods_files_from_folder(folder_path: str) -> List[str]:
    files = []
    for directory, subdirs, file_list in os.walk(folder_path):
        for file in file_list:
            if file.endswith('.ods'):
                files.append(file)
    return files


async def post_products_batch(products: List[Dict]) -> Tuple[int, int, int]:
    """
    Post all products concurrently with progress bar
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    print(f"\n📤 Posting {len(products)} products to API...")
    print(f"⚙️  Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    print(f"🔗 Target: {API_URL}")
    print("-" * 80)

    async with aiohttp.ClientSession() as session:
        with tqdm(total=len(products), desc="Progress", unit="products") as progress_bar:
            tasks = [
                post_product_to_api(session, product, semaphore, progress_bar)
                for product in products
            ]
            results = await asyncio.gather(*tasks)

    # Analyze results
    success_count = sum(1 for status, _ in results if status in [200, 201])
    error_count = sum(1 for status, _ in results if status and status not in [200, 201])
    failed_count = sum(1 for status, _ in results if status is None)

    return success_count, error_count, failed_count


async def main_async():
    """
    Main async function
    """
    start_time = time.time()

    print("=" * 80)
    print("🚀 ODS Product Reader - Optimized Version")
    print("=" * 80)
    print(f"📁 Reading from folder: {TABLES_FOLDER}")
    print(f"🔑 Token configured: {'✅ Yes' if BEARER_TOKEN else '❌ No (set VERLY_API_TOKEN)'}")
    print("-" * 80)

    if not BEARER_TOKEN:
        print("\n❌ ERROR: BEARER_TOKEN is not set!")
        print("Please set the VERLY_API_TOKEN environment variable")
        print("Example: export VERLY_API_TOKEN='your-token-here'")
        return

    files = get_ods_files_from_folder(TABLES_FOLDER)
    print(f"\n📋 Found {len(files)} ODS file(s) to process")
    print("-" * 80)

    # Read all files and collect products
    all_products = []
    for file in files:
        print(f"📖 Reading file: {file}")
        products = read_and_process_file(file)
        all_products.extend(products)
        print(f"   ✅ Extracted {len(products)} products")

    print(f"\n📊 Total products to post: {len(all_products)}")

    if not all_products:
        print("⚠️  No products found to process")
        return

    # Post all products concurrently
    success, errors, failed = await post_products_batch(all_products)

    elapsed_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 80)
    print("📈 RESULTS SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {success}")
    print(f"⚠️  Errors: {errors}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(all_products)}")
    print(f"⏱️  Time elapsed: {elapsed_time:.2f} seconds")
    print(f"⚡ Average: {len(all_products)/elapsed_time:.1f} products/second")
    print("=" * 80)


def main():
    """
    Entry point - runs async main
    """
    asyncio.run(main_async())


if __name__ == '__main__':
    main()

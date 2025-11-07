# Product ODS Reader - Optimized Version

High-performance ODS file reader that posts products to Verly API with concurrent requests.

## Features

- **Async/Concurrent Requests**: Uses `asyncio` + `aiohttp` for parallel API calls
- **50 concurrent requests** by default (configurable)
- **Automatic retry logic** with exponential backoff
- **Progress bar** with real-time statistics
- **Error handling** and detailed reporting
- **Environment-based configuration**

## Performance Improvements

### Before Optimization:
- Sequential requests (one at a time)
- ~1-2 requests/second
- **Estimated time for 1000 products: 8-16 minutes**

### After Optimization:
- 50 concurrent requests
- **10-50x faster** depending on API response time
- **Estimated time for 1000 products: 15-60 seconds**

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file from the example:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API token:
```bash
VERLY_API_TOKEN=your-actual-token-here
```

## Usage

### Option 1: Using the run script (recommended)
```bash
chmod +x run.sh
./run.sh
```

### Option 2: Direct execution
```bash
export VERLY_API_TOKEN='your-token-here'
python3 main.py
```

### Option 3: Inline token
```bash
VERLY_API_TOKEN='your-token-here' python3 main.py
```

## Performance Tuning

You can adjust these settings in `main.py`:

```python
MAX_CONCURRENT_REQUESTS = 50  # Increase/decrease based on API limits
REQUEST_TIMEOUT = 30          # Seconds before timeout
MAX_RETRIES = 3               # Number of retry attempts
RETRY_DELAY = 1               # Delay between retries (seconds)
```

### Recommendations:
- **50 concurrent requests**: Good for most APIs
- **100+ concurrent requests**: Use if API has high rate limits
- **20-30 concurrent requests**: Use if experiencing timeouts

## API Configuration

- **Endpoint**: `https://api.verlyvidracaria.com/verly-service/products`
- **Method**: `POST`
- **Authentication**: Bearer Token (via `VERLY_API_TOKEN`)
- **Content-Type**: `application/json`

## Output Example

```
================================================================================
🚀 ODS Product Reader - Optimized Version
================================================================================
📁 Reading from folder: ./tables
🔑 Token configured: ✅ Yes
--------------------------------------------------------------------------------

📋 Found 9 ODS file(s) to process
--------------------------------------------------------------------------------
📖 Reading file: bascula.ods
   ✅ Extracted 150 products
📖 Reading file: box_2f.ods
   ✅ Extracted 450 products
...

📊 Total products to post: 1500

📤 Posting 1500 products to API...
⚙️  Max concurrent requests: 50
🔗 Target: https://api.verlyvidracaria.com/verly-service/products
--------------------------------------------------------------------------------
Progress: 100%|███████████████████| 1500/1500 [00:32<00:00, 46.2products/s]

================================================================================
📈 RESULTS SUMMARY
================================================================================
✅ Successful: 1498
⚠️  Errors: 2
❌ Failed: 0
📊 Total: 1500
⏱️  Time elapsed: 32.45 seconds
⚡ Average: 46.2 products/second
================================================================================
```

## Troubleshooting

### "Token is not set" error
Make sure you've set the `VERLY_API_TOKEN` environment variable:
```bash
export VERLY_API_TOKEN='your-token-here'
```

### Connection timeouts
- Reduce `MAX_CONCURRENT_REQUESTS` to 20-30
- Increase `REQUEST_TIMEOUT` to 60
- Check network connectivity to the API

### Too many errors
- Verify the API endpoint is correct
- Check token validity
- Review API rate limits

## Files Structure

```
product-ods-reader/
├── main.py              # Optimized async version
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
├── .env                # Your configuration (gitignored)
├── run.sh              # Convenience script
└── tables/             # ODS files directory
    ├── bascula.ods
    ├── box_2f.ods
    ├── box_4f.ods
    └── ...
```

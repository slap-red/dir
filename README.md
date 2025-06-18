# Dir - Web Scraping Tool

A Python-based web scraping application designed to extract bonus and reward data from websites with authentication support.

## Features

- **Asynchronous Processing**: Built with `asyncio` and `aiohttp` for efficient concurrent requests
- **Authentication Support**: Handles login-protected websites
- **Multiple Output Formats**: Supports both CSV and database output
- **Rate Limiting**: Configurable delays between requests to avoid being blocked
- **Progress Tracking**: Real-time UI updates showing scraping progress
- **Caching**: Optional caching to avoid re-processing URLs
- **Comprehensive Logging**: Detailed logging with configurable levels

## Project Structure

```
dir/
├── main.py              # Main application entry point
├── In/
│   └── config.ini       # Configuration file
├── src/                 # Source code modules
│   ├── acq/            # Data acquisition (API client, authentication)
│   ├── core/           # Core configuration
│   ├── io/             # Input/output handlers
│   ├── log/            # Logging configuration
│   ├── proc/           # Data processing and models
│   └── ui/             # User interface components
├── out/                # Output directory
└── util/               # Utility functions
```

## Configuration

The application is configured through the [`In/config.ini`](In/config.ini) file:

### Authentication
```ini
[auth]
username = your_username    # Login username/mobile number
password = your_password    # Login password
```

### Scraper Settings
```ini
[scraper]
url_list_path = urls.txt           # Path to target URLs file
max_concurrent_requests = 1        # Parallel requests (keep low to avoid bans)
min_request_delay = 1.0           # Minimum delay between requests (seconds)
max_request_delay = 3.0           # Maximum delay between requests (seconds)
```

### Output Options
```ini
[output]
enable_csv_output = true                    # Enable CSV output
csv_output_path = data/bonuses.csv         # CSV output file path
enable_db_output = true                    # Enable database output
db_connection_string = sqlite:///data/bonuses.db  # Database connection string
```

### Logging
```ini
[logging]
log_level = INFO                    # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_file_path = logs/scraper.log   # Log file path
```

### Caching
```ini
[cache]
use_cache = true                        # Enable caching
run_cache_path = cache/run_cache.json  # Cache file path
```

## Usage

1. **Configure the application**: Edit [`In/config.ini`](In/config.ini) with your settings
2. **Prepare URL list**: Create a text file with target URLs (one per line)
3. **Run the scraper**:
   ```bash
   python main.py
   ```

## Requirements

- Python 3.7+
- aiohttp
- asyncio (built-in)
- configparser (built-in)
- logging (built-in)

## Output

The application generates:
- **CSV files**: Structured bonus data in CSV format
- **Database records**: Data stored in SQLite or other databases
- **Log files**: Detailed execution logs for debugging and monitoring

## Rate Limiting

The scraper includes built-in rate limiting to be respectful to target websites:
- Configurable delays between requests
- Request tracking to monitor rate
- Single concurrent request by default (configurable)

## Error Handling

- Comprehensive error logging
- Graceful handling of failed URLs
- Progress tracking with failure counts
- Detailed error messages for debugging
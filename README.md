# Slap Red Scraper v0.5.4

## 1. Project Overview

The Slap Red Scraper is a professional-grade, command-line data intelligence tool engineered in Python. Its primary purpose is to automate the complex process of collecting, processing, and analyzing promotional bonus data from a large number of target websites. This tool is designed for data analysts, market researchers, and developers who require consistent, structured, and insightful data on market trends and promotional strategies.

Version 0.5.4 marks a significant milestone in the project's history, transitioning from a single-file script into a robust, modular Python package. This evolution introduces powerful new features for historical analysis and data archiving while establishing a scalable and maintainable foundation for future development.

---

## 2. Core Features: A Deeper Look

The scraper is built on a foundation of powerful, interconnected features designed for efficiency, deep data analysis, and operational clarity.

* #### **Automated & Robust Scraping Engine**
    The core of the application is its ability to systematically process a list of hundreds of URLs. It handles secure authentication for each site, manages sessions, and is built with robust error handling to gracefully manage network timeouts, server errors, and platform inconsistencies.

* #### **Advanced Data Categorization**
    This is a key intelligence feature. The scraper doesn't just collect raw data; it performs on-the-fly analysis of the complex `claimConfig` JSON string returned by the target API. It dissects this string to extract and flag critical bonus attributes, such as whether a bonus is automatically claimed, restricted to VIPs, or requires a net loss or deposit to activate. This transforms raw, often cryptic, data into structured, immediately useful information.

* #### **Historical Analysis & Archiving**
    New in v0.5.4, the scraper now functions as a true time-series analysis tool. It automatically archives the daily bonus data into a consolidated Excel workbook ([`historical_bonuses.xlsx`](data/historical_bonuses.xlsx)), with each day's results on a separate sheet. Crucially, it then generates a daily [`comparison_report.csv`](data/comparison_report.csv) that provides a differential analysis between the current and previous day's data, explicitly identifying all new, expired ("used"), and persistent bonuses.

* #### **Intelligent Run-over-Run Caching**
    The system maintains a detailed cache ([`run_metrics_cache.json`](cache/run_metrics_cache.json)) that stores vital statistics from every run for each specific site. This intelligent caching is the engine that powers the rich, comparative console display, allowing users to see at a glance how metrics for a site have changed since the last execution.

* #### **Dynamic & Informative Console UI**
    During operation, the scraper presents a rich, 4-line dynamic display in the console that updates in real-time for each site being processed. This UI provides a comprehensive overview of job progress, processing times, run history, and detailed comparative statistics, offering complete operational transparency.

* #### **Comprehensive & Multi-Format Logging**
    All operations are captured in a structured [`bonus.log`](logs/bonus.log) file using the JSON Lines format, which is ideal for programmatic analysis, log aggregation platforms, and deep debugging. Additionally, the tool can be configured via a command-line argument to generate a parallel, human-readable plain text log file for quick reviews.

* #### **Highly Configurable Operation**
    A central [`config.ini`](config.ini) file allows for easy management of user credentials, the target URL list, and logging verbosity. This separation of configuration from code means the tool can be easily adapted to different environments without modifying the source.

* #### **Professional Modular Architecture**
    The entire codebase is structured as a formal Python package. This modular design, with components for services, analysis, configuration, and utilities, follows best practices for software engineering, ensuring the project is scalable, maintainable, and easy for other developers to contribute to.

---

## 3. How It Works: A Technical Deep Dive

The scraper follows a logical, multi-stage process for each run. Understanding this lifecycle is key to leveraging the tool effectively.

1.  **Initialization**: The application starts by loading and validating all settings from [`config.ini`](config.ini). The logging system is configured based on the specified `detail` level, preparing handlers for both JSON and optional text output. The historical [`run_metrics_cache.json`](cache/run_metrics_cache.json) is loaded into memory.

2.  **URL Processing Loop**: The script reads the list of target sites from [`urls.txt`](urls.txt) and begins iterating through them one by one.

3.  **URL Cleaning & Authentication**: For each URL, it is first cleaned to its base domain (e.g., `https://example.com/RF123` becomes `https://example.com`). The `AuthService` then attempts to log in using the provided credentials.

4.  **Data Scraping & Parsing**: Upon a successful login, the `BonusScraper` service is invoked. It makes the API call to fetch bonus data. For each bonus item returned, it performs its main parsing logic, including the advanced analysis of the `claimConfig` string to generate the new categorical fields.

5.  **Data Persistence (Live)**: As bonus data is scraped and parsed, it is immediately appended to the current day's `[YYYY-MM-DD]_bonuses.csv` file. This ensures that data is saved incrementally and is not lost if the script is interrupted.

6.  **Post-Run Analysis**: After the URL loop is complete, the `AnalysisService` takes over.
    * **Excel Archiving**: It reads the newly created daily bonus CSV and archives its contents as a new sheet in [`data/historical_bonuses.xlsx`](data/historical_bonuses.xlsx).
    * **Comparison Reporting**: It then loads today's data and yesterday's data (from the Excel archive) and performs a differential analysis, generating the [`comparison_report_[YYYY-MM-DD].csv`](data/comparison_report.csv) that details all changes.

7.  **Cache Update**: Finally, the script updates the [`run_metrics_cache.json`](cache/run_metrics_cache.json) file with the statistics from the just-completed run and shuts down.

---

## 4. Prerequisites & Installation

1.  **Python**: Python 3.8 or higher is recommended.
2.  **Dependencies**: The project dependencies are listed in [`requirements.txt`](requirements.txt). Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

---

## 5. Setup & Configuration

Place the [`src/`](src/) directory, [`config.ini`](config.ini), [`requirements.txt`](requirements.txt), and [`urls.txt`](urls.txt) files in the same root project directory.

### [`config.ini`](config.ini)

This file is the central control panel for the scraper.

```ini
[credentials]
# Your mobile number and password for site login
mobile = YOUR_MOBILE_NUMBER
password = YOUR_PASSWORD

[settings]
# The name of the file containing URLs to scrape
file = urls.txt
# Set to 'true' to run the downline scraper, 'false' for bonus scraping
downline = false

[logging]
# Path for the primary JSON log file
log_file = logs/bonus.log
# Set to true to see live log output in the console below the UI
console = true
# Controls the verbosity of logging. Options:
# LESS: Shows only WARNING, ERROR, CRITICAL messages.
# MORE: Shows INFO, WARNING, ERROR, CRITICAL messages. (Recommended)
# MAX: Shows DEBUG, INFO, WARNING, ERROR, CRITICAL messages. (Very verbose)
detail = MORE
```

---

## 6. Usage

### Web Interface (Recommended)

The easiest way to use the scraper is through the web interface:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the web application
python run_web_app.py
```

Then open your browser and navigate to `http://localhost:12000`

**Features of the Web Interface:**
- 🔐 Secure login using credentials from [`In/config.ini`](In/config.ini)
- 📁 Upload URL files (TXT or CSV format)
- 📊 Real-time progress tracking with visual progress bar
- 📈 Quick stats dashboard showing file counts and progress
- 📥 Download all output files (CSV, Excel, JSON, logs)
- 🎨 Modern, responsive user interface with status indicators
- ⚡ Auto-refresh during scraping operations
- 🛡️ Secure file handling and validation

### Command Line Interface

Alternatively, run the scraper from the command line:

### Basic Operation

1. **Configure credentials**: Edit [`config.ini`](In/config.ini) with your login credentials
2. **Prepare URL list**: Add target URLs to [`urls.txt`](urls.txt) (one per line)
3. **Run the scraper**:
   ```bash
   python main.py
   ```

### Command Line Options

```bash
# Run with default settings
python main.py

# Enable additional text logging
python main.py --text-log

# Run in downline mode (if supported)
# Set downline = true in config.ini
```

---

## 7. Output Files

The scraper generates several types of output files:

- **Daily CSV files**: `[YYYY-MM-DD]_bonuses.csv` - Raw bonus data for each day
- **Historical archive**: [`data/historical_bonuses.xlsx`](data/historical_bonuses.xlsx) - Consolidated Excel workbook with daily sheets
- **Comparison reports**: [`data/comparison_report_[YYYY-MM-DD].csv`](data/comparison_report.csv) - Daily differential analysis
- **Log files**: [`logs/bonus.log`](logs/bonus.log) - JSON Lines format operational logs
- **Cache files**: [`cache/run_metrics_cache.json`](cache/run_metrics_cache.json) - Performance metrics and statistics

---

## 8. Project Structure

```
slap-red-scraper/
├── main.py                    # Main application entry point
├── web_app.py                 # Flask web interface application
├── run_web_app.py            # Web application launcher script
├── requirements.txt          # Python dependencies
├── In/
│   └── config.ini            # Configuration file
├── src/                      # Source code modules
│   ├── ui/                   # User interface components
│   │   ├── app.py           # Original Flask application
│   │   └── ui.py            # Console UI handler
│   ├── core/                # Core configuration
│   ├── io/                  # Input/output handling
│   ├── log/                 # Logging configuration
│   ├── proc/                # Data processing and models
│   └── acq/                 # Data acquisition (API, auth)
├── data/                     # Output data files
│   ├── historical_bonuses.xlsx  # Excel archive
│   ├── comparison_report_*.csv  # Daily comparison reports
│   └── *.csv                # Daily bonus data files
├── logs/                     # Log files
│   └── bonus.log            # JSON Lines format logs
├── cache/                    # Cache and metrics
│   └── run_metrics_cache.json  # Performance metrics
├── temp/                     # Temporary files
└── util/                     # Utility functions
```

### Key Components

- **`run_webapp.py`**: Launch script for the Flask web interface
- **`src/ui/app.py`**: Complete Flask web application with authentication, file upload, progress tracking, and result downloads
- **`main.py`**: Command-line interface for the scraper
- **`In/config.ini`**: Configuration file with authentication and scraper settings
- **`out/`**: Directory containing all output files (CSV, JSON, database)
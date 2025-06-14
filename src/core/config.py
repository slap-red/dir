# config.py

import configparser
import sys
import os

def get_config(path: str = "config.ini") -> configparser.ConfigParser:
    """
    Loads and validates the config.ini file, ignoring inline comments.
    Exits gracefully if the file or required settings are missing.
    """
    if not os.path.exists(path):
        print(f"FATAL ERROR: Configuration file not found at '{path}'")
        sys.exit(1)

    # Initialize the parser to recognize ; and # as inline comment markers.
    config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
    config.read(path)

    required_settings = {
        "auth": ["username", "password"],
        "scraper": ["url_list_path"],
        "output": ["enable_csv_output", "csv_output_path", "enable_db_output", "db_connection_string"],
        "logging": ["log_level", "log_file_path"],
    }

    for section, keys in required_settings.items():
        if not config.has_section(section):
            print(f"FATAL ERROR: Missing required section '[{section}]' in '{path}'")
            sys.exit(1)
        for key in keys:
            if not config.has_option(section, key):
                print(f"FATAL ERROR: Missing required key '{key}' in section '[{section}]' in '{path}'")
                sys.exit(1)
    
    return config

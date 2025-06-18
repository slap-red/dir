# main.py
import asyncio
import aiohttp
import logging
import configparser
import random
import time
import collections
from typing import List, Deque
from urllib.parse import urlparse, urlunparse

# Re-added api_client to the import list
import io_handler, ui, processing, auth, models, config, logger_config, api_client

async def process_url(url: str, app_config: configparser.ConfigParser, logger: logging.Logger, session: aiohttp.ClientSession, request_tracker: Deque[float]):
    cleaned_url = ""
    try:
        cleaned_url = urlunparse(urlparse(url)._replace(path="", params="", query="", fragment=""))
    except Exception:
        cleaned_url = url

    auth_data = await auth.get_auth(cleaned_url, app_config, logger, session, request_tracker)
    if not auth_data:
        return [], cleaned_url, False, 0

    min_delay = app_config.getfloat('scraper', 'min_request_delay', fallback=1.0)
    max_delay = app_config.getfloat('scraper', 'max_request_delay', fallback=3.0)
    await asyncio.sleep(random.uniform(min_delay, max_delay))

    # Corrected: Call get_bonuses from api_client, not processing
    bonuses_json = await api_client.get_bonuses(auth_data, session, logger)
    if bonuses_json is None:
        return [], cleaned_url, True, 0

    processed_bonuses = processing.process_bonuses(bonuses_json, cleaned_url, auth_data.merchant_name, logger)
    bonus_count = len(processed_bonuses)
    logger.info(f"Successfully processed {cleaned_url} - Found {bonus_count} bonuses.")
    return processed_bonuses, cleaned_url, True, bonus_count

async def main():
    app_config = config.get_config()
    logger = logger_config.setup_logger(app_config)
    
    urls = io_handler.load_urls(app_config.get('scraper', 'url_list_path'), logger)
    
    ui_handler = ui.UIHandler()
    ui_handler.set_total_urls(len(urls))
    
    request_tracker: Deque[float] = collections.deque(maxlen=200)
    all_bonuses = []
    failed_url_count = 0
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            success = False
            bonuses_found = 0
            cleaned_url = url
            try:
                bonuses_list, cleaned_url, success, bonuses_found = await process_url(url.strip(), app_config, logger, session, request_tracker)
                if bonuses_list:
                    all_bonuses.extend(bonuses_list)
            except Exception as e:
                success = False
                failed_url_count += 1
                logger.error(f"A task failed for URL {url.strip()}: {e}")
            
            ui_handler.update_site_progress(cleaned_url, success, bonuses_found, request_tracker)

    if app_config.getboolean('output', 'enable_db_output'):
        db_url = app_config.get('output', 'db_connection_string')
        io_handler.write_bonuses_to_db(all_bonuses, db_url, logger)

    if app_config.getboolean('output', 'enable_csv_output'):
        csv_path = app_config.get('output', 'csv_output_path')
        io_handler.write_bonuses_to_csv(all_bonuses, csv_path, logger)

    ui_handler.print_final_summary(len(all_bonuses), failed_url_count)
    logger.info(f"Scraping complete. Found {len(all_bonuses)} total bonuses. {failed_url_count} URLs failed.")

if __name__ == "__main__":
    asyncio.run(main())

# ui.py

import sys
import time

class UIHandler:
    def __init__(self):
        self.total_urls = 0
        self.processed_count = 0

    def set_total_urls(self, total):
        self.total_urls = total
        print(f"Starting scrape of {total} URLs...")

    def update_site_progress(self, url: str, success: bool, bonus_count: int, request_tracker):
        self.processed_count += 1
        status = "SUCCESS" if success and bonus_count > 0 else "FAIL"
        progress = f"[{self.processed_count}/{self.total_urls}]"
        
        # Print a simple, single line for each update
        print(f"{progress} {status:<8} | Bonuses: {bonus_count:<4} | URL: {url}")

    def print_final_summary(self, total_bonuses_found: int, failed_urls: int):
        print("\n" + "="*40)
        print("Scraping Complete")
        print(f"Total Bonuses Found: {total_bonuses_found}")
        print(f"Successful Sites: {self.processed_count - failed_urls}")
        print(f"Failed Sites: {failed_urls}")
        print("="*40)

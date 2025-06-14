# auth.py

import configparser
import logging
import re
import time
import asyncio
from typing import Optional, Deque
from pydantic import ValidationError
import aiohttp

from models import AuthData

async def get_auth(url: str, config: configparser.ConfigParser, logger: logging.Logger, session: aiohttp.ClientSession, request_tracker: Deque[float]) -> Optional[AuthData]:
    """
    Performs two-step authentication with detailed, specific exception handling.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    request_tracker.append(time.time())

    # Step 1: GET request
    try:
        async with session.get(url, headers=headers, proxy=None, timeout=15, ssl=False) as response:
            response.raise_for_status()
            html = await response.text()
            if not html:
                logger.warning("auth_html_empty", extra={"url": url})
                return None
            match = re.search(r'var MERCHANTID = (\d+);\s*var MERCHANTNAME = ["\'](.*?)["\'];', html, re.IGNORECASE)
            if not match:
                logger.warning("auth_merch_id_fail", extra={"url": url})
                return None
            merchant_id, merchant_name = match.groups()
    except asyncio.TimeoutError:
        logger.error("auth_html_timeout", extra={"url": url})
        return None
    except aiohttp.ClientResponseError as e:
        logger.error("auth_html_http_error", extra={"url": url, "status": e.status, "err": e.message})
        return None
    except aiohttp.ClientConnectorError as e:
        logger.error("auth_html_connection_error", extra={"url": url, "err": str(e)})
        return None

    # Step 2: POST request
    api_url = f"{url}/api/v1/index.php"
    payload = {"module": "/users/login", "mobile": config.get('auth', 'username'), "password": config.get('auth', 'password'), "merchantId": merchant_id}
    
    try:
        async with session.post(api_url, data=payload, headers=headers, proxy=None, timeout=15, ssl=False) as response:
            response.raise_for_status()
            res_json = await response.json()

            if res_json.get("status") != "SUCCESS":
                logger.warning("auth_api_status_fail", extra={"url": api_url, "response": res_json})
                return None
            
            auth_payload = {
                "merchant_id": merchant_id, "merchant_name": merchant_name,
                "access_id": res_json.get("data", {}).get("id"),
                "token": res_json.get("data", {}).get("token"),
                "api_url": api_url
            }
            auth_data = AuthData.model_validate(auth_payload)
            logger.debug("auth_success", extra={"url": url})
            return auth_data
            
    except asyncio.TimeoutError:
        logger.error("auth_api_timeout", extra={"url": api_url})
        return None
    except aiohttp.ClientResponseError as e:
        logger.error("auth_api_http_error", extra={"url": api_url, "status": e.status, "err": e.message})
        return None
    except aiohttp.ClientConnectorError as e:
        logger.error("auth_api_connection_error", extra={"url": api_url, "err": str(e)})
        return None
    except ValidationError as e:
        logger.error("auth_data_validation_error", extra={"url": api_url, "err": str(e)})
        return None

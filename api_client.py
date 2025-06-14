# api_client.py

import aiohttp
import logging
from typing import Optional, List, Dict, Any

from models import AuthData

async def get_bonuses(auth: AuthData, session: aiohttp.ClientSession, logger: logging.Logger) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches bonus data asynchronously.
    """
    payload = {
        "module": "/users/syncData",
        "merchantId": auth.merchant_id,
        "domainId": "0",
        "accessId": auth.access_id,
        "accessToken": auth.token,
        "walletIsAdmin": ""
    }
    
    try:
        async with session.post(auth.api_url, data=payload, proxy=None, timeout=15, ssl=False) as response:
            # ... (rest of the function is unchanged)
            response.raise_for_status()
            res_json = await response.json()
            
            if res_json.get("status") != "SUCCESS":
                logger.warning("api_bonus_status_fail", {"url": auth.api_url, "response": res_json})
                return None
            
            bonus_l = res_json.get("data", {}).get("bonus", [])
            promo_l = res_json.get("data", {}).get("promotions", [])
            raw_data = (bonus_l if isinstance(bonus_l, list) else []) + (promo_l if isinstance(promo_l, list) else [])
            logger.debug("fetch_success", {"url": auth.api_url, "count": len(raw_data)})
            return raw_data
            
    except Exception as e:
        logger.error("fetch_fail", {"url": auth.api_url, "err": str(e)})
        return None
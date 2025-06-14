# processing.py

import json
import logging
from typing import Any, List, Dict

from models import Bonus # <--- Corrected Import

def _parse_float(value: Any) -> float:
    # ... function content is unchanged
    if value is None: return 0.0
    try: return float(value)
    except (ValueError, TypeError): return 0.0

def _create_and_map_bonus(data: Dict[str, Any], url: str, merchant_name: str) -> Bonus:
    bonus_obj = Bonus() # <--- Corrected Class
    bonus_obj.url = url
    bonus_obj.merchant_name = merchant_name
    bonus_obj.id = str(data.get("id", ""))
    bonus_obj.name = str(data.get("name", ""))
    bonus_obj.amount = _parse_float(data.get("amount"))
    bonus_obj.rollover = _parse_float(data.get("rollover"))
    bonus_obj.bonus_fixed = _parse_float(data.get("bonusFixed"))
    bonus_obj.min_withdraw = _parse_float(data.get("minWithdraw"))
    bonus_obj.max_withdraw = _parse_float(data.get("maxWithdraw"))
    bonus_obj.min_topup = _parse_float(data.get("minTopup"))
    bonus_obj.max_topup = _parse_float(data.get("maxTopup"))
    bonus_obj.withdraw_to_bonus_ratio = bonus_obj.min_withdraw / bonus_obj.bonus_fixed if bonus_obj.bonus_fixed != 0 else None
    bonus_obj.transaction_type = str(data.get("transactionType", ""))
    bonus_obj.balance = str(data.get("balance", ""))
    bonus_obj.bonus = str(data.get("bonus", ""))
    bonus_obj.bonus_random = str(data.get("bonusRandom", ""))
    bonus_obj.reset = str(data.get("reset", ""))
    bonus_obj.refer_link = str(data.get("referLink", ""))
    bonus_obj.raw_claim_config = data.get("claimConfig", "")
    bonus_obj.raw_claim_condition = data.get("claimCondition", "")
    return bonus_obj

def _parse_claim_config(bonus_obj: Bonus, logger: logging.Logger) -> Bonus:
    # ... function content is unchanged
    raw_config = bonus_obj.raw_claim_config
    if not isinstance(raw_config, str) or not raw_config.startswith('['): return bonus_obj
    try:
        config_list = json.loads(raw_config)
        if not isinstance(config_list, list): return bonus_obj
        for item in config_list:
            if not isinstance(item, str): continue
            item_upper = item.upper()
            if "AUTO_CLAIM" in item_upper: bonus_obj.is_auto_claim = True
            if "VIP" in item_upper: bonus_obj.is_vip_only = True
            if "DEPOSIT" in item_upper: bonus_obj.claim_type = "DEPOSIT"
            if "RESCUE" in item_upper: bonus_obj.claim_type = "RESCUE"
            if "REBATE" in item_upper: bonus_obj.claim_type = "REBATE"
            if "LOSS" in item_upper:
                bonus_obj.has_loss_requirement = True
                parts = item.split('_')
                if len(parts) > 1:
                    val_str = parts[-1].replace('%', '')
                    if '%' in parts[-1]: bonus_obj.loss_req_percent = _parse_float(val_str)
                    else: bonus_obj.loss_req_amount = _parse_float(val_str)
            if "TOPUP" in item_upper:
                bonus_obj.has_topup_requirement = True
                parts = item.split('_')
                if len(parts) > 1: bonus_obj.topup_req_amount = _parse_float(parts[-1])
    except json.JSONDecodeError:
        logger.debug("claim_config_parse_fail", {"config": raw_config, "bonus_id": bonus_obj.id})
    return bonus_obj

def process_bonuses(bonuses_json: List[Dict[str, Any]], url: str, merchant_name: str, logger: logging.Logger) -> List[Bonus]:
    processed_list = []
    for bonus_data in bonuses_json:
        if not isinstance(bonus_data, dict):
            continue
        bonus_obj = _create_and_map_bonus(bonus_data, url, merchant_name)
        fully_processed_bonus = _parse_claim_config(bonus_obj, logger)
        processed_list.append(fully_processed_bonus)
    return processed_list

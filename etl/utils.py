# Các hàm dùng chung: config, logging, helpers
from pathlib import Path
import logging
import json
import os
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
    

def get_env_variable(var_name):
    env_path = BASE_DIR / ".env"
    load_dotenv(dotenv_path=env_path)
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Environment variable '{var_name}' is not set in {env_path}!")
    return value


def load_json(file_path):
    path = BASE_DIR / file_path
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    path = BASE_DIR / file_path
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def setup_logger(name="pipeline"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(BASE_DIR / "logs" / "pipeline.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)


logger = setup_logger("http")
RETRYABLE_STATUS_CODES = (500, 502, 503, 504)


def request_with_retry(url, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            wait_time = 2 ** attempt
            logger.warning(f"Attempt {attempt + 1}/{max_retries} network error ({e}). Retrying in {wait_time}s...")
            time.sleep(wait_time)
            continue

        if response.status_code == 200:
            return response

        if response.status_code in RETRYABLE_STATUS_CODES:
            wait_time = 2 ** attempt
            logger.warning(f"Attempt {attempt + 1}/{max_retries} got status {response.status_code}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            continue

        return response

    logger.error(f"Giving up after {max_retries} attempts: {url}")
    return None


def get_channel_id(ids_data, batch_size=50):
    if isinstance(ids_data, dict):
        ids_data = [cid for cid in ids_data.values() if cid]
    
    channel_ids = []
    for i in range(0, len(ids_data), batch_size):
        batch = ids_data[i:i + batch_size]
        channel_ids.append(",".join(batch))
    return channel_ids


def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


get_ingest_date = today_str
get_extracted_at = now_iso



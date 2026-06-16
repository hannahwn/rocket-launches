"""Main pipeline: fetch, validate, store."""

import logging
import os
import sys

from dotenv.main import logger
import pandas as pd
from pydantic import ValidationError
import requests
from dotenv import load_dotenv

from src.models import RocketLaunch
from src.storage import insert_readings, upload_raw_json

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("azure").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

load_dotenv()


def fetch_data() -> list[dict]:
    """Fetch data from your API. Replace this with your own logic."""
    # TODO: Replace with your API call
    # Example using requests:
    #   response = requests.get("https://api.open-meteo.com/v1/forecast?...")
    #   response.raise_for_status()
    #   return response.json()["hourly"]
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming"

    try:
        logger.info("Fetching data from SpaceDev API...")

        response = requests.get(
            url,
            params={"limit": 10, "format": "json"},
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        logger.info(f"Successfully fetched {len(results)} rocket launches")
        return results

    except requests.exceptions.ConnectionError:
        logger.error(
            "ConnectionError: Cannot connect to the API (no internet or API down)"
        )
        return []

    except requests.JSONDecodeError:
        logger.error("JSONDecodeError: API did not return valid JSON")
        return []

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []

    except Exception as e:
        logger.error(f"Unexpected error while fetching data: {e}")
        return []


def validate(raw_records: list[dict]) -> list[RocketLaunch]:
    """Validate raw records using Pydantic models."""
    valid = []
    for record in raw_records:
        try:
            launch = RocketLaunch.from_api_response(record)
            valid.append(launch)
        except ValidationError as e:
            log.warning("Skipping invalid record: %s", e)
    log.info("Validated %d / %d records", len(valid), len(raw_records))
    return valid


def transform(readings: list[RocketLaunch]) -> pd.DataFrame:
    """Convert validated records to a DataFrame and apply transformations.

    This is where pandas earns its place. Replace the examples below with
    transformations that make sense for your data.
    """
    df = pd.DataFrame([r.model_dump() for r in readings])

    # TODO: Replace these with your own transformations. Examples:
    #
    # Parse timestamp strings into proper datetime objects:
    #   df["timestamp"] = pd.to_datetime(df["timestamp"])
    #
    # Derive a new column from existing data:
    #   df["temp_fahrenheit"] = df["temperature"] * 9 / 5 + 32
    #
    # Drop rows where a required field is missing:
    #   df = df.dropna(subset=["temperature"])
    #
    # Rename columns to match your Postgres table:
    #   df = df.rename(columns={"timestamp": "recorded_at"})

    # 1. Drop duplicates
    df = df.drop_duplicates(subset=["id"])

    # 2. Normalize text
    df["name"] = df["name"].str.strip().str.title()
    df["provider_name"] = df["provider_name"].str.strip()
    df["location"] = df["location"].str.strip()

    # 3. Fill missing values
    df["mission_name"] = df["mission_name"].fillna("Unknown")
    df["mission_type"] = df["mission_type"].fillna("Unknown")
    df["orbit"] = df["orbit"].fillna("Unknown")

    # Remove launches with unknown payload
    df = df[~df["name"].str.contains("Unknown Payload", case=False, na=False)]

    # 4. Drop rows where critical fields are missing
    df = df.dropna(subset=["rocket_name", "provider_name"])

    log.info("Transformed %d rows", len(df))
    return df


def run():
    """Run the full pipeline: fetch -> validate -> transform -> store."""
    log.info("Pipeline starting")

    raw = fetch_data()
    readings = validate(raw)

    if not readings:
        log.error("No valid records to store")
        sys.exit(1)

    df = transform(readings)
    insert_readings(df)
    upload_raw_json(raw)

    log.info("Pipeline finished: %d records stored", len(df))


if __name__ == "__main__":
    # Fail fast if required env vars are missing
    for var in ["POSTGRES_URL", "AZURE_STORAGE_CONNECTION_STRING"]:
        if var not in os.environ:
            log.error("Missing required environment variable: %s", var)
            sys.exit(1)

    run()

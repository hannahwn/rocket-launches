"""Storage functions for Postgres and Blob Storage."""

import json
import logging
import os
from contextlib import closing
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

log = logging.getLogger(__name__)


def insert_readings(df: pd.DataFrame) -> None:
    """Insert a DataFrame of readings into Postgres.

    Creates the table in your personal schema (DB_SCHEMA env var, e.g. dev_alice).
    All CREATE TABLE and INSERT statements run inside that schema so your tables
    never collide with other students on the shared server.
    """
    db_url = os.environ["POSTGRES_URL"]
    schema = os.environ.get("DB_SCHEMA", "public")

    with closing(psycopg2.connect(db_url)) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE SCHEMA IF NOT EXISTS {schema}"  # noqa: S608
            )
            cur.execute(f"SET search_path TO {schema}")  # noqa: S608

            cur.execute("""
                CREATE TABLE IF NOT EXISTS rocket_launches (
                     id TEXT PRIMARY KEY,
                    name TEXT,
                    launch_date TIMESTAMPTZ,
                    launch_status TEXT,
                    rocket_name TEXT,
                    mission_name TEXT,
                    mission_type TEXT,
                    orbit TEXT,
                    provider_name TEXT,
                    provider_type TEXT,
                    pad_name TEXT,
                    location TEXT
                )
            """)

            for _, row in df.iterrows():
                launch_date = (
                    row["launch_date"] if pd.notna(row["launch_date"]) else None
                )
                cur.execute(
                    "INSERT INTO rocket_launches (id, name, launch_date, launch_status, rocket_name, mission_name, mission_type, orbit, provider_name, provider_type, pad_name, location)"
                    " VALUES (%s,%s,%s, %s, %s, %s, %s, %s, %s, %s,%s,%s)"
                    " ON CONFLICT (id) DO UPDATE SET"
                    " launch_status = EXCLUDED.launch_status,"
                    " launch_date = EXCLUDED.launch_date",
                    (
                        row["id"],
                        row["name"],
                        launch_date,
                        row["launch_status"],
                        row["rocket_name"],
                        row["mission_name"],
                        row["mission_type"],
                        row["orbit"],
                        row["provider_name"],
                        row["provider_type"],
                        row["pad_name"],
                        row["location"],
                    ),
                )

        conn.commit()

    log.info("Inserted %d rows into %s.rocket_launches", len(df), schema)


def insert_provider_summary(df: pd.DataFrame) -> None:
    """Create and insert provider summary table."""
    db_url = os.environ["POSTGRES_URL"]
    schema = os.environ.get("DB_SCHEMA", "public")

    summary = (
        df.groupby(["provider_name", "provider_type"])
        .agg(launch_count=("id", "count"))
        .reset_index()
    )

    with closing(psycopg2.connect(db_url)) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {schema}")  # noqa: S608

            cur.execute("""
                CREATE TABLE IF NOT EXISTS launch_providers (
                    provider_name TEXT,
                    provider_type TEXT,
                    launch_count INTEGER,
                    PRIMARY KEY (provider_name, provider_type)
                )
            """)
            for _, row in summary.iterrows():
                cur.execute(
                    """
                    INSERT INTO launch_providers
                    (provider_name, provider_type, launch_count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (provider_name, provider_type)
                    DO UPDATE SET launch_count = EXCLUDED.launch_count
                    """,
                    (
                        row["provider_name"],
                        row["provider_type"],
                        row["launch_count"],
                    ),
                )
        conn.commit()
    log.info("Inserted %d rows into launch_providers", len(summary))


def upload_raw_json(raw_data: list[dict]) -> None:
    """Upload raw API response to Blob Storage as a JSON backup."""
    conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    client = BlobServiceClient.from_connection_string(conn_str)
    container = client.get_container_client("raw")
    try:
        container.create_container()
    except ResourceExistsError:
        pass

    blob_name = (
        f"pipeline/{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')}.json"
    )
    container.upload_blob(
        name=blob_name,
        data=json.dumps(raw_data).encode("utf-8"),
        overwrite=True,
    )
    log.info("Uploaded raw data to blob: %s", blob_name)
import os
from google.cloud import storage, bigquery
from fastapi import UploadFile, File, Form, BackgroundTasks, HTTPException, status
import datetime as dt
from dotenv import load_dotenv

load_dotenv()

def _lazy_clients() -> tuple[storage.Client, bigquery.Client]:
    global storage_client, bq_client
    if storage_client is None:
        storage_client = storage.Client(project=os.environ["GCS_PROJECT_ID"])
    if bq_client is None:
        bq_client = bigquery.Client(project=os.environ["GCS_PROJECT_ID"])
    return storage_client, bq_client

def _upload_to_gcs(file: UploadFile, blob_name: str) -> str:
    """Upload bytes to GCS and return signed URL."""
    storage_client, _ = _lazy_clients()
    bucket = storage_client.bucket(os.environ["GCS_BUCKET"])
    blob = bucket.blob(blob_name)

    # stream upload
    blob.upload_from_file(file.file, content_type=file.content_type)

    url = blob.generate_signed_url(
        expiration=dt.timedelta(seconds=os.environ["SIGNED_URL_TTL"]),
        version="v4",
        method="GET",
    )
    return url

def _insert_row(metadata: dict[str, str | float | None]):
    """Insert row into BigQuery table"""
    _, bq = _lazy_clients()
    table_ref = f"{os.environ["GCS_PROJECT_ID"]}.{os.environ["BQ_DATASET"]}.{os.environ["BQ_TABLE"]}"
    errors = bq.insert_rows_json(table_ref, [metadata])
    if errors:
        raise RuntimeError(f"BigQuery insertion failed: {errors}")

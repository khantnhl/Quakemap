import os, json, base64
from google.cloud import storage, bigquery
from fastapi import UploadFile
import datetime as dt
from dotenv import load_dotenv
from google.oauth2 import service_account
from typing import Union

load_dotenv() 

storage_client=None
bq_client=None

def lazy_clients() -> tuple[storage.Client, bigquery.Client]:
    global storage_client, bq_client

    if storage_client is None or bq_client is None:
        
        creds_b64 = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not creds_b64:
            raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON env var")

        creds_info = json.loads(base64.b64decode(creds_b64))
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        if storage_client is None:
            storage_client = storage.Client(project=os.environ["GCS_PROJECT_ID"],credentials=credentials)
        if bq_client is None:
            bq_client = bigquery.Client(project=os.environ["GCS_PROJECT_ID"], credentials=credentials)
    return storage_client, bq_client

def upload_to_gcs(file: Union[str, UploadFile], bucketname = "earthquake_bukt", blob_name: str="placeholder") -> str:
    """Upload bytes to GCS and return signed URL."""
    
    storage_client, _ = lazy_clients()
    
    bucket = storage_client.bucket(bucketname)
    blob = bucket.blob(blob_name)

    # stream upload
    if isinstance(file, str):
        with open(file, "rb") as f:
            blob.upload_from_file(f, content_type="image/png")
    else:
        blob.upload_from_file(file.file, content_type=file.content_type)

    url = blob.generate_signed_url(
        expiration=dt.timedelta(seconds= int(os.environ["SIGNED_URL_TTL"])),
        version="v4",
        method="GET",
    )
    return url

def insert_row(metadata: dict[str, str | float | None]):
    """Insert row into BigQuery table"""
    _, bq = lazy_clients()

    table_ref = f"{os.environ["GCS_PROJECT_ID"]}.{os.environ["BQ_DATASET"]}.{os.environ["BQ_TABLE"]}"
    errors = bq.insert_rows_json(table_ref, [metadata])
    if errors:
        raise RuntimeError(f"BigQuery insertion failed: {errors}")

def insert_analysis(formData : dict):
    """Insert row into BigQuery table"""
    _, bq = lazy_clients()

    table_ref = f"{os.environ["GCS_PROJECT_ID"]}.{os.environ["BQ_DATASET"]}.map_store"
    errors = bq.insert_rows_json(table_ref, [formData])
    if errors:
        raise RuntimeError(f"BigQuery insertion failed: {errors}")

    return

def fetch_from_db(blob_name):
    query = f"""
        SELECT blob_name, mmi_estimation, confidence, map_url, reasoning
        FROM `{os.environ["GCS_PROJECT_ID"]}.{os.environ["BQ_DATASET"]}.map_store`
        WHERE blob_name=@blob_name
        LIMIT 1
    """
    _, bq = lazy_clients()  
    
    job_config = bigquery.QueryJobConfig(
    
    query_parameters=[
            bigquery.ScalarQueryParameter("blob_name", "STRING", blob_name)
        ]
    )

    result = bq.query(query, job_config=job_config).result()
    row = next(result, None)

    if row:
        return {
            "blob_name": row.blob_name,
            "mmi_estimation": row.mmi_estimation,
            "confidence": row.confidence,
            "map_url": row.map_url,
            "reasoning": row.reasoning
        }
    return None




   
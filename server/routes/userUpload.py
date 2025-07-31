from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, status
import uuid, datetime as dt

from services.utilities import _upload_to_gcs, _insert_row

router_upload = APIRouter()

@router_upload.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file : UploadFile = File(description="jpeg, png, pdf, mp4")):
    """
        upload to GCS 
    """
    if file.content_type not in {"image/jpeg", "image/png", "application/pdf", "video/mp4"}:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    blob_name = f"{uuid.uuid4()}_{file.filename}"
    signed_url = _upload_to_gcs(file, blob_name)

    _insert_row({
        "blob_name": blob_name,
        "signed_url": signed_url,
        "location": None,
        "mmi": None,
        "lat": None,
        "lon": None,
        "shakemap_url": None,
        "timestamp": dt.datetime.now().isoformat(),
    })

    return {
        "blob_name": blob_name,
        "signed_url": signed_url,
        "message": "Upload successful"
    }
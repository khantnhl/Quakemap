from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, status

from services.generateMap import generate_gmt_script
from services.utilities import upload_to_gcs, insert_row, insert_analysis, fetch_from_db
from services.crag import MultimodalEarthquakeCRAG
import subprocess

router_upload = APIRouter()
quake_CRAG = MultimodalEarthquakeCRAG()

def analyze_blob(blob_name: str, signed_url: str, mime_type: str):
    result = quake_CRAG.analyze_media_and_traverse_states(
        blob_name=blob_name,
        signed_url=signed_url,
        mime_type=mime_type
    )

    # save sample to see
    with open("sample_test.txt", 'w') as f:
        f.write(result["generation"])

    if(not result["final_analysis"]["location"]["coordinates"]):
        raise ValueError("Invalid Location")
    
    lat = result["final_analysis"]["location"]["coordinates"][0]
    lon = result["final_analysis"]["location"]["coordinates"][1]
    mmi = result["final_analysis"]["mmi_estimation"]

    # add point to map
    with open("./assets/records.txt", "a") as f:
        f.write(f"{lon} {lat} {mmi}\n")

    # run gmt again to generate map
    try:
        subprocess.run(["./assets/plot.sh"])
    except subprocess.CalledProcessError as e:
        print("gmt failed: ", e)

    map_url = upload_to_gcs("./assets/mmi_mandalay_map.png", "earthquake_bukt", "mmi_mandalay_map.png")

    insert_analysis({
        "blob_name": blob_name,
        "mmi_estimation": result["final_analysis"]["mmi_estimation"],
        "confidence": result["final_analysis"]["confidence"],
        "map_url": map_url,
        "reasoning" : result["final_analysis"]["reasoning"]
    })

    print("Status: inserted analysis to BigQ")

@router_upload.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    background_tasks: BackgroundTasks,
    file : UploadFile = File(description="jpeg, png, pdf, mp4")):
    """
        upload to GCS 
    """
    if file.content_type not in {"image/jpeg", "image/png", "application/pdf", "video/mp4"}:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    blob_name = f"{file.filename}"
    
    signed_url = upload_to_gcs(file, bucketname="earthquake_bukt", blob_name=blob_name)

    insert_row({
        "blob_name": blob_name,
        "signed_url": signed_url,
    })


    background_tasks.add_task(analyze_blob, blob_name, signed_url, file.content_type)

    return {
        "blob_name": blob_name,
        "signed_url": signed_url,
        "message": "Upload successful"
    }

@router_upload.get("/result/{blob_name}")
def get_analysis(blob_name : str):
    
    result = fetch_from_db(blob_name)  

    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not ready yet")

    return result
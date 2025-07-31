from pydantic import BaseModel, Field
from typing import List, Optional

class Location(BaseModel):
    address : str
    coordinates : List[float] # lat, lon

class responseModel(BaseModel):
    blob_name: str
    description: str
    location: Location
    auditory_cues: str
    background_noise: str
    sounds_of_distress: str
    visual_observation: str
    video_evidence: str
    building_type: str
    building_materials: str
    evidence_analysis: str
    context_summary: str
    mmi_estimation: float = Field(..., ge=0.0, le=10.0)
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)
import os, json
import asyncio
from typing import Tuple
from dotenv import load_dotenv
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel, Part
from vertexai.generative_models import GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold
from google.cloud import aiplatform
load_dotenv()

geminiConfig= GenerationConfig(
        temperature=0.4,
        top_p=0.95,
        top_k=20,
        candidate_count=1,
        seed=5,
        max_output_tokens=8100,
        stop_sequences=["STOP!"],
        presence_penalty=0.0,
        frequency_penalty=0.0,
        response_logprobs=False,  # Set to True to get logprobs, Note this can only be run once per day
        response_mime_type="application/json"
    )

sf_settings = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    )
]

# One-time model + init instance
aiplatform.init(project=os.environ["GCS_PROJECT_ID"], location=os.environ["GCS_REGION"])
gemini_model = GenerativeModel("gemini-2.5-flash")

async def get_mmi_from_gemini(signed_url: str, location: str) -> Tuple[float, float, float]:
    """
    Calls Gemini with signed GCS URL + location prompt.
    Returns: (lon, lat, mmi)
    """
    prompt = (
        "You are an expert seismologist. Given an image/video at the signed URL and the location, "
        "infer a single, numeric Modified Mercalli Intensity (MMI) value (0‑12). "
        "Return JSON: {\"lon\": <float>}, \"lat\": <float>, \"mmi\": <float>}"
    )

    # Run in a thread since Vertex SDK is blocking
    response = await asyncio.to_thread(
        gemini_model.generate_content,
        [prompt, Part.from_uri(signed_url, mime_type="application/octet-stream")],
        generation_config=geminiConfig,
        safety_settings=sf_settings
    )

    try:
        data = json.loads(response.text)
        return float(data["lon"]), float(data["lat"]), float(data["mmi"])
    except Exception as e:
        raise ValueError(f"Invalid Gemini response: {response.text}") from e

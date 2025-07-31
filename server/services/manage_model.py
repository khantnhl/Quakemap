import vertexai
import os
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, HarmBlockThreshold, HarmCategory, GenerationConfig
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from functools import lru_cache

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

@lru_cache
def get_model():
        return GenerativeModel("gemini-2.5-flash")

def get_response(contents: list):
    model = get_model()
    response = model.generate_content(
                    generation_config=geminiConfig, 
                    safety_settings=sf_settings, 
                    contents=contents,    
                    stream=False
                    )
        
    return response.text

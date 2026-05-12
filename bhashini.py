"""
services/bhashini.py
Bhashini (MeitY) — Government-grade Indian language translation.
Covers 22+ Indic languages. Unlimited for education use.
Apply for API access at: bhashini.gov.in

Falls back gracefully if keys are not configured (Gemini handles translation then).
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")

# Bhashini language codes mapped to BCP-47 / ISO 639 codes used elsewhere
BHASHINI_LANG_MAP = {
    "hi": "hi",   # Hindi
    "mr": "mr",   # Marathi
    "kn": "kn",   # Kannada
    "ta": "ta",   # Tamil
    "te": "te",   # Telugu
    "bn": "bn",   # Bengali
    "gu": "gu",   # Gujarati
    "pa": "pa",   # Punjabi
    "ml": "ml",   # Malayalam
    "or": "or",   # Odia
    "as": "as",   # Assamese
    "ur": "ur",   # Urdu
    "sa": "sa",   # Sanskrit
    "en": "en",   # English
}

_PIPELINE_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
_INFERENCE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"


def is_configured() -> bool:
    return bool(BHASHINI_API_KEY and BHASHINI_USER_ID)


async def translate(text: str, source_lang: str = "en", target_lang: str = "hi") -> str:
    """
    Translate text using Bhashini pipeline API.
    Returns translated string, or raises httpx.HTTPError on failure.
    """
    if not is_configured():
        raise RuntimeError(
            "Bhashini is not configured. "
            "Apply at bhashini.gov.in and add BHASHINI_API_KEY + BHASHINI_USER_ID to .env."
        )

    headers = {
        "userID": BHASHINI_USER_ID,
        "ulcaApiKey": BHASHINI_API_KEY,
        "Content-Type": "application/json",
    }

    # Step 1: Get pipeline config
    pipeline_payload = {
        "pipelineTasks": [{"taskType": "translation", "config": {"language": {"sourceLanguage": source_lang, "targetLanguage": target_lang}}}],
        "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"},
    }

    async with httpx.AsyncClient(timeout=15) as client:
        pipeline_resp = await client.post(_PIPELINE_URL, json=pipeline_payload, headers=headers)
        pipeline_resp.raise_for_status()
        pipeline_data = pipeline_resp.json()

        # Extract callback URL and service ID from pipeline config
        pipeline_response_config = pipeline_data.get("pipelineResponseConfig", [])
        if not pipeline_response_config:
            raise ValueError("No pipeline config returned from Bhashini.")

        task_config = pipeline_response_config[0]
        config = task_config.get("config", [{}])[0]
        service_id = config.get("serviceId", "")
        callback_url = pipeline_data.get("pipelineInferenceAPIEndPoint", {}).get(
            "callbackUrl", _INFERENCE_URL
        )
        inference_key_name = pipeline_data.get("pipelineInferenceAPIEndPoint", {}).get(
            "inferenceApiKey", {}
        ).get("name", "Authorization")
        inference_key_value = pipeline_data.get("pipelineInferenceAPIEndPoint", {}).get(
            "inferenceApiKey", {}
        ).get("value", "")

        # Step 2: Run inference
        inference_headers = {
            inference_key_name: inference_key_value,
            "Content-Type": "application/json",
        }
        inference_payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {"sourceLanguage": source_lang, "targetLanguage": target_lang},
                        "serviceId": service_id,
                    },
                }
            ],
            "inputData": {"input": [{"source": text}]},
        }

        infer_resp = await client.post(callback_url, json=inference_payload, headers=inference_headers)
        infer_resp.raise_for_status()
        infer_data = infer_resp.json()

        # Extract translated text
        output = (
            infer_data.get("pipelineResponse", [{}])[0]
            .get("output", [{}])[0]
            .get("target", "")
        )
        return output

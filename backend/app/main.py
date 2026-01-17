"""Main FastAPI application for multi-model translation service."""
import time
import asyncio
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.config import config_manager
from app.models import (
    TranslationRequest,
    TranslationResponse,
    TranslationResult,
    HealthResponse
)
from app.services.translator import translator_service
from app.services.evaluator import get_evaluator


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Model Translation API",
    description="Translation service using multiple AI models with automatic quality selection",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_manager.settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Multi-Model Translation API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and available models."""
    models = config_manager.get_enabled_models()
    model_names = [m.name for m in models]

    # Check Ollama connection
    ollama_connected = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config_manager.settings.ollama_base_url}/api/tags")
            ollama_connected = response.status_code == 200
    except Exception as e:
        print(f"Ollama health check failed: {e}")

    return HealthResponse(
        status="healthy",
        models_available=model_names,
        ollama_connected=ollama_connected
    )


@app.post("/translate", response_model=TranslationResponse, tags=["Translation"])
async def translate(request: TranslationRequest):
    """
    Translate text from English or Traditional Chinese to Russian and Kazakh.

    This endpoint:
    1. Validates the source language
    2. Sends the text to all enabled models
    3. Receives multiple translations for each target language
    4. Evaluates and selects the best translation for each language
    5. Returns the best translations along with all alternatives
    """
    start_time = time.time()

    # Validate source language
    if request.source_language not in ['en', 'zh-TW']:
        raise HTTPException(
            status_code=400,
            detail="Source language must be 'en' (English) or 'zh-TW' (Traditional Chinese)"
        )

    # Get enabled models
    models = config_manager.get_enabled_models()

    if not models:
        raise HTTPException(
            status_code=503,
            detail="No translation models are currently enabled"
        )

    # Get translation configs for target languages
    russian_config = config_manager.get_translation_config('ru')
    kazakh_config = config_manager.get_translation_config('kk')

    # Create evaluator
    evaluator = get_evaluator(
        method=config_manager.settings.evaluation_method,
        threshold=config_manager.settings.consensus_threshold
    )

    try:
        # Translate to both languages concurrently
        russian_translations_task = translator_service.translate_with_all_models(
            models=models,
            text=request.text,
            source_lang=request.source_language,
            target_lang='ru',
            config=russian_config
        )

        kazakh_translations_task = translator_service.translate_with_all_models(
            models=models,
            text=request.text,
            source_lang=request.source_language,
            target_lang='kk',
            config=kazakh_config
        )

        # Wait for both to complete
        russian_translations, kazakh_translations = await asyncio.gather(
            russian_translations_task,
            kazakh_translations_task
        )

        # Check if we got any translations
        if not russian_translations:
            raise HTTPException(
                status_code=503,
                detail="All models failed to translate to Russian"
            )

        if not kazakh_translations:
            raise HTTPException(
                status_code=503,
                detail="All models failed to translate to Kazakh"
            )

        # Evaluate and select best translations
        model_weights = {m.name: m.weight for m in models}

        best_russian, russian_confidence = evaluator.evaluate(
            russian_translations,
            model_weights
        )

        best_kazakh, kazakh_confidence = evaluator.evaluate(
            kazakh_translations,
            model_weights
        )

        # Calculate total processing time
        total_time = time.time() - start_time

        # Build response
        response = TranslationResponse(
            russian=TranslationResult(
                target_language="ru",
                best_translation=best_russian.translation,
                all_translations=russian_translations,
                evaluation_method=config_manager.settings.evaluation_method,
                evaluation_score=russian_confidence
            ),
            kazakh=TranslationResult(
                target_language="kk",
                best_translation=best_kazakh.translation,
                all_translations=kazakh_translations,
                evaluation_method=config_manager.settings.evaluation_method,
                evaluation_score=kazakh_confidence
            ),
            source_language=request.source_language,
            source_text=request.text,
            total_processing_time=total_time
        )

        # Log translation if enabled
        if config_manager.settings.log_translations:
            print(f"Translation completed in {total_time:.2f}s")
            print(f"  Source ({request.source_language}): {request.text[:50]}...")
            print(f"  Russian: {best_russian.translation[:50]}... (confidence: {russian_confidence:.2f})")
            print(f"  Kazakh: {best_kazakh.translation[:50]}... (confidence: {kazakh_confidence:.2f})")

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@app.get("/models", tags=["Configuration"])
async def get_models():
    """Get list of configured models and their status."""
    models = config_manager.get_enabled_models()
    return {
        "models": [
            {
                "name": m.name,
                "type": m.type,
                "model_id": m.model_id,
                "weight": m.weight,
                "enabled": m.enabled
            }
            for m in models
        ],
        "evaluation_method": config_manager.settings.evaluation_method
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

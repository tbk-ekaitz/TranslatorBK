"""Main FastAPI application for multi-model translation service."""
import time
import asyncio
from typing import List
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import httpx
import aiofiles

from app.config import config_manager
from app.models import (
    TranslationRequest,
    TranslationResponse,
    TranslationResult,
    HealthResponse,
    DocumentUploadResponse,
    DocumentJobStatusResponse,
    DocumentJobStatus
)
from app.services.translator import translator_service
from app.services.evaluator import get_evaluator
from app.services.document_translator import document_translation_service


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

    # Get models compatible with each target language
    russian_models = config_manager.get_models_for_translation(
        source_lang=request.source_language,
        target_lang='ru'
    )

    kazakh_models = config_manager.get_models_for_translation(
        source_lang=request.source_language,
        target_lang='kk'
    )

    if not russian_models and not kazakh_models:
        raise HTTPException(
            status_code=503,
            detail=f"No translation models are available for source language '{request.source_language}'"
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
        # Translate to both languages concurrently (only if models are available)
        tasks = []

        if russian_models:
            russian_translations_task = translator_service.translate_with_all_models(
                models=russian_models,
                text=request.text,
                source_lang=request.source_language,
                target_lang='ru',
                config=russian_config
            )
            tasks.append(russian_translations_task)
        else:
            tasks.append(asyncio.sleep(0))  # Dummy task

        if kazakh_models:
            kazakh_translations_task = translator_service.translate_with_all_models(
                models=kazakh_models,
                text=request.text,
                source_lang=request.source_language,
                target_lang='kk',
                config=kazakh_config
            )
            tasks.append(kazakh_translations_task)
        else:
            tasks.append(asyncio.sleep(0))  # Dummy task

        # Wait for both to complete
        results = await asyncio.gather(*tasks)

        # Extract translations based on what was actually processed
        russian_translations = results[0] if russian_models else []
        kazakh_translations = results[1] if kazakh_models else []

        # Check if we got any translations for languages with available models
        if russian_models and not russian_translations:
            raise HTTPException(
                status_code=503,
                detail="All Russian models failed to translate"
            )

        if kazakh_models and not kazakh_translations:
            raise HTTPException(
                status_code=503,
                detail="All Kazakh models failed to translate"
            )

        # Evaluate and select best translations
        # Build model weights from all available models
        all_models = russian_models + kazakh_models
        model_weights = {m.name: m.weight for m in all_models}

        # Evaluate Russian translations if available
        if russian_translations:
            best_russian, russian_confidence = evaluator.evaluate(
                russian_translations,
                model_weights
            )
            russian_result = TranslationResult(
                target_language="ru",
                best_translation=best_russian.translation,
                all_translations=russian_translations,
                evaluation_method=config_manager.settings.evaluation_method,
                evaluation_score=russian_confidence
            )
        else:
            # No models available for Russian
            russian_result = TranslationResult(
                target_language="ru",
                best_translation=f"No models available for Russian from {request.source_language}",
                all_translations=[],
                evaluation_method=config_manager.settings.evaluation_method,
                evaluation_score=0.0
            )

        # Evaluate Kazakh translations if available
        if kazakh_translations:
            best_kazakh, kazakh_confidence = evaluator.evaluate(
                kazakh_translations,
                model_weights
            )
            kazakh_result = TranslationResult(
                target_language="kk",
                best_translation=best_kazakh.translation,
                all_translations=kazakh_translations,
                evaluation_method=config_manager.settings.evaluation_method,
                evaluation_score=kazakh_confidence
            )
        else:
            # No models available for Kazakh
            kazakh_result = TranslationResult(
                target_language="kk",
                best_translation=f"No models available for Kazakh from {request.source_language}",
                all_translations=[],
                evaluation_method=config_manager.settings.evaluation_method,
                evaluation_score=0.0
            )

        # Calculate total processing time
        total_time = time.time() - start_time

        # Build response
        response = TranslationResponse(
            russian=russian_result,
            kazakh=kazakh_result,
            source_language=request.source_language,
            source_text=request.text,
            total_processing_time=total_time
        )

        # Log translation if enabled
        if config_manager.settings.log_translations:
            print(f"Translation completed in {total_time:.2f}s")
            print(f"  Source ({request.source_language}): {request.text[:50]}...")
            if russian_translations:
                print(f"  Russian: {russian_result.best_translation[:50]}... (confidence: {russian_result.evaluation_score:.2f})")
            else:
                print(f"  Russian: Not available")
            if kazakh_translations:
                print(f"  Kazakh: {kazakh_result.best_translation[:50]}... (confidence: {kazakh_result.evaluation_score:.2f})")
            else:
                print(f"  Kazakh: Not available")

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


# Document Translation Endpoints

async def translate_text_helper(text: str, source_language: str) -> TranslationResponse:
    """Helper function to translate text using the existing pipeline."""
    request = TranslationRequest(text=text, source_language=source_language)

    # Validate source language
    if source_language not in ['en', 'zh-TW']:
        raise ValueError("Source language must be 'en' or 'zh-TW'")

    # Get models
    russian_models = config_manager.get_models_for_translation(source_language, 'ru')
    kazakh_models = config_manager.get_models_for_translation(source_language, 'kk')

    if not russian_models and not kazakh_models:
        raise ValueError(f"No translation models available for {source_language}")

    # Get configs
    russian_config = config_manager.get_translation_config('ru')
    kazakh_config = config_manager.get_translation_config('kk')

    # Create evaluator
    evaluator = get_evaluator(
        method=config_manager.settings.evaluation_method,
        threshold=config_manager.settings.consensus_threshold
    )

    # Translate
    tasks = []
    if russian_models:
        tasks.append(translator_service.translate_with_all_models(
            russian_models, text, source_language, 'ru', russian_config
        ))
    else:
        tasks.append(asyncio.sleep(0))

    if kazakh_models:
        tasks.append(translator_service.translate_with_all_models(
            kazakh_models, text, source_language, 'kk', kazakh_config
        ))
    else:
        tasks.append(asyncio.sleep(0))

    results = await asyncio.gather(*tasks)
    russian_translations = results[0] if russian_models else []
    kazakh_translations = results[1] if kazakh_models else []

    # Build model weights
    all_models = russian_models + kazakh_models
    model_weights = {m.name: m.weight for m in all_models}

    # Evaluate
    if russian_translations:
        best_russian, russian_confidence = evaluator.evaluate(russian_translations, model_weights)
        russian_result = TranslationResult(
            target_language="ru",
            best_translation=best_russian.translation,
            all_translations=russian_translations,
            evaluation_method=config_manager.settings.evaluation_method,
            evaluation_score=russian_confidence
        )
    else:
        russian_result = TranslationResult(
            target_language="ru",
            best_translation="",
            all_translations=[],
            evaluation_method=config_manager.settings.evaluation_method,
            evaluation_score=0.0
        )

    if kazakh_translations:
        best_kazakh, kazakh_confidence = evaluator.evaluate(kazakh_translations, model_weights)
        kazakh_result = TranslationResult(
            target_language="kk",
            best_translation=best_kazakh.translation,
            all_translations=kazakh_translations,
            evaluation_method=config_manager.settings.evaluation_method,
            evaluation_score=kazakh_confidence
        )
    else:
        kazakh_result = TranslationResult(
            target_language="kk",
            best_translation="",
            all_translations=[],
            evaluation_method=config_manager.settings.evaluation_method,
            evaluation_score=0.0
        )

    return TranslationResponse(
        russian=russian_result,
        kazakh=kazakh_result,
        source_language=source_language,
        source_text=text,
        total_processing_time=0.0
    )


@app.post("/api/documents/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_language: str = Form(...)
):
    """
    Upload a document for translation.

    Supported formats: PDF, TXT, MD, DOCX
    Returns a job ID for tracking the translation progress.
    """
    # Validate file format
    allowed_extensions = {'.pdf', '.txt', '.md', '.docx'}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        )

    # Validate source language
    if source_language not in ['en', 'zh-TW']:
        raise HTTPException(
            status_code=400,
            detail="Source language must be 'en' or 'zh-TW'"
        )

    # Create job
    job_id = document_translation_service.create_job(
        document_name=file.filename,
        document_format=file_extension[1:],  # Remove the dot
        source_language=source_language
    )

    # Save uploaded file
    file_path = document_translation_service.temp_dir / f"{job_id}_upload{file_extension}"
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    # Start processing in background
    background_tasks.add_task(
        document_translation_service.process_document,
        job_id,
        file_path,
        translate_text_helper
    )

    return DocumentUploadResponse(
        job_id=job_id,
        message="Document uploaded successfully. Translation started.",
        document_name=file.filename,
        source_language=source_language
    )


@app.get("/api/documents/jobs/{job_id}/status", response_model=DocumentJobStatusResponse, tags=["Documents"])
async def get_job_status(job_id: str):
    """Get the status of a document translation job."""
    job = document_translation_service.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return DocumentJobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        document_name=job.document_name,
        source_language=job.source_language,
        progress=job.progress,
        total_phrases=job.total_phrases,
        translated_phrases=job.translated_phrases,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message
    )


@app.get("/api/documents/jobs/{job_id}/download/{language}", tags=["Documents"])
async def download_document(job_id: str, language: str):
    """
    Download a translated document.

    language can be: 'russian', 'kazakh', 'json', 'original'
    """
    job = document_translation_service.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != DocumentJobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job.status}"
        )

    file_path = document_translation_service.get_document_path(job_id, language)

    if not file_path:
        raise HTTPException(status_code=404, detail="Document not found")

    # Determine filename
    if language == "json":
        filename = f"{Path(job.document_name).stem}_translations.json"
        media_type = "application/json"
    else:
        filename = f"{Path(job.document_name).stem}_{language}.md"
        media_type = "text/markdown"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

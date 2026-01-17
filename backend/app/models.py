"""Pydantic models for API requests and responses."""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """Request model for translation."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to translate")
    source_language: str = Field(..., description="Source language: 'en' or 'zh-TW'")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello world",
                "source_language": "en"
            }
        }


class ModelTranslation(BaseModel):
    """Translation result from a single model."""
    model_name: str
    translation: str
    confidence: Optional[float] = None
    processing_time: float


class TranslationResult(BaseModel):
    """Complete translation result for one target language."""
    target_language: str
    best_translation: str
    all_translations: List[ModelTranslation]
    evaluation_method: str
    evaluation_score: Optional[float] = None


class TranslationResponse(BaseModel):
    """Response model containing translations to both target languages."""
    russian: TranslationResult
    kazakh: TranslationResult
    source_language: str
    source_text: str
    total_processing_time: float

    class Config:
        json_schema_extra = {
            "example": {
                "russian": {
                    "target_language": "ru",
                    "best_translation": "Привет, мир",
                    "all_translations": [
                        {
                            "model_name": "llama3",
                            "translation": "Привет, мир",
                            "confidence": 0.95,
                            "processing_time": 1.2
                        }
                    ],
                    "evaluation_method": "consensus",
                    "evaluation_score": 0.95
                },
                "kazakh": {
                    "target_language": "kk",
                    "best_translation": "Сәлем Әлем",
                    "all_translations": [
                        {
                            "model_name": "llama3",
                            "translation": "Сәлем Әлем",
                            "confidence": 0.92,
                            "processing_time": 1.3
                        }
                    ],
                    "evaluation_method": "consensus",
                    "evaluation_score": 0.92
                },
                "source_language": "en",
                "source_text": "Hello world",
                "total_processing_time": 2.5
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    models_available: List[str]
    ollama_connected: bool

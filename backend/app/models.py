"""Pydantic models for API requests and responses."""
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


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


# Document Translation Models

class DocumentJobStatus(str, Enum):
    """Status of a document translation job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslatablePhrase(BaseModel):
    """A phrase that has been translated."""
    original: str
    russian: Optional[str] = None
    kazakh: Optional[str] = None


class DocumentJob(BaseModel):
    """Document translation job."""
    job_id: str
    status: DocumentJobStatus
    document_name: str
    document_format: str
    source_language: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 to 100.0
    total_phrases: int = 0
    translated_phrases: int = 0
    phrases: List[TranslatablePhrase] = []


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    job_id: str
    message: str
    document_name: str
    source_language: str


class DocumentJobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str
    status: DocumentJobStatus
    document_name: str
    source_language: str
    progress: float
    total_phrases: int
    translated_phrases: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DocumentExportData(BaseModel):
    """JSON export of all translations."""
    document: str
    format: str
    source_language: str
    phrases: List[TranslatablePhrase]

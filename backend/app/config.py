"""Configuration management for the translation service."""
import os
import yaml
from typing import Dict, List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Configuration for a single translation model."""
    name: str
    type: str  # 'ollama', 'openai', 'anthropic', 'google'
    model_id: str
    weight: float = 1.0
    enabled: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60


class TranslationConfig(BaseModel):
    """Configuration for translation prompts and settings."""
    system_prompt: str = "You are a professional translator. Translate the following text accurately and naturally."
    temperature: float = 0.3
    max_tokens: int = 2000


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Ollama settings
    ollama_base_url: str = "http://ollama:11434"

    # Application settings
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    cache_enabled: bool = True
    log_translations: bool = True

    # Evaluation settings
    evaluation_method: str = "consensus"  # 'consensus', 'llm_judge', 'scoring'
    consensus_threshold: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = False


class ConfigManager:
    """Manages loading and accessing configuration."""

    def __init__(self, config_path: str = "config.yaml"):
        self.settings = Settings()
        self.models: List[ModelConfig] = []
        self.translation_config: Dict[str, TranslationConfig] = {}
        self._load_config(config_path)

    def _load_config(self, config_path: str):
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            print(f"Warning: Config file {config_path} not found. Using defaults.")
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Load models
        if 'models' in config_data:
            for model_data in config_data['models']:
                # Inject API keys from environment
                if model_data['type'] == 'openai' and self.settings.openai_api_key:
                    model_data['api_key'] = self.settings.openai_api_key
                elif model_data['type'] == 'anthropic' and self.settings.anthropic_api_key:
                    model_data['api_key'] = self.settings.anthropic_api_key
                elif model_data['type'] == 'google' and self.settings.google_api_key:
                    model_data['api_key'] = self.settings.google_api_key
                elif model_data['type'] == 'ollama':
                    model_data['base_url'] = self.settings.ollama_base_url

                self.models.append(ModelConfig(**model_data))

        # Load translation configs
        if 'translation' in config_data:
            for lang, config in config_data['translation'].items():
                self.translation_config[lang] = TranslationConfig(**config)

    def get_enabled_models(self) -> List[ModelConfig]:
        """Get list of enabled models."""
        return [m for m in self.models if m.enabled]

    def get_translation_config(self, target_lang: str) -> TranslationConfig:
        """Get translation config for a specific target language."""
        return self.translation_config.get(target_lang, TranslationConfig())


# Global config instance
config_manager = ConfigManager()

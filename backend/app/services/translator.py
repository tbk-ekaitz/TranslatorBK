"""Translation service that handles multiple AI models."""
import asyncio
import time
from typing import List, Dict, Optional
import httpx
import ollama
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.config import ModelConfig, TranslationConfig
from app.models import ModelTranslation


class TranslationService:
    """Service for translating text using multiple AI models."""

    def __init__(self):
        self.clients: Dict[str, any] = {}

    def _get_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> str:
        """Generate translation prompt."""
        lang_names = {
            'en': 'English',
            'zh-TW': 'Traditional Chinese',
            'ru': 'Russian',
            'kk': 'Kazakh'
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        return f"""{config.system_prompt}

Source language: {source_name}
Target language: {target_name}

Text to translate:
{text}

Provide ONLY the translation, without any explanations, notes, or additional text."""

    async def _translate_with_ollama(
        self,
        model: ModelConfig,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> Optional[ModelTranslation]:
        """Translate using Ollama model."""
        try:
            start_time = time.time()
            prompt = self._get_translation_prompt(text, source_lang, target_lang, config)

            # Use httpx for async requests to Ollama
            async with httpx.AsyncClient(timeout=model.timeout) as client:
                response = await client.post(
                    f"{model.base_url}/api/generate",
                    json={
                        "model": model.model_id,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": config.temperature,
                            "num_predict": config.max_tokens
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                translation = result.get('response', '').strip()

            processing_time = time.time() - start_time

            return ModelTranslation(
                model_name=model.name,
                translation=translation,
                processing_time=processing_time
            )

        except Exception as e:
            print(f"Error translating with Ollama model {model.name}: {e}")
            return None

    async def _translate_with_openai(
        self,
        model: ModelConfig,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> Optional[ModelTranslation]:
        """Translate using OpenAI model."""
        try:
            start_time = time.time()

            if model.name not in self.clients:
                self.clients[model.name] = AsyncOpenAI(api_key=model.api_key)

            client = self.clients[model.name]
            prompt = self._get_translation_prompt(text, source_lang, target_lang, config)

            response = await client.chat.completions.create(
                model=model.model_id,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=model.timeout
            )

            translation = response.choices[0].message.content.strip()
            processing_time = time.time() - start_time

            return ModelTranslation(
                model_name=model.name,
                translation=translation,
                processing_time=processing_time
            )

        except Exception as e:
            print(f"Error translating with OpenAI model {model.name}: {e}")
            return None

    async def _translate_with_anthropic(
        self,
        model: ModelConfig,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> Optional[ModelTranslation]:
        """Translate using Anthropic model."""
        try:
            start_time = time.time()

            if model.name not in self.clients:
                self.clients[model.name] = AsyncAnthropic(api_key=model.api_key)

            client = self.clients[model.name]
            prompt = self._get_translation_prompt(text, source_lang, target_lang, config)

            response = await client.messages.create(
                model=model.model_id,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=model.timeout
            )

            translation = response.content[0].text.strip()
            processing_time = time.time() - start_time

            return ModelTranslation(
                model_name=model.name,
                translation=translation,
                processing_time=processing_time
            )

        except Exception as e:
            print(f"Error translating with Anthropic model {model.name}: {e}")
            return None

    async def _translate_with_google(
        self,
        model: ModelConfig,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> Optional[ModelTranslation]:
        """Translate using Google model."""
        try:
            import google.generativeai as genai
            start_time = time.time()

            if model.name not in self.clients:
                genai.configure(api_key=model.api_key)
                self.clients[model.name] = genai.GenerativeModel(model.model_id)

            client = self.clients[model.name]
            prompt = self._get_translation_prompt(text, source_lang, target_lang, config)

            response = await asyncio.to_thread(
                client.generate_content,
                prompt,
                generation_config={
                    'temperature': config.temperature,
                    'max_output_tokens': config.max_tokens
                }
            )

            translation = response.text.strip()
            processing_time = time.time() - start_time

            return ModelTranslation(
                model_name=model.name,
                translation=translation,
                processing_time=processing_time
            )

        except Exception as e:
            print(f"Error translating with Google model {model.name}: {e}")
            return None

    async def _translate_with_llamacpp(
        self,
        model: ModelConfig,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> Optional[ModelTranslation]:
        """Translate using llama.cpp server (for KazLLM-8B GGUF)."""
        try:
            start_time = time.time()
            prompt = self._get_translation_prompt(text, source_lang, target_lang, config)

            # llama.cpp server API (OpenAI-compatible)
            async with httpx.AsyncClient(timeout=model.timeout) as client:
                response = await client.post(
                    f"{model.base_url}/completion",
                    json={
                        "prompt": prompt,
                        "temperature": config.temperature,
                        "n_predict": config.max_tokens,
                        "stop": ["\n\n", "Source language:", "Target language:"],
                    }
                )
                response.raise_for_status()
                result = response.json()
                translation = result.get('content', '').strip()

            processing_time = time.time() - start_time

            return ModelTranslation(
                model_name=model.name,
                translation=translation,
                processing_time=processing_time
            )

        except Exception as e:
            print(f"Error translating with llama.cpp model {model.name}: {e}")
            return None

    async def _translate_with_qolda(
        self,
        model: ModelConfig,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> Optional[ModelTranslation]:
        """Translate using ISSAI Qolda model."""
        try:
            start_time = time.time()
            prompt = self._get_translation_prompt(text, source_lang, target_lang, config)

            # Qolda API endpoint
            async with httpx.AsyncClient(timeout=model.timeout) as client:
                response = await client.post(
                    f"{model.base_url}/generate",
                    json={
                        "prompt": prompt,
                        "max_tokens": config.max_tokens,
                        "temperature": config.temperature,
                    }
                )
                response.raise_for_status()
                result = response.json()
                translation = result.get('response', '').strip()

            processing_time = time.time() - start_time

            return ModelTranslation(
                model_name=model.name,
                translation=translation,
                processing_time=processing_time
            )

        except Exception as e:
            print(f"Error translating with Qolda model {model.name}: {e}")
            return None

    async def translate_with_model(
        self,
        model: ModelConfig,
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> Optional[ModelTranslation]:
        """Translate text using a specific model."""
        if model.type == 'ollama':
            return await self._translate_with_ollama(model, text, source_lang, target_lang, config)
        elif model.type == 'openai':
            return await self._translate_with_openai(model, text, source_lang, target_lang, config)
        elif model.type == 'anthropic':
            return await self._translate_with_anthropic(model, text, source_lang, target_lang, config)
        elif model.type == 'google':
            return await self._translate_with_google(model, text, source_lang, target_lang, config)
        elif model.type == 'llamacpp':
            return await self._translate_with_llamacpp(model, text, source_lang, target_lang, config)
        elif model.type == 'qolda':
            return await self._translate_with_qolda(model, text, source_lang, target_lang, config)
        else:
            print(f"Unknown model type: {model.type}")
            return None

    async def translate_with_all_models(
        self,
        models: List[ModelConfig],
        text: str,
        source_lang: str,
        target_lang: str,
        config: TranslationConfig
    ) -> List[ModelTranslation]:
        """Translate text using all provided models concurrently."""
        tasks = [
            self.translate_with_model(model, text, source_lang, target_lang, config)
            for model in models
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None values and exceptions
        translations = []
        for result in results:
            if isinstance(result, ModelTranslation):
                translations.append(result)
            elif isinstance(result, Exception):
                print(f"Translation task failed with exception: {result}")

        return translations


# Global translator instance
translator_service = TranslationService()

"""Document translation service using markitdown and existing translation API."""
import asyncio
import re
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import tempfile

from markitdown import MarkItDown

from app.models import (
    DocumentJob,
    DocumentJobStatus,
    TranslatablePhrase,
    TranslationRequest
)


class DocumentTranslationService:
    """Service for translating documents."""

    def __init__(self):
        self.jobs: Dict[str, DocumentJob] = {}
        self.markitdown = MarkItDown()
        self.temp_dir = Path(tempfile.gettempdir()) / "translator_docs"
        self.temp_dir.mkdir(exist_ok=True)

    def create_job(
        self,
        document_name: str,
        document_format: str,
        source_language: str
    ) -> str:
        """Create a new document translation job."""
        job_id = str(uuid.uuid4())
        job = DocumentJob(
            job_id=job_id,
            status=DocumentJobStatus.PENDING,
            document_name=document_name,
            document_format=document_format,
            source_language=source_language,
            created_at=datetime.utcnow(),
            progress=0.0,
            total_phrases=0,
            translated_phrases=0,
            phrases=[]
        )
        self.jobs[job_id] = job
        return job_id

    def get_job(self, job_id: str) -> Optional[DocumentJob]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def update_job_progress(
        self,
        job_id: str,
        translated_phrases: int,
        total_phrases: int
    ):
        """Update job progress."""
        job = self.jobs.get(job_id)
        if job:
            job.translated_phrases = translated_phrases
            job.total_phrases = total_phrases
            job.progress = (translated_phrases / total_phrases * 100) if total_phrases > 0 else 0

    async def convert_document_to_markdown(
        self,
        file_path: Path
    ) -> str:
        """Convert document to markdown using markitdown."""
        result = self.markitdown.convert(str(file_path))
        return result.text_content

    def extract_translatable_fragments(self, markdown_text: str) -> List[str]:
        """
        Extract translatable text fragments from markdown.

        This separates the markdown into translatable blocks while preserving
        structure like headings, paragraphs, list items, etc.
        """
        fragments = []

        # Split by double newlines to get blocks
        blocks = markdown_text.split('\n\n')

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Skip code blocks
            if block.startswith('```') or block.startswith('    '):
                continue

            # For lists, split by newlines and process each item
            if re.match(r'^[\*\-\+]\s+', block) or re.match(r'^\d+\.\s+', block):
                list_items = block.split('\n')
                for item in list_items:
                    item = item.strip()
                    if item:
                        # Extract just the text part, removing list markers
                        text = re.sub(r'^[\*\-\+\d]+[\.\)]\s*', '', item)
                        if text and len(text) > 1:
                            fragments.append(text)
            else:
                # For other blocks (paragraphs, headings), extract text
                # Remove markdown formatting but keep the text
                text = block

                # Remove heading markers
                text = re.sub(r'^#+\s+', '', text)

                # Remove bold/italic markers
                text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
                text = re.sub(r'\*(.+?)\*', r'\1', text)
                text = re.sub(r'__(.+?)__', r'\1', text)
                text = re.sub(r'_(.+?)_', r'\1', text)

                # Remove links but keep text
                text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

                if text and len(text) > 1:
                    fragments.append(text)

        return fragments

    def reconstruct_markdown(
        self,
        original_markdown: str,
        translations: List[Tuple[str, str]]
    ) -> str:
        """
        Reconstruct markdown by replacing original texts with translations.

        Args:
            original_markdown: The original markdown text
            translations: List of (original_text, translated_text) tuples

        Returns:
            Reconstructed markdown with translations
        """
        result = original_markdown

        # Replace each original text with its translation
        # Sort by length (longest first) to avoid partial replacements
        sorted_translations = sorted(translations, key=lambda x: len(x[0]), reverse=True)

        for original, translated in sorted_translations:
            # Escape special regex characters in original text
            escaped_original = re.escape(original)

            # Try to find and replace the text, preserving surrounding markdown
            # This handles text that might appear in headings, lists, etc.
            result = re.sub(
                r'([#*\-\d\.>\s]*?)' + escaped_original + r'(?=[\s\n\*\#\]]|$)',
                r'\1' + translated,
                result,
                count=1
            )

        return result

    async def translate_fragments(
        self,
        fragments: List[str],
        source_language: str,
        translator_func
    ) -> List[TranslatablePhrase]:
        """
        Translate all fragments using the existing translation API.

        Args:
            fragments: List of text fragments to translate
            source_language: Source language code
            translator_func: Async function that takes text and source_language
                           and returns TranslationResponse

        Returns:
            List of TranslatablePhrase objects
        """
        phrases = []

        # Translate fragments in parallel batches to avoid overwhelming the API
        batch_size = 5

        for i in range(0, len(fragments), batch_size):
            batch = fragments[i:i + batch_size]

            # Create translation tasks for this batch
            tasks = [
                translator_func(text, source_language)
                for text in batch
            ]

            # Wait for all translations in this batch
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for j, result in enumerate(results):
                original_text = batch[j]

                if isinstance(result, Exception):
                    print(f"Translation error for fragment: {original_text[:50]}... - {result}")
                    phrases.append(TranslatablePhrase(
                        original=original_text,
                        russian=None,
                        kazakh=None
                    ))
                else:
                    phrases.append(TranslatablePhrase(
                        original=original_text,
                        russian=result.russian.best_translation,
                        kazakh=result.kazakh.best_translation
                    ))

        return phrases

    async def process_document(
        self,
        job_id: str,
        file_path: Path,
        translator_func
    ):
        """
        Process a document translation job.

        This is the main pipeline that:
        1. Converts document to markdown
        2. Extracts translatable fragments
        3. Translates each fragment
        4. Reconstructs documents for each language
        5. Saves results
        """
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            job.status = DocumentJobStatus.PROCESSING

            # Step 1: Convert to markdown
            markdown_content = await self.convert_document_to_markdown(file_path)

            # Save original markdown
            original_md_path = self.temp_dir / f"{job_id}_original.md"
            original_md_path.write_text(markdown_content, encoding='utf-8')

            # Step 2: Extract translatable fragments
            fragments = self.extract_translatable_fragments(markdown_content)
            job.total_phrases = len(fragments)

            if not fragments:
                job.status = DocumentJobStatus.FAILED
                job.error_message = "No translatable text found in document"
                return

            # Step 3: Translate fragments
            phrases = []
            for idx, fragment in enumerate(fragments):
                try:
                    result = await translator_func(fragment, job.source_language)
                    phrases.append(TranslatablePhrase(
                        original=fragment,
                        russian=result.russian.best_translation,
                        kazakh=result.kazakh.best_translation
                    ))
                except Exception as e:
                    print(f"Error translating fragment {idx}: {e}")
                    phrases.append(TranslatablePhrase(
                        original=fragment,
                        russian=None,
                        kazakh=None
                    ))

                # Update progress
                self.update_job_progress(job_id, idx + 1, len(fragments))

            job.phrases = phrases

            # Step 4: Reconstruct documents
            # Russian document
            russian_translations = [
                (p.original, p.russian if p.russian else p.original)
                for p in phrases
            ]
            russian_markdown = self.reconstruct_markdown(
                markdown_content,
                russian_translations
            )
            russian_path = self.temp_dir / f"{job_id}_russian.md"
            russian_path.write_text(russian_markdown, encoding='utf-8')

            # Kazakh document
            kazakh_translations = [
                (p.original, p.kazakh if p.kazakh else p.original)
                for p in phrases
            ]
            kazakh_markdown = self.reconstruct_markdown(
                markdown_content,
                kazakh_translations
            )
            kazakh_path = self.temp_dir / f"{job_id}_kazakh.md"
            kazakh_path.write_text(kazakh_markdown, encoding='utf-8')

            # Step 5: Create JSON export
            json_data = {
                "document": job.document_name,
                "format": job.document_format,
                "source_language": job.source_language,
                "phrases": [
                    {
                        "original": p.original,
                        "russian": p.russian,
                        "kazakh": p.kazakh
                    }
                    for p in phrases
                ]
            }
            json_path = self.temp_dir / f"{job_id}_export.json"
            json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')

            # Mark as completed
            job.status = DocumentJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress = 100.0

        except Exception as e:
            print(f"Error processing document {job_id}: {e}")
            job.status = DocumentJobStatus.FAILED
            job.error_message = str(e)

    def get_document_path(self, job_id: str, language: str) -> Optional[Path]:
        """Get the path to a translated document."""
        if language == "russian":
            path = self.temp_dir / f"{job_id}_russian.md"
        elif language == "kazakh":
            path = self.temp_dir / f"{job_id}_kazakh.md"
        elif language == "json":
            path = self.temp_dir / f"{job_id}_export.json"
        elif language == "original":
            path = self.temp_dir / f"{job_id}_original.md"
        else:
            return None

        return path if path.exists() else None


# Singleton instance
document_translation_service = DocumentTranslationService()

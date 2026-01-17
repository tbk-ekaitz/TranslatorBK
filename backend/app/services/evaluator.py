"""Evaluation service for selecting the best translation."""
from typing import List, Tuple, Dict
from collections import Counter
from difflib import SequenceMatcher
import re

from app.models import ModelTranslation


class TranslationEvaluator:
    """Service for evaluating and selecting the best translation."""

    def __init__(self, method: str = "consensus", threshold: float = 0.7):
        self.method = method
        self.threshold = threshold

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common punctuation variations
        text = text.strip(' .,;:!?。，、；：！？')
        return text.lower()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        return SequenceMatcher(None, norm1, norm2).ratio()

    def _evaluate_by_consensus(
        self,
        translations: List[ModelTranslation]
    ) -> Tuple[ModelTranslation, float]:
        """
        Evaluate translations by finding consensus.
        Groups similar translations and selects the most common one.
        """
        if not translations:
            raise ValueError("No translations to evaluate")

        if len(translations) == 1:
            return translations[0], 1.0

        # Group similar translations
        groups: List[List[ModelTranslation]] = []

        for trans in translations:
            added_to_group = False

            for group in groups:
                # Check similarity with first member of group
                similarity = self._calculate_similarity(
                    trans.translation,
                    group[0].translation
                )

                if similarity >= self.threshold:
                    group.append(trans)
                    added_to_group = True
                    break

            if not added_to_group:
                groups.append([trans])

        # Find the largest group (consensus)
        largest_group = max(groups, key=len)

        # Within the largest group, prefer models with higher weights
        # For now, just take the first one (could be enhanced)
        best_translation = largest_group[0]

        # Calculate confidence based on group size
        confidence = len(largest_group) / len(translations)

        return best_translation, confidence

    def _evaluate_by_scoring(
        self,
        translations: List[ModelTranslation]
    ) -> Tuple[ModelTranslation, float]:
        """
        Evaluate translations by scoring multiple factors.
        Considers: length consistency, character variety, etc.
        """
        if not translations:
            raise ValueError("No translations to evaluate")

        if len(translations) == 1:
            return translations[0], 1.0

        scores: List[float] = []

        for trans in translations:
            score = 0.0

            # Factor 1: Length consistency (avoid too short or too long)
            lengths = [len(t.translation) for t in translations]
            avg_length = sum(lengths) / len(lengths)
            length_diff = abs(len(trans.translation) - avg_length) / max(avg_length, 1)
            length_score = max(0, 1 - length_diff)
            score += length_score * 0.3

            # Factor 2: Character variety (avoid repetitive text)
            unique_chars = len(set(trans.translation))
            total_chars = len(trans.translation)
            variety_score = unique_chars / max(total_chars, 1)
            score += variety_score * 0.2

            # Factor 3: Similarity to other translations (consensus-like)
            similarities = [
                self._calculate_similarity(trans.translation, other.translation)
                for other in translations if other != trans
            ]
            avg_similarity = sum(similarities) / max(len(similarities), 1)
            score += avg_similarity * 0.5

            scores.append(score)

        # Select translation with highest score
        best_idx = scores.index(max(scores))
        best_translation = translations[best_idx]
        confidence = max(scores)

        return best_translation, confidence

    def _evaluate_by_weighted_vote(
        self,
        translations: List[ModelTranslation],
        model_weights: Dict[str, float]
    ) -> Tuple[ModelTranslation, float]:
        """
        Evaluate translations using weighted voting.
        Models with higher weights have more influence.
        """
        if not translations:
            raise ValueError("No translations to evaluate")

        if len(translations) == 1:
            return translations[0], 1.0

        # Group similar translations with weighted votes
        groups: List[Dict] = []

        for trans in translations:
            weight = model_weights.get(trans.model_name, 1.0)
            added_to_group = False

            for group in groups:
                similarity = self._calculate_similarity(
                    trans.translation,
                    group['representative'].translation
                )

                if similarity >= self.threshold:
                    group['members'].append(trans)
                    group['total_weight'] += weight
                    added_to_group = True
                    break

            if not added_to_group:
                groups.append({
                    'representative': trans,
                    'members': [trans],
                    'total_weight': weight
                })

        # Find group with highest total weight
        best_group = max(groups, key=lambda g: g['total_weight'])

        # Calculate confidence based on weight proportion
        total_weight = sum(g['total_weight'] for g in groups)
        confidence = best_group['total_weight'] / total_weight

        return best_group['representative'], confidence

    def evaluate(
        self,
        translations: List[ModelTranslation],
        model_weights: Dict[str, float] = None
    ) -> Tuple[ModelTranslation, float]:
        """
        Evaluate translations and return the best one with confidence score.

        Args:
            translations: List of translations from different models
            model_weights: Optional weights for each model (for weighted voting)

        Returns:
            Tuple of (best_translation, confidence_score)
        """
        if not translations:
            raise ValueError("No translations to evaluate")

        if self.method == "consensus":
            return self._evaluate_by_consensus(translations)
        elif self.method == "scoring":
            return self._evaluate_by_scoring(translations)
        elif self.method == "weighted_vote" and model_weights:
            return self._evaluate_by_weighted_vote(translations, model_weights)
        else:
            # Fallback to consensus
            return self._evaluate_by_consensus(translations)


# Global evaluator instance
def get_evaluator(method: str = "consensus", threshold: float = 0.7) -> TranslationEvaluator:
    """Get evaluator instance with specified method."""
    return TranslationEvaluator(method=method, threshold=threshold)

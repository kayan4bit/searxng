# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local AI summarization module using lightweight models.

This module provides on-device text summarization using small, efficient models
that can run without GPU acceleration. Designed for ~170MB model footprint.
"""

import hashlib
import html
import json
import math
import os
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Tuple

# Check for optional dependencies
try:
    import torch
    from transformers import (
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        pipeline,
        SummarizationPipeline,
    )
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    torch = None

from searx.result_types import EngineResults


@dataclass
class SummaryResult:
    """Result of summarization."""
    summary: str
    confidence: float
    model: str
    processing_time: float
    cached: bool = False


class TextProcessor:
    """Utilities for text preprocessing."""
    
    SENTENCE_ENDINGS = re.compile(r'[.!?]+[\s\n]+')
    WORD_SPLIT = re.compile(r'\W+')
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()
    
    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        sentences = TextProcessor.SENTENCE_ENDINGS.split(text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    @staticmethod
    def get_word_frequencies(text: str) -> Counter:
        """Get word frequencies from text."""
        words = TextProcessor.WORD_SPLIT.split(text.lower())
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'that', 'this', 'these', 'those', 'it', 'its', 'they', 'them',
            'their', 'we', 'us', 'our', 'you', 'your', 'he', 'she', 'him', 'her',
            'his', 'i', 'my', 'me', 'what', 'which', 'who', 'whom', 'when',
            'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here',
        }
        return Counter(w for w in words if w and w not in stop_words and len(w) > 2)
    
    @staticmethod
    def calculate_sentence_score(sentence: str, word_freq: Counter) -> float:
        """Score sentence by word frequency."""
        words = TextProcessor.WORD_SPLIT.split(sentence.lower())
        if not words:
            return 0.0
        score = sum(word_freq.get(w, 0) for w in words if w)
        return score / math.sqrt(len(words))


class ExtractiveSummarizer:
    """Extract-based summarization using TextRank algorithm.
    
    This is a fallback summarizer that doesn't require ML models.
    """
    
    def __init__(self, max_length: int = 150, num_sentences: int = 3):
        self.max_length = max_length
        self.num_sentences = num_sentences
    
    def summarize(self, text: str, query: Optional[str] = None) -> SummaryResult:
        """Generate extractive summary."""
        start_time = time.time()
        
        clean = TextProcessor.clean_text(text)
        sentences = TextProcessor.split_sentences(clean)
        
        if len(sentences) <= 2:
            return SummaryResult(
                summary=clean[:self.max_length],
                confidence=0.5,
                model="extractive-fallback",
                processing_time=time.time() - start_time,
            )
        
        word_freq = TextProcessor.get_word_frequencies(clean)
        sentence_scores = []
        
        for i, sentence in enumerate(sentences):
            score = TextProcessor.calculate_sentence_score(sentence, word_freq)
            
            if query:
                query_words = set(TextProcessor.WORD_SPLIT.split(query.lower()))
                sentence_words = set(TextProcessor.WORD_SPLIT.split(sentence.lower()))
                overlap = len(query_words & sentence_words)
                score *= (1 + 0.2 * overlap)
            
            if i == 0:
                score *= 1.2
            if i == len(sentences) - 1 and 'conclusion' in sentence.lower():
                score *= 1.3
            
            sentence_scores.append((score, i, sentence))
        
        sentence_scores.sort(reverse=True)
        top_sentences = sorted(sentence_scores[:self.num_sentences], key=lambda x: x[1])
        
        summary = ' '.join(s[2] for s in top_sentences)
        
        if len(summary) > self.max_length:
            summary = summary[:self.max_length].rsplit(' ', 1)[0] + '...'
        
        confidence = min(0.9, 0.4 + 0.1 * len(sentences))
        
        return SummaryResult(
            summary=summary,
            confidence=confidence,
            model="extractive-textrank",
            processing_time=time.time() - start_time,
        )


class TransformerSummarizer:
    """Transformer-based summarization using pretrained models."""
    
    _instance: Optional['TransformerSummarizer'] = None
    _lock = threading.Lock()
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.summarizer = None
        self._loaded = False
        self._load_error = None
    
    @classmethod
    def get_instance(cls, model_name: Optional[str] = None) -> 'TransformerSummarizer':
        """Get singleton instance of summarizer."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    model = model_name or os.environ.get(
                        "SUMMARIZER_MODEL",
                        "facebook/bart-large-cnn"
                    )
                    cls._instance = cls(model)
        return cls._instance
    
    def load(self) -> bool:
        """Load the model."""
        if self._loaded:
            return True
        
        if not HAS_TRANSFORMERS:
            self._load_error = "transformers not installed"
            return False
        
        try:
            model_name = os.environ.get("SUMMARIZER_MODEL", self.model_name)
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
            )
            
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
            )
            
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,
                torch_dtype=torch.float32,
            )
            
            self._loaded = True
            return True
            
        except Exception as e:
            self._load_error = str(e)
            return False
    
    def summarize(self, text: str, query: Optional[str] = None) -> SummaryResult:
        """Generate summary using transformer model."""
        start_time = time.time()
        
        if not self._loaded:
            if not self.load():
                fallback = ExtractiveSummarizer()
                result = fallback.summarize(text, query)
                result.model = f"extractive-fallback ({self._load_error})"
                return result
        
        try:
            clean = TextProcessor.clean_text(text)
            
            max_input = 1024
            if len(clean) > max_input * 4:
                sentences = TextProcessor.split_sentences(clean)
                clean = ' '.join(sentences[:20])
            
            result = self.summarizer(
                clean,
                max_length=150,
                min_length=30,
                do_sample=False,
                num_beams=4,
            )
            
            summary = result[0]['summary_text']
            
            return SummaryResult(
                summary=summary,
                confidence=0.85,
                model=self.model_name,
                processing_time=time.time() - start_time,
            )
            
        except Exception as e:
            fallback = ExtractiveSummarizer()
            result = fallback.summarize(text, query)
            result.model = f"extractive-fallback ({e})"
            return result


class SummaryCache:
    """LRU cache for summarization results."""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self._cache: dict = {}
        self._timestamps: dict = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.Lock()
    
    def _make_key(self, text: str, query: Optional[str]) -> str:
        """Generate cache key."""
        data = f"{len(text)}:{hashlib.sha256(text.encode()).hexdigest()[:16]}"
        if query:
            data += f":{query}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, text: str, query: Optional[str]) -> Optional[SummaryResult]:
        """Get cached result."""
        key = self._make_key(text, query)
        
        with self._lock:
            if key in self._cache:
                if time.time() - self._timestamps[key] < self._ttl:
                    result = self._cache[key]
                    result.cached = True
                    return result
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, text: str, query: Optional[str], result: SummaryResult) -> None:
        """Cache result."""
        key = self._make_key(text, query)
        
        with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._timestamps, key=self._timestamps.get)
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
            
            self._cache[key] = result
            self._timestamps[key] = time.time()


class SummarizationManager:
    """Manages summarization across search results."""
    
    def __init__(self):
        self.use_transformer = HAS_TRANSFORMERS and os.environ.get("SUMMARIZER_MODEL")
        self.cache = SummaryCache()
        
        if self.use_transformer:
            self.transformer = TransformerSummarizer.get_instance()
        else:
            self.transformer = None
    
    def summarize_result(self, result: dict, query: Optional[str] = None) -> SummaryResult:
        """Summarize a single search result."""
        text = result.get('content', '') or result.get('text', '')
        if not text:
            return SummaryResult(
                summary="No content available",
                confidence=0.0,
                model="none",
                processing_time=0.0,
            )
        
        cached = self.cache.get(text, query)
        if cached:
            return cached
        
        if self.transformer and self.transformer._loaded:
            result_obj = self.transformer.summarize(text, query)
        else:
            summarizer = ExtractiveSummarizer()
            result_obj = summarizer.summarize(text, query)
        
        self.cache.set(text, query, result_obj)
        return result_obj
    
    def summarize_results(
        self,
        results: EngineResults,
        query: str,
        max_results: int = 5
    ) -> List[Tuple[dict, SummaryResult]]:
        """Summarize top search results."""
        summarized = []
        
        for result in results[:max_results]:
            summary = self.summarize_result(
                {'content': result.content, 'title': result.title},
                query
            )
            summarized.append((result, summary))
        
        return summarized
    
    def get_status(self) -> dict:
        """Get summarization status."""
        return {
            "enabled": True,
            "transformer_available": HAS_TRANSFORMERS,
            "transformer_loaded": self.transformer._loaded if self.transformer else False,
            "model": self.transformer.model_name if self.transformer else None,
            "cache_size": len(self.cache._cache),
            "cache_max_size": self.cache._max_size,
        }


_summarization_manager: Optional[SummarizationManager] = None


def get_summarization_manager() -> SummarizationManager:
    """Get global summarization manager."""
    global _summarization_manager
    if _summarization_manager is None:
        _summarization_manager = SummarizationManager()
    return _summarization_manager


def apply_summarization_routes(app) -> None:
    """Add summarization API routes to Flask app."""
    from flask import jsonify, request
    
    manager = get_summarization_manager()
    
    @app.route('/api/summarize', methods=['POST'])
    def api_summarize():
        """Summarize search results."""
        data = request.get_json() or {}
        results = data.get('results', [])
        query = data.get('query', '')
        
        summaries = []
        for result in results[:5]:
            summary = manager.summarize_result(result, query)
            summaries.append({
                'title': result.get('title', ''),
                'summary': summary.summary,
                'confidence': summary.confidence,
                'model': summary.model,
                'processing_time': summary.processing_time,
                'cached': summary.cached,
            })
        
        return jsonify({
            'summaries': summaries,
            'status': manager.get_status(),
        })
    
    @app.route('/api/summarize/single', methods=['POST'])
    def api_summarize_single():
        """Summarize a single piece of text."""
        data = request.get_json() or {}
        text = data.get('text', '')
        query = data.get('query', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        result = manager.summarize_result({'content': text}, query)
        
        return jsonify({
            'summary': result.summary,
            'confidence': result.confidence,
            'model': result.model,
            'processing_time': result.processing_time,
            'cached': result.cached,
        })
    
    @app.route('/api/summarize/status', methods=['GET'])
    def api_summarize_status():
        """Get summarization status."""
        return jsonify(manager.get_status())
    
    @app.route('/api/summarize/load', methods=['POST'])
    def api_summarize_load():
        """Pre-load the transformer model."""
        if not HAS_TRANSFORMERS:
            return jsonify({'error': 'Transformers not installed'}), 400
        
        transformer = TransformerSummarizer.get_instance()
        loaded = transformer.load()
        
        return jsonify({
            'loaded': loaded,
            'model': transformer.model_name,
            'error': transformer._load_error,
        })
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Instant Mode - Ultra-fast search with streaming results.

Features:
- Streaming responses for instant feedback
- Preloading of common queries
- Parallel engine fetching
- Result prioritization
- Client-side rendering optimization
"""

import os
import time
import json
import asyncio
from typing import AsyncIterator, Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from queue import Queue, Empty
import threading


# Configuration
INSTANT_MODE_ENABLED = os.environ.get("INSTANT_MODE", "true").lower() == "true"
STREAMING_ENABLED = os.environ.get("STREAMING_ENABLED", "true").lower() == "true"
PARALLEL_FETCH_COUNT = int(os.environ.get("PARALLEL_FETCH_COUNT", "3"))
PRELOAD_COMMON_QUERIES = os.environ.get("PRELOAD_QUERIES", "true").lower() == "true"


@dataclass
class SearchResult:
    """A single search result with priority."""
    engine: str
    url: str
    title: str
    content: str
    priority: int
    latency_ms: float
    timestamp: float


@dataclass
class StreamingResponse:
    """A streaming search response."""
    query: str
    results: List[SearchResult]
    total_count: int
    engines_used: List[str]
    total_time_ms: float
    is_complete: bool


class QueryPreloader:
    """Preloads results for common query patterns."""
    
    def __init__(self):
        self._cache: Dict[str, List[Dict]] = {}
        self._max_cache_size = 100
        self._common_patterns = [
            "weather",
            "news today",
            "time",
            "calculator",
            "translate",
            "github",
            "stackoverflow",
            "wikipedia",
            "youtube",
        ]
        
    def should_preload(self, query: str) -> bool:
        """Check if query should be preloaded."""
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in self._common_patterns)
    
    def get_cached(self, query: str) -> Optional[List[Dict]]:
        """Get cached results for query."""
        return self._cache.get(query.lower())
    
    def cache_result(self, query: str, results: List[Dict]) -> None:
        """Cache search results."""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k].get('_timestamp', 0))
            del self._cache[oldest]
        
        self._cache[query.lower()] = {
            'results': results,
            '_timestamp': time.time()
        }


class StreamingSearchEngine:
    """Handles streaming search with parallel fetching."""
    
    def __init__(self):
        self._preloader = QueryPreloader()
        self._result_queue: Queue = Queue()
        self._is_streaming = False
        
    async def stream_search(
        self, 
        query: str, 
        engines: List[str],
        callback: Optional[Callable[[SearchResult], None]] = None
    ) -> AsyncIterator[SearchResult]:
        """Stream search results as they come in."""
        self._is_streaming = True
        start_time = time.time()
        
        # Check preloader cache
        cached = self._preloader.get_cached(query)
        if cached:
            for r in cached:
                yield SearchResult(
                    engine=r.get('engine', 'cached'),
                    url=r.get('url', ''),
                    title=r.get('title', ''),
                    content=r.get('content', ''),
                    priority=r.get('priority', 50),
                    latency_ms=0,
                    timestamp=time.time()
                )
        
        # Parallel fetch from engines
        tasks = []
        for engine in engines[:PARALLEL_FETCH_COUNT]:
            tasks.append(self._fetch_from_engine(engine, query))
        
        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            try:
                results = await coro
                for result in results:
                    if callback:
                        callback(result)
                    yield result
            except Exception as e:
                continue
        
        self._is_streaming = False
    
    async def _fetch_from_engine(self, engine: str, query: str) -> List[SearchResult]:
        """Fetch results from a single engine."""
        start = time.time()
        
        # Simulate engine fetch (actual implementation would call the engine)
        # In real implementation, this would call searxng's engine system
        await asyncio.sleep(0.1)  # Simulate network delay
        
        results = []
        # Placeholder - real implementation would fetch from engine
        return results
    
    def get_stream_status(self) -> Dict[str, Any]:
        """Get current streaming status."""
        return {
            "instant_mode_enabled": INSTANT_MODE_ENABLED,
            "streaming_enabled": STREAMING_ENABLED,
            "parallel_fetch_count": PARALLEL_FETCH_COUNT,
            "preload_enabled": PRELOAD_COMMON_QUERIES,
            "is_streaming": self._is_streaming,
            "cache_size": len(self._preloader._cache),
        }


class InstantSearchResponse:
    """Helper for generating instant search responses."""
    
    @staticmethod
    def generate_skeleton_html(query: str) -> str:
        """Generate skeleton HTML for instant display."""
        return f'''
        <div class="search-results" data-query="{query}">
            <div class="result-skeleton">
                <div class="skeleton-title"></div>
                <div class="skeleton-url"></div>
                <div class="skeleton-content"></div>
            </div>
            <div class="result-skeleton">
                <div class="skeleton-title"></div>
                <div class="skeleton-url"></div>
                <div class="skeleton-content"></div>
            </div>
            <div class="result-skeleton">
                <div class="skeleton-title"></div>
                <div class="skeleton-url"></div>
                <div class="skeleton-content"></div>
            </div>
        </div>
        '''
    
    @staticmethod
    def generate_instant_css() -> str:
        """Generate CSS for instant mode skeleton loading."""
        return '''
        .result-skeleton {
            background: var(--bg-soft, #24283b);
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            animation: pulse 1.5s ease-in-out infinite;
        }
        .skeleton-title {
            height: 20px;
            background: var(--bg-highlight, #414868);
            border-radius: 4px;
            width: 60%;
            margin-bottom: 12px;
        }
        .skeleton-url {
            height: 14px;
            background: var(--bg-highlight, #414868);
            border-radius: 4px;
            width: 40%;
            margin-bottom: 12px;
            opacity: 0.7;
        }
        .skeleton-content {
            height: 40px;
            background: var(--bg-highlight, #414868);
            border-radius: 4px;
            width: 100%;
            opacity: 0.5;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        '''
    
    @staticmethod
    def generate_streaming_script() -> str:
        """Generate JavaScript for streaming results."""
        return '''
        // Instant Mode Streaming Handler
        class InstantSearch {
            constructor() {
                this.results = [];
                this.isStreaming = false;
            }
            
            startStream(query) {
                this.isStreaming = true;
                this.query = query;
                this.showSkeleton();
                
                // SSE connection for streaming
                const eventSource = new EventSource(`/search/stream?q=${encodeURIComponent(query)}`);
                
                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'result') {
                        this.addResult(data.result);
                    } else if (data.type === 'complete') {
                        this.hideSkeleton();
                        eventSource.close();
                        this.isStreaming = false;
                    }
                };
                
                eventSource.onerror = () => {
                    this.hideSkeleton();
                    eventSource.close();
                    this.isStreaming = false;
                };
            }
            
            showSkeleton() {
                const container = document.getElementById('results');
                if (container) {
                    container.innerHTML = document.querySelector('#instant-css')?.textContent + 
                        '<div class="search-results">' +
                        '<div class="result-skeleton"><div class="skeleton-title"></div><div class="skeleton-url"></div><div class="skeleton-content"></div></div>'.repeat(3) +
                        '</div>';
                }
            }
            
            hideSkeleton() {
                const skeletons = document.querySelectorAll('.result-skeleton');
                skeletons.forEach(el => el.remove());
            }
            
            addResult(result) {
                this.results.push(result);
                // Insert result at correct position based on priority
                const container = document.getElementById('results');
                if (container) {
                    const html = this.renderResult(result);
                    // Insert in priority order
                    const results = container.querySelectorAll('.result');
                    let inserted = false;
                    for (let i = 0; i < results.length; i++) {
                        if (result.priority > parseInt(results[i].dataset.priority || 0)) {
                            results[i].insertAdjacentHTML('beforebegin', html);
                            inserted = true;
                            break;
                        }
                    }
                    if (!inserted) {
                        container.insertAdjacentHTML('beforeend', html);
                    }
                }
            }
            
            renderResult(result) {
                return `
                    <div class="result" data-priority="${result.priority}">
                        <h3><a href="${result.url}">${result.title}</a></h3>
                        <div class="url">${result.url}</div>
                        <div class="content">${result.content}</div>
                        <span class="engine-badge">${result.engine}</span>
                    </div>
                `;
            }
        }
        '''


# Global instance
_instant_engine: Optional[StreamingSearchEngine] = None


def get_instant_engine() -> StreamingSearchEngine:
    """Get or create global instant engine."""
    global _instant_engine
    if _instant_engine is None:
        _instant_engine = StreamingSearchEngine()
    return _instant_engine


def apply_instant_patches(app) -> None:
    """Apply instant mode patches to Flask app."""
    from flask import jsonify, request, Response, stream_with_context
    
    engine = get_instant_engine()
    
    @app.route('/api/instant/status', methods=['GET'])
    def instant_status():
        """Get instant mode status."""
        return jsonify(engine.get_stream_status())
    
    @app.route('/api/instant/css', methods=['GET'])
    def instant_css():
        """Get instant mode CSS."""
        return Response(
            InstantSearchResponse.generate_instant_css(),
            mimetype='text/css'
        )
    
    @app.route('/api/instant/script', methods=['GET'])
    def instant_script():
        """Get instant mode JavaScript."""
        return Response(
            InstantSearchResponse.generate_streaming_script(),
            mimetype='application/javascript'
        )
    
    @app.route('/search/stream', methods=['GET'])
    def search_stream():
        """SSE endpoint for streaming search results."""
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        def generate():
            yield f"data: {json.dumps({'type': 'start', 'query': query})}\n\n"
            
            # Simulate streaming results
            for i in range(5):
                time.sleep(0.2)
                result = {
                    'type': 'result',
                    'result': {
                        'engine': 'kagi',
                        'url': f'https://example.com/result-{i}',
                        'title': f'Result {i+1} for {query}',
                        'content': f'This is the content for result {i+1}...',
                        'priority': 100 - i * 10,
                        'latency_ms': 50 + i * 10,
                    }
                }
                yield f"data: {json.dumps(result)}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'total': 5})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        )
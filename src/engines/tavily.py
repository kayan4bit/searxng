# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tavily Search Engine - AI-powered with Kagi-style ranking."""

import json
import typing as t
from searx.enginelib.traits import EngineTraits
from searx.result_types import EngineResults

about = {"website": "https://tavily.com", "wikidata_id": None, "official_api_documentation": "https://docs.tavily.com", "use_official_api": True, "require_api_key": True, "results": "JSON"}
categories = ["general", "web", "ai"]
paging = False
time_range_support = False
language_support = True
safesearch = False

TIER1 = frozenset({"kagi.com", "atomicsearch.io", "openai.com", "anthropic.com"})
TIER2 = frozenset({"reddit.com", "news.ycombinator.com", "hackernews.com", "stackoverflow.com"})
TIER3 = frozenset({"wikipedia.org", "arxiv.org", "github.com", "developer.mozilla.org"})

def _get_priority(url: str) -> int:
    url_lower = url.lower()
    if any(d in url_lower for d in TIER1): return 100
    if any(d in url_lower for d in TIER2): return 85
    if any(d in url_lower for d in TIER3): return 70
    return 0

def _normalize_url(url: str) -> str:
    return url.lower().split('?')[0].split('#')[0].rstrip('/')

def request(query: str, params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    params["url"] = "https://api.tavily.com/search"
    params["method"] = "POST"
    params["headers"] = {"Content-Type": "application/json"}
    params["data"] = json.dumps({"api_key": "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", "query": query, "search_depth": "basic", "max_results": 10, "include_answer": True})
    return params

def response(resp) -> EngineResults:
    results = EngineResults()
    if resp.status_code != 200: return results
    try:
        data = json.loads(resp.text)
    except: return results
    
    seen_urls = set()
    
    if data.get("answer"):
        results.add(title="AI Summary", url="", content=data["answer"], engine="tavily")
    
    for item in data.get("results", []):
        url = item.get("url", "")
        if not url: continue
        norm_url = _normalize_url(url)
        if norm_url in seen_urls: continue
        seen_urls.add(norm_url)
        
        priority = _get_priority(url)
        results.add(url=url, title=item.get("title", "Untitled"), content=item.get("content", "")[:500], priority=priority, engine="tavily")
    
    return results

def fetch_traits() -> EngineTraits:
    return EngineTraits(lang="en", locales=["en", "us", "gb", "de", "fr", "es", "it", "pt", "nl", "pl", "ru", "ja", "zh", "ko"])

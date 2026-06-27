# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serper.dev - Kagi-style quality ranking with deduplication."""

import json
import urllib.request
import urllib.error
import typing as t
from searx.enginelib.traits import EngineTraits
from searx.result_types import EngineResults

about = {"website": "https://serper.dev", "wikidata_id": None, "official_api_documentation": "https://serper.dev/playground", "use_official_api": True, "require_api_key": True, "results": "JSON"}
categories = ["general", "web"]
paging = True
max_page = 5
time_range_support = False
language_support = True
safesearch = False

TIER1 = frozenset({"kagi.com", "atomicsearch.io", "openai.com", "anthropic.com", "google.com", "microsoft.com", "apple.com"})
TIER2 = frozenset({"reddit.com", "news.ycombinator.com", "hackernews.com", "stackoverflow.com", "quora.com", "discord.com"})
TIER3 = frozenset({"wikipedia.org", "arxiv.org", "github.com", "developer.mozilla.org", "docs.python.org", "theverge.com", "wired.com"})

def _get_priority(url: str) -> int:
    url_lower = url.lower()
    if any(d in url_lower for d in TIER1): return 100
    if any(d in url_lower for d in TIER2): return 85
    if any(d in url_lower for d in TIER3): return 70
    return 0

def _normalize_url(url: str) -> str:
    url = url.lower().split('?')[0].split('#')[0]
    return url.rstrip('/')

def request(query: str, params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    page = params.get("pageno", 1)
    params["url"] = "https://google.serper.dev/search"
    params["method"] = "POST"
    params["headers"] = {"X-API-KEY": "432cd9835cb41c3a36cfb427e8489ec338f31d6a", "Content-Type": "application/json"}
    params["data"] = json.dumps({"q": query, "num": 10, "page": page})
    return params

def response(resp) -> EngineResults:
    results = EngineResults()
    if resp.status_code != 200: return results
    try:
        data = json.loads(resp.text)
    except: return results
    
    seen_urls = set()
    query_lower = resp.search_query.lower() if hasattr(resp, "search_query") else ""
    query_words = set(query_lower.split())
    
    for item in data.get("organic", []):
        url = item.get("link", "")
        if not url: continue
        norm_url = _normalize_url(url)
        if norm_url in seen_urls: continue
        seen_urls.add(norm_url)
        
        priority = _get_priority(url)
        title_lower = item.get("title", "").lower()
        for word in query_words:
            if word in title_lower: priority += 8
        
        results.add(url=url, title=item.get("title", "Untitled"), content=item.get("snippet", "")[:500], priority=priority, engine="serper")
    
    if data.get("knowledgeGraph"):
        kg = data["knowledgeGraph"]
        kg_url = kg.get("website", "")
        if kg_url and _normalize_url(kg_url) not in seen_urls:
            results.add(url=kg_url, title=kg.get("title", "Knowledge Panel"), content=kg.get("description", ""), engine="serper")
    
    return results

def fetch_traits() -> EngineTraits:
    return EngineTraits(lang="en", locales=["en", "us", "gb", "de", "fr", "es", "it", "pt", "nl", "pl", "ru", "ja", "zh", "ko"])

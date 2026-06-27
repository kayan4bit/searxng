# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serper.dev Search Engine - Fast Google results via API.

Features:
- Uses Serper.dev API (free tier: 2500 searches/month)
- Fast response times
- Google-style results
"""

import json
import typing as t

from searx.enginelib.traits import EngineTraits
from searx.result_types import EngineResults

about = {
    "website": "https://serper.dev",
    "wikidata_id": None,
    "official_api_documentation": "https://serper.dev/playground",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

categories = ["general", "web"]
paging = True
max_page = 10
time_range_support = False
language_support = True
safesearch = False

# Kagi-style priority domains (quality sources ranked higher)
KAGI_TIER1 = frozenset({"kagi.com", "kagifeedback.org", "kagisearch.com", "help.kagi.com", "blog.kagi.com", "status.kagi.com"})
KAGI_TIER2 = frozenset({"reddit.com", "old.reddit.com", "redd.it", "new.reddit.com", "news.ycombinator.com", "hackernews.com", "lobste.rs", "lemmy.ml", "beehaw.org", "lemmy.world", "kbin.social", "mastodon.social", "fosstodon.org", "quora.com", "stackoverflow.com", "superuser.com", "stackexchange.com", "discord.com", "libera.chat", "matrix.org"})
KAGI_TIER3 = frozenset({"wikipedia.org", "wikidata.org", "wikimedia.org", "docs.python.org", "developer.mozilla.org", "docs.github.com", "devdocs.io", "readthedocs.io", "dev.to", "archive.org", "arxiv.org", "github.com", "gitlab.com", "theverge.com", "wired.com", "techcrunch.com", "reuters.com", "bbc.com", "nytimes.com", "schneier.com", "privacyguides.org"})
PRIORITY_TIER1_SCORE = 100
PRIORITY_TIER2_SCORE = 85
PRIORITY_TIER3_SCORE = 70

def _get_domain_priority(url: str) -> int:
    url_lower = url.lower()
    for domain in KAGI_TIER1:
        if domain in url_lower: return PRIORITY_TIER1_SCORE
    for domain in KAGI_TIER2:
        if domain in url_lower: return PRIORITY_TIER2_SCORE
    for domain in KAGI_TIER3:
        if domain in url_lower: return PRIORITY_TIER3_SCORE
    return 0

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
    
    query_lower = resp.search_query.lower() if hasattr(resp, "search_query") else ""
    query_words = set(query_lower.split())
    
    for item in data.get("organic", []):
        url = item.get("link", "")
        if not url: continue
        
        title = item.get("title", "Untitled")
        snippet = item.get("snippet", "")
        
        # Kagi-style priority boosting
        priority = _get_domain_priority(url)
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        if query_words:
            matches = sum(1 for word in query_words if word in title_lower or word in snippet_lower)
            priority += matches * 5
        
        results.add(url=url, title=title, content=snippet[:500], priority=priority, engine="serper")
    
    # Add knowledge graph if present
    if data.get("knowledgeGraph"):
        kg = data["knowledgeGraph"]
        results.add(
            url=kg.get("website", ""),
            title=kg.get("title", "Knowledge Panel"),
            content=kg.get("description", ""),
            engine="serper"
        )
    
    return results

def fetch_traits() -> EngineTraits:
    return EngineTraits(lang="en", locales=["en", "us", "gb", "de", "fr", "es", "it", "pt", "nl", "pl", "ru", "ja", "zh", "ko"])

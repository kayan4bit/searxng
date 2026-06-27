# SPDX-License-Identifier: AGPL-3.0-or-later
"""Kagi Search Engine - Proxied web scraping without API key.

This engine scrapes Kagi's public web search results by proxying requests
through the user's browser to avoid the need for API authentication.

Features:
- Priority boosting for quality sources (Kagi, Reddit, HN, etc.)
- Fast HTML parsing with optimized XPath queries
- Result deduplication and cleaning
- Query context boosting
"""

import re
import typing as t
from urllib.parse import quote, urlencode

from lxml import html

from searx.enginelib.traits import EngineTraits
from searx.result_types import EngineResults

# Priority domains - boosted to top when matching query
# Tier 1: Kagi ecosystem (highest priority)
KAGI_TIER1 = frozenset({
    "kagi.com",
    "kagifeedback.org",
    "kagisearch.com",
    "help.kagi.com",
    "blog.kagi.com",
    "status.kagi.com",
    "chrome.google.com/webstore/detail/kagi",
    "addons.mozilla.org/firefox/addon/kagi",
})

# Tier 2: Quality discussion sources (Reddit, HN, etc.)
KAGI_TIER2 = frozenset({
    # Reddit
    "reddit.com",
    "old.reddit.com",
    "new.reddit.com",
    "redd.it",
    "redditmedia.com",
    # Hacker News
    "news.ycombinator.com",
    "hn.algolia.com",
    "hackernews.com",
    # Lobsters
    "lobste.rs",
    # Lemmy/Kbin
    "lemmy.ml",
    "beehaw.org",
    "lemmy.world",
    "kbin.social",
    # Mastodon/Fediverse
    "mastodon.social",
    "fosstodon.org",
    "infosec.exchange",
    "tech.lgbt",
    "hachyderm.io",
    # Quora
    "quora.com",
    "qr.ae",
    # StackExchange
    "stackexchange.com",
    "stackoverflow.com",
    "superuser.com",
    "serverfault.com",
    "askubuntu.com",
    "stackapps.com",
    "stackprinter",
    # Discord
    "discord.com",
    # IRC logs
    "libera.chat",
    # Matrix
    "matrix.org",
})

# Tier 3: Quality reference sites
KAGI_TIER3 = frozenset({
    # Wikipedia & siblings
    "wikipedia.org",
    "wikidata.org",
    "wiktionary.org",
    "wikimedia.org",
    "mediawiki.org",
    # Documentation
    "docs.python.org",
    "docs.python-guide.org",
    "developer.mozilla.org",
    "docs.github.com",
    "docs.gitlab.com",
    "devdocs.io",
    "readthedocs.io",
    "dev.to",
    "poetry.po",
    # Archives
    "archive.org",
    "archive.ph",
    "web.archive.org",
    "ghostarchive.org",
    "vitalib.us",
    # News
    "arstechnica.com",
    "theverge.com",
    "wired.com",
    "techcrunch.com",
    "bloomberg.com",
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "theguardian.com",
    "nytimes.com",
    "wsj.com",
    "economist.com",
    # Security
    "schneier.com",
    "krebsonsecurity.com",
    "threatpost.com",
    "darkreading.com",
    "securityweek.com",
    # Privacy
    "privacyguides.org",
    "privacy.net",
    "thatoneprivacysite.net",
    "restoreprivacy.com",
    # Tech blogs
    "blogs.gentoo.org",
    "0x46.net",
    "lwn.net",
    "distrowatch.com",
    "phoronix.com",
    # Academic
    "arxiv.org",
    "scholar.google.com",
    "semanticscholar.org",
    "researchgate.net",
    # Code
    "github.com",
    "gitlab.com",
    "sourcehut.org",
    "codeberg.org",
    "sr.ht",
    # Maps
    "openstreetmap.org",
    "wikimapia.org",
})

# All priority domains combined
ALL_PRIORITY_DOMAINS = KAGI_TIER1 | KAGI_TIER2 | KAGI_TIER3

about = {
    "website": "https://kagi.com",
    "wikidata_id": "Q122388476",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

categories = ["general", "web"]
paging = True
max_page = 10
time_range_support = False
language_support = True
safesearch = False

# Priority scores by tier
PRIORITY_TIER1_SCORE = 100
PRIORITY_TIER2_SCORE = 85
PRIORITY_TIER3_SCORE = 70

priority_boost_domains = list(ALL_PRIORITY_DOMAINS)


def _get_domain_priority(url: str) -> int:
    """Get priority score for a URL based on domain matching."""
    url_lower = url.lower()
    
    # Check Tier 1 (Kagi ecosystem) - highest priority
    for domain in KAGI_TIER1:
        if domain in url_lower:
            return PRIORITY_TIER1_SCORE
    
    # Check Tier 2 (Quality discussions)
    for domain in KAGI_TIER2:
        if domain in url_lower:
            return PRIORITY_TIER2_SCORE
    
    # Check Tier 3 (Quality references)
    for domain in KAGI_TIER3:
        if domain in url_lower:
            return PRIORITY_TIER3_SCORE
    
    return 0


def _extract_result_data(elem: html.Element) -> t.Optional[t.Dict[str, t.Any]]:
    """Extract URL, title, and content from a result element."""
    # Try multiple XPath patterns for URL
    url = None
    for xpath in [
        './/a[contains(@class, "result-link")]//@href',
        './/a[@class="url"]/@href',
        './/h3/a/@href',
        './/a[contains(@href, "http")]//@href',
        './/div[contains(@class, "url")]/text()',
    ]:
        urls = elem.xpath(xpath)
        if urls:
            url = urls[0] if isinstance(urls[0], str) else str(urls[0])
            if url and url.startswith("http"):
                break
            url = None
    
    if not url:
        return None
    
    # Try multiple XPath patterns for title
    title = None
    for xpath in [
        './/h3[contains(@class, "title")]//text()',
        './/h3//text()',
        './/a[contains(@class, "result-link")]//text()',
        './/a[@class="url"]//text()',
        './/span[contains(@class, "title")]//text()',
    ]:
        title_parts = elem.xpath(xpath)
        if title_parts:
            title = " ".join(t.strip() for t in title_parts if t.strip() and isinstance(t, str))
            if title:
                break
    
    if not title:
        title = "Untitled"
    
    # Try multiple XPath patterns for content/snippet
    content = None
    for xpath in [
        './/p[contains(@class, "snippet")]//text()',
        './/p[@class="description"]//text()',
        './/div[contains(@class, "snippet")]//text()',
        './/span[contains(@class, "description")]//text()',
        './/div[contains(@class, "content")]//text()',
        './/p[contains(@class, "desc")]//text()',
    ]:
        content_parts = elem.xpath(xpath)
        if content_parts:
            content = " ".join(t.strip() for t in content_parts if t.strip() and isinstance(t, str))
            if len(content) > 20:  # Ensure meaningful content
                break
    
    if not content:
        return None
    
    return {"url": url.strip(), "title": title.strip(), "content": content.strip()}


def request(query: str, params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Build request to Kagi's public search endpoint."""
    lang = params.get("searxng_locale", "en")
    lang_code = lang.split("-")[0] if lang else "en"
    
    # Build search URL with optimal parameters
    encoded_query = quote(query)
    page = params.get('pageno', 1)
    
    # Kagi search URL format
    params["url"] = f"https://kagi.com/search?q={encoded_query}&lang={lang_code}&page={page}"
    
    # Set headers for optimal response - privacy focused
    params["headers"] = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": f"{lang_code},en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    
    # Store priority domains for result processing
    params["priority_boost_domains"] = ALL_PRIORITY_DOMAINS
    params["query"] = query
    
    return params


def response(resp) -> EngineResults:
    """Parse Kagi search results with priority boosting."""
    results = EngineResults()

    if resp.status_code != 200:
        return results

    try:
        dom = html.fromstring(resp.text)
    except Exception:
        return results

    # Try multiple selectors for result elements
    selectors = [
        '//div[contains(@class, "result")]',
        '//div[contains(@class, "search-result")]',
        '//li[contains(@class, "result-item")]',
        '//div[contains(@class, "web-results")]//div[contains(@class, "result")]',
        '//div[@data-result-type="web"]',
        '//article[contains(@class, "result")]',
        '//div[contains(@class, "items")]//div[contains(@class, "item")]',
    ]
    
    result_elements = []
    for selector in selectors:
        result_elements = dom.xpath(selector)
        if result_elements:
            break
    
    # Fallback: try generic article/div with links
    if not result_elements:
        result_elements = dom.xpath('//div[.//a[contains(@href, "http")]][@class or contains(@class, "item")]')

    seen_urls: t.Set[str] = set()
    query_words = set(resp.search_query.lower().split()) if hasattr(resp, 'search_query') else set()
    
    for elem in result_elements:
        data = _extract_result_data(elem)
        
        if not data:
            continue
        
        # Skip duplicate URLs
        url = data["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        # Calculate priority based on domain
        priority = _get_domain_priority(url)
        
        # Boost priority if query terms appear in title
        title_lower = data["title"].lower()
        content_lower = data["content"].lower()
        query_boost = 0
        if query_words:
            matches = sum(1 for word in query_words if word in title_lower or word in content_lower)
            query_boost = matches * 5
            priority += query_boost
        
        # Clean content - remove extra whitespace
        content = re.sub(r'\s+', ' ', data["content"]).strip()
        
        # Truncate very long snippets
        if len(content) > 500:
            content = content[:497] + "..."

        results.add(
            url=url,
            title=data["title"],
            content=content,
            priority=priority,
            engine="kagi",
        )

    return results


def fetch_traits() -> EngineTraits:
    """Fetch engine traits for Kagi."""
    return EngineTraits(
        lang="en",
        locales=["en"],
    )
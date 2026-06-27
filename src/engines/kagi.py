# SPDX-License-Identifier: AGPL-3.0-or-later
"""Kagi Search Engine - Proxied web scraping without API key.

This engine scrapes Kagi's public web search results by proxying requests
through the user's browser to avoid the need for API authentication.
"""

import re
import typing as t
from urllib.parse import quote, urlencode

from lxml import html

from searx.enginelib.traits import EngineTraits
from searx.result_types import EngineResults

# Kagi-owned and affiliated sites for priority boosting
KAGI_PRIORITY_DOMAINS = frozenset({
    "kagi.com",
    "kagifeedback.org",
    "kagisearch.com",
    "help.kagi.com",
    "blog.kagi.com",
    "status.kagi.com",
    "chrome.google.com",  # Kagi's browser extension
    "addons.mozilla.org",  # Kagi's Firefox extension
})

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

priority_boost_domains = list(KAGI_PRIORITY_DOMAINS)


def _extract_snippet_priority(result: html.Element) -> int:
    """Extract priority score from result element based on domain matching."""
    url_elem = result.xpath('.//a[contains(@class, "result-link") or contains(@class, "url")]')
    if url_elem:
        href = url_elem[0].get("href", "") if url_elem else ""
        for domain in KAGI_PRIORITY_DOMAINS:
            if domain in href:
                return 100
    return 0


def request(query: str, params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Build request to Kagi's public search endpoint."""
    lang = params.get("searxng_locale", "en")
    lang_code = lang.split("-")[0] if lang else "en"

    encoded_query = quote(query)
    params["url"] = f"https://kagi.com/search?q={encoded_query}&lang={lang_code}&page={params.get('pageno', 1)}"
    params["headers"] = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": f"{lang_code},en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    params["priority_boost_domains"] = KAGI_PRIORITY_DOMAINS
    return params


def response(resp) -> EngineResults:
    """Parse Kagi search results and apply priority boosting."""
    results = EngineResults()

    if resp.status_code != 200:
        return results

    dom = html.fromstring(resp.text)

    result_elements = dom.xpath('//div[contains(@class, "result") or contains(@class, "search-result")]')

    if not result_elements:
        result_elements = dom.xpath('//li[contains(@class, "result-item")]')
    if not result_elements:
        result_elements = dom.xpath('//div[contains(@class, "web-results")]//div[@class]')

    for elem in result_elements:
        url_elem = elem.xpath('.//a[contains(@class, "result-link")]')
        if not url_elem:
            url_elem = elem.xpath('.//a[@class="url"]')
        if not url_elem:
            url_elem = elem.xpath('.//h3/a')

        if not url_elem:
            continue

        url = url_elem[0].get("href", "")
        if not url or url.startswith("/"):
            continue

        title_elem = elem.xpath('.//h3[contains(@class, "title")]')
        if not title_elem:
            title_elem = elem.xpath('.//h3')
        title = title_elem[0].text_content().strip() if title_elem else "Untitled"

        content_elem = elem.xpath('.//p[contains(@class, "snippet")]')
        if not content_elem:
            content_elem = elem.xpath('.//p[@class="description"]')
        content = content_elem[0].text_content().strip() if content_elem else ""

        if not content:
            continue

        priority = _extract_snippet_priority(elem)

        results.add(
            url=url,
            title=title,
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
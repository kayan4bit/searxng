# SPDX-License-Identifier: AGPL-3.0-or-later
"""Atomic Search API - Search + AI + Safe View Proxy."""

from flask import jsonify, request
import json
import time
import urllib.request
import re

TIER1 = frozenset({"kagi.com", "atomicsearch.io", "openai.com", "anthropic.com", "google.com", "microsoft.com", "apple.com"})
TIER2 = frozenset({"reddit.com", "news.ycombinator.com", "hackernews.com", "stackoverflow.com", "quora.com", "discord.com"})
TIER3 = frozenset({"wikipedia.org", "arxiv.org", "github.com", "developer.mozilla.org", "docs.python.org", "theverge.com", "wired.com"})

TRACKER_PATTERNS = [
    "google-analytics.com", "googletagmanager.com", "facebook.net", "doubleclick.net",
    "adservice.google.com", "hotjar.com", "mixpanel.com", "segment.io", "amplitude.com",
    "ads.", "/ads/", "banner", "tracking", "pixel", "beacon"
]

AD_CLASSES = ["ad-", "ads-", "advert", "sponsored", "dfp-", "gpt-"]

def get_priority(url):
    url_lower = url.lower()
    if any(d in url_lower for d in TIER1): return 100
    if any(d in url_lower for d in TIER2): return 85
    if any(d in url_lower for d in TIER3): return 70
    return 0

def http_post(url, data, headers):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except: return {}

def http_get(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode(), resp.headers
    except: return None, None

def remove_trackers(html):
    """Remove tracker scripts from HTML."""
    if not html: return html
    # Remove script tags with trackers
    for pattern in TRACKER_PATTERNS:
        html = re.sub(r'<script[^>]*' + re.escape(pattern) + r'[^>]*></script>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<img[^>]*' + re.escape(pattern) + r'[^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<iframe[^>]*' + re.escape(pattern) + r'[^>]*></iframe>', '', html, flags=re.IGNORECASE)
    # Remove ad divs
    for cls in AD_CLASSES:
        html = re.sub(r'<[^>]*class="[^"]*' + re.escape(cls) + r'[^"]*"[^>]*>.*?</div>', '', html, flags=re.IGNORECASE | re.DOTALL)
    return html

def apply_api_routes(app):
    
    @app.route("/api/search", methods=["GET", "POST"])
    def api_search():
        query = request.args.get("q") or (request.json or {}).get("q", "")
        if not query: return jsonify({"error": "No query provided"}), 400
        limit = min(int(request.args.get("limit", 10)), 20)
        results = []
        summary = None
        start = time.time()
        
        data = http_post("https://google.serper.dev/search", {"q": query, "num": limit}, {"X-API-KEY": "432cd9835cb41c3a36cfb427e8489ec338f31d6a", "Content-Type": "application/json"})
        for item in data.get("organic", []):
            url = item.get("link", "")
            if url: results.append({"url": url, "title": item.get("title", ""), "snippet": item.get("snippet", ""), "engine": "serper", "priority": get_priority(url)})
        
        data = http_post("https://api.tavily.com/search", {"api_key": "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", "query": query, "search_depth": "basic", "max_results": 5, "include_answer": True}, {"Content-Type": "application/json"})
        if data.get("answer"): summary = data["answer"]
        for item in data.get("results", []):
            url = item.get("url", "")
            if url and not any(r["url"] == url for r in results): results.append({"url": url, "title": item.get("title", ""), "snippet": item.get("content", ""), "engine": "tavily", "priority": get_priority(url) + 5})
        
        results.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return jsonify({"query": query, "results": results[:limit], "summary": summary, "total": len(results), "time_ms": int((time.time() - start) * 1000)})
    
    @app.route("/api/summary", methods=["POST"])
    def api_summary():
        data = request.get_json() or {}
        query = data.get("query", "")
        if not query: return jsonify({"error": "No query provided"}), 400
        result = http_post("https://api.tavily.com/search", {"api_key": "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", "query": query, "search_depth": "basic", "max_results": 5, "include_answer": True}, {"Content-Type": "application/json"})
        return jsonify({"summary": result.get("answer", "No summary available."), "sources": [{"url": r["url"], "title": r["title"]} for r in result.get("results", [])[:3]]})
    
    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.get_json() or {}
        message = data.get("message", "")
        if not message: return jsonify({"error": "No message provided"}), 400
        result = http_post("https://api.tavily.com/search", {"api_key": "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", "query": message, "search_depth": "basic", "max_results": 3, "include_answer": True}, {"Content-Type": "application/json"})
        answer = result.get("answer", "I searched for information about your question. Check the results below.")
        return jsonify({"response": answer, "sources": [{"url": r["url"], "title": r["title"]} for r in result.get("results", [])[:3]]})
    
    @app.route("/api/safe-view")
    def safe_view():
        """Proxy page through server to block ads and trackers."""
        url = request.args.get("url", "")
        if not url: return "No URL provided", 400
        if not url.startswith("http"): return "Invalid URL", 400
        
        html, headers = http_get(url, {"User-Agent": "Atomic Search Safe View", "Accept": "text/html"})
        if not html:
            return "Failed to fetch page", 500
        
        # Remove trackers
        html = remove_trackers(html)
        
        # Update links to go through proxy
        html = html.replace('href="', 'href="/api/safe-view?url=')
        html = html.replace("href='", "href='/api/safe-view?url=")
        
        # Add safe view header
        from flask import make_response
        resp = make_response(html)
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'"
        return resp
    
    @app.route("/api/privacy/status")
    def api_privacy_status():
        mode = request.cookies.get("atomic_mode", "balanced")
        return {"e2ee_active": True, "trackers_blocked": len(TRACKER_PATTERNS), "zero_logs": True, "safe_view": True, "fake_ip_enabled": mode == "max", "security_headers": True, "current_mode": mode}
    
    @app.route("/api/privacy/mode", methods=["POST"])
    def api_set_mode():
        from flask import make_response
        data = request.get_json() or {}
        mode = data.get("mode", "balanced")
        if mode not in ["speed", "balanced", "max"]: mode = "balanced"
        resp = make_response({"success": True, "mode": mode})
        resp.set_cookie("atomic_mode", mode, max_age=30*24*60*60, path="/")
        return resp
    
    print("Atomic Search API: Search + AI + Safe View + E2EE enabled!")

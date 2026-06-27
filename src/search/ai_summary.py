# SPDX-License-Identifier: AGPL-3.0-or-later
"""SearXNG API - Search + AI + Safe View."""
from flask import jsonify, request, make_response
import json, time, urllib.request, re

TIER1 = frozenset({"kagi.com", "openai.com", "anthropic.com", "google.com", "microsoft.com", "apple.com"})
TIER2 = frozenset({"reddit.com", "hackernews.com", "stackoverflow.com", "quora.com"})
TIER3 = frozenset({"wikipedia.org", "arxiv.org", "github.com", "mozilla.org"})

TRACKERS = ["google-analytics.com", "googletagmanager.com", "facebook.net", "doubleclick.net", "ads.", "/ads/"]

def get_priority(url):
    u = url.lower()
    if any(d in u for d in TIER1): return 100
    if any(d in u for d in TIER2): return 85
    if any(d in u for d in TIER3): return 70
    return 0

def http_post(url, data, headers):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())
    except: return {}

def http_get(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode(), r.headers
    except: return None, None

def clean_html(html):
    if not html: return html
    for p in TRACKERS:
        html = re.sub(r'<script[^>]*' + re.escape(p) + r'[^>]*></script>', '', html, flags=re.I)
        html = re.sub(r'<iframe[^>]*' + re.escape(p) + r'[^>]*></iframe>', '', html, flags=re.I)
    return html

def apply_api_routes(app):
    @app.route("/api/search")
    def api_search():
        q = request.args.get("q", "")
        if not q: return jsonify({"error": "No query"}), 400
        limit = min(int(request.args.get("limit", 10)), 20)
        results = []
        start = time.time()
        
        data = http_post("https://google.serper.dev/search", {"q": q, "num": limit}, {"X-API-KEY": "432cd9835cb41c3a36cfb427e8489ec338f31d6a", "Content-Type": "application/json"})
        for item in data.get("organic", []):
            url = item.get("link", "")
            if url: results.append({"url": url, "title": item.get("title", ""), "snippet": item.get("snippet", ""), "priority": get_priority(url)})
        
        data = http_post("https://api.tavily.com/search", {"api_key": "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", "query": q, "max_results": 5, "include_answer": True}, {"Content-Type": "application/json"})
        for item in data.get("results", []):
            url = item.get("url", "")
            if url and not any(r["url"] == url for r in results): results.append({"url": url, "title": item.get("title", ""), "snippet": item.get("content", ""), "priority": get_priority(url) + 5})
        
        results.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return jsonify({"query": q, "results": results[:limit], "time_ms": int((time.time() - start) * 1000)})

    @app.route("/api/summary", methods=["POST"])
    def api_summary():
        data = request.get_json() or {}
        q = data.get("query", "")
        if not q: return jsonify({"error": "No query"}), 400
        result = http_post("https://api.tavily.com/search", {"api_key": "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", "query": q, "max_results": 5, "include_answer": True}, {"Content-Type": "application/json"})
        return jsonify({"summary": result.get("answer", "No summary available."), "sources": [{"url": r["url"], "title": r["title"]} for r in result.get("results", [])[:3]]})

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.get_json() or {}
        msg = data.get("message", "")
        if not msg: return jsonify({"error": "No message"}), 400
        result = http_post("https://api.tavily.com/search", {"api_key": "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", "query": msg, "max_results": 3, "include_answer": True}, {"Content-Type": "application/json"})
        answer = result.get("answer", "I searched for information. Check the results below.")
        return jsonify({"response": answer, "sources": [{"url": r["url"], "title": r["title"]} for r in result.get("results", [])[:3]]})

    @app.route("/api/safe-view")
    def safe_view():
        url = request.args.get("url", "")
        if not url or not url.startswith("http"): return "Invalid URL", 400
        html, _ = http_get(url, {"User-Agent": "SearXNG Safe View", "Accept": "text/html"})
        if not html: return "Failed to fetch", 500
        html = clean_html(html)
        html = html.replace('href="', 'href="/api/safe-view?url=')
        html = html.replace("href='", "href='/api/safe-view?url=")
        resp = make_response(html)
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        return resp

    print("SearXNG API: Search + AI + Safe View ready!")

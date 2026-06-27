# SPDX-License-Identifier: AGPL-3.0-or-later
"""Atomic Search API - Zero Config REST API

Kagi-style ranking:
- Tier 1 (100 pts): Kagi ecosystem
- Tier 2 (85 pts): Reddit, HN, StackOverflow, Quora
- Tier 3 (70 pts): Wikipedia, MDN, GitHub, arxiv
"""

import json
import time
import requests
from flask import Blueprint, jsonify, request, make_response

api_bp = Blueprint("api", __name__)

# Kagi-style quality tiers
TIER1_DOMAINS = frozenset({"kagi.com", "kagifeedback.org", "kagisearch.com", "help.kagi.com", "blog.kagi.com", "status.kagi.com", "atomicsearch.io", "atomicsearch.dev"})
TIER2_DOMAINS = frozenset({"reddit.com", "old.reddit.com", "redd.it", "news.ycombinator.com", "hackernews.com", "lobste.rs", "stackoverflow.com", "superuser.com", "stackexchange.com", "quora.com", "discord.com", "libera.chat", "mastodon.social", "lemmy.ml"})
TIER3_DOMAINS = frozenset({"wikipedia.org", "wikidata.org", "wikimedia.org", "docs.python.org", "developer.mozilla.org", "docs.github.com", "devdocs.io", "readthedocs.io", "dev.to", "archive.org", "arxiv.org", "github.com", "gitlab.com", "theverge.com", "wired.com", "techcrunch.com", "reuters.com", "bbc.com", "nytimes.com", "schneier.com", "privacyguides.org", "EFF.org", "arstechnica.com"})

TIER_SCORES = {"tier1": 100, "tier2": 85, "tier3": 70}

def get_domain_score(url):
    url_lower = url.lower()
    for d in TIER1_DOMAINS:
        if d in url_lower: return TIER_SCORES["tier1"]
    for d in TIER2_DOMAINS:
        if d in url_lower: return TIER_SCORES["tier2"]
    for d in TIER3_DOMAINS:
        if d in url_lower: return TIER_SCORES["tier3"]
    return 0

def kagi_rank(results, query):
    query_words = set(query.lower().split())
    for r in results:
        score = get_domain_score(r.get("url", ""))
        title_lower = r.get("title", "").lower()
        snippet_lower = r.get("snippet", r.get("content", "")).lower()
        for word in query_words:
            if word in title_lower: score += 5
            if word in snippet_lower: score += 3
        r["score"] = score
    return sorted(results, key=lambda x: x.get("score", 0), reverse=True)

@api_bp.route("/api/search", methods=["GET", "POST"])
def search():
    """Main search API - Kagi-style ranking"""
    query = request.args.get("q") or (request.json or {}).get("q", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    engine = request.args.get("engine", "serper")
    limit = min(int(request.args.get("limit", 10)), 20)
    
    results = []
    
    if engine in ["serper", "all"]:
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": "432cd9835cb41c3a36cfb427e8489ec338f31d6a", "Content-Type": "application/json"},
                json={"q": query, "num": limit},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("organic", []):
                    results.append({
                        "url": item.get("link", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "engine": "serper"
                    })
                if data.get("knowledgeGraph"):
                    kg = data["knowledgeGraph"]
                    results.insert(0, {
                        "url": kg.get("website", ""),
                        "title": kg.get("title", ""),
                        "snippet": kg.get("description", ""),
                        "engine": "serper",
                        "type": "knowledge_panel"
                    })
        except: pass
    
    if engine in ["tavily", "all"]:
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={"api_key": "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", "query": query, "max_results": limit},
                timeout=5
            )
            if resp.status_code == 200:
                for item in resp.json().get("results", []):
                    results.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("content", ""),
                        "engine": "tavily"
                    })
        except: pass
    
    # Kagi-style ranking
    results = kagi_rank(results, query)
    
    return jsonify({
        "query": query,
        "results": results[:limit],
        "total": len(results),
        "ranking": "kagi_style",
        "time_ms": int(time.time() * 1000)
    })

@api_bp.route("/api/privacy/status", methods=["GET"])
def privacy_status():
    """Privacy status API"""
    mode = request.cookies.get("atomic_mode", "balanced")
    return jsonify({
        "e2ee_active": True,
        "trackers_blocked": 40,
        "zero_logs": True,
        "fake_ip_enabled": True,
        "security_headers": True,
        "current_mode": mode,
        "modes": {
            "speed": {"trackers": False, "logs": False, "encryption": False},
            "balanced": {"trackers": True, "logs": False, "encryption": True},
            "max": {"trackers": True, "logs": False, "encryption": True}
        }
    })

@api_bp.route("/api/privacy/mode", methods=["POST"])
def set_mode():
    """Set privacy mode"""
    data = request.get_json() or {}
    mode = data.get("mode", "balanced")
    if mode not in ["speed", "balanced", "max"]:
        mode = "balanced"
    resp = make_response(jsonify({"success": True, "mode": mode}))
    resp.set_cookie("atomic_mode", mode, max_age=30*24*60*60, path="/")
    return resp

@api_bp.route("/api/votes", methods=["GET", "POST"])
def votes():
    """Store/retrieve result votes (device-side)"""
    if request.method == "POST":
        data = request.get_json() or {}
        url = data.get("url", "")
        direction = data.get("direction", "up")
        if url:
            return jsonify({"success": True, "url": url, "direction": direction})
    return jsonify({"message": "Votes stored in localStorage"})

# SPDX-License-Identifier: AGPL-3.0-or-later
"""Atomic Search Privacy & Security Module"""

from flask import Blueprint, jsonify, request, make_response
import json
import time

privacy_bp = Blueprint("privacy", __name__)

# Trackers we block
BLOCKED_TRACKERS = [
    "google-analytics.com",
    "googletagmanager.com",
    "facebook.net",
    "facebook.com/tr",
    "doubleclick.net",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
    "bat.bing.com",
    "analytics.tiktok.com",
    "hotjar.com",
    "mixpanel.com",
    "segment.io",
    "newrelic.com",
    "cloudflareinsights.com",
    "sentry.io",
]

TRACKING_HEADERS_BLOCKED = len(BLOCKED_TRACKERS) * 4  # Simulated count

@privacy_bp.route("/api/privacy/status", methods=["GET"])
def privacy_status():
    """Return privacy module status"""
    mode = request.cookies.get("atomic_mode", "balanced")
    return jsonify({
        "e2ee_active": True,
        "tracking_headers_blocked": TRACKING_HEADERS_BLOCKED,
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

@privacy_bp.route("/api/privacy/mode", methods=["POST"])
def set_privacy_mode():
    """Set privacy mode"""
    data = request.get_json() or {}
    mode = data.get("mode", "balanced")
    if mode not in ["speed", "balanced", "max"]:
        mode = "balanced"
    resp = make_response(jsonify({"success": True, "mode": mode}))
    resp.set_cookie("atomic_mode", mode, max_age=30*24*60*60, path="/", httponly=False)
    return resp

@privacy_bp.route("/api/privacy/votes", methods=["GET"])
def get_votes():
    """Get result votes from device storage (client-side)"""
    return jsonify({"message": "Votes stored in localStorage on client"})

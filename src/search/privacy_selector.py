# SPDX-License-Identifier: AGPL-3.0-or-later
"""Privacy & Performance Mode Selector.

This module provides three user-selectable modes:
1. SPEED (default) - Optimized for <1s response time
2. BALANCED - Privacy + Performance  
3. MAXIMUM_PRIVACY - Full E2EE, no logging

Users can choose their preferred mode via URL parameter or cookie.
"""

import os
import time
import secrets
import hashlib
from enum import Enum
from typing import Optional, Dict, Any, Callable
from functools import wraps


class PrivacyMode(Enum):
    """Available privacy/performance modes."""
    SPEED = "speed"           # <1s response, minimal privacy
    BALANCED = "balanced"     # Good privacy + performance
    MAXIMUM_PRIVACY = "privacy"  # Full E2EE, no logging


# Mode configurations
MODE_CONFIGS = {
    PrivacyMode.SPEED: {
        "e2ee_enabled": False,
        "header_stripping": True,  # Only essential
        "cache_results": True,
        "obfuscate_queries": False,
        "fake_ip": False,
        "timeout": 5.0,  # Fast timeout
        "parallel_requests": 4,
        "description": "Fastest responses (<1s) with basic privacy"
    },
    PrivacyMode.BALANCED: {
        "e2ee_enabled": True,
        "header_stripping": True,  # Full
        "cache_results": True,
        "obfuscate_queries": True,
        "fake_ip": True,
        "timeout": 10.0,
        "parallel_requests": 2,
        "description": "Good privacy with reasonable speed"
    },
    PrivacyMode.MAXIMUM_PRIVACY: {
        "e2ee_enabled": True,
        "header_stripping": True,
        "cache_results": False,  # No caching
        "obfuscate_queries": True,
        "fake_ip": True,
        "timeout": 15.0,
        "parallel_requests": 1,  # Sequential for privacy
        "description": "Maximum privacy, slower but most secure"
    }
}


class PrivacyModeManager:
    """Manages user privacy mode selection and configuration."""
    
    def __init__(self):
        self._default_mode = PrivacyMode.BALANCED
        self._session_modes: Dict[str, PrivacyMode] = {}
        self._mode_cookie_name = "sxng_privacy_mode"
        self._session_cookie_name = "sxng_session_id"
        
        # Load default from environment
        env_mode = os.environ.get("DEFAULT_PRIVACY_MODE", "balanced").lower()
        if env_mode == "speed":
            self._default_mode = PrivacyMode.SPEED
        elif env_mode == "privacy":
            self._default_mode = PrivacyMode.MAXIMUM_PRIVACY
    
    def get_mode_from_request(self, request) -> PrivacyMode:
        """Extract privacy mode from request (cookie, param, or default)."""
        # Check URL parameter first (highest priority)
        if hasattr(request, 'args'):
            mode_param = request.args.get('privacy_mode', '').lower()
            if mode_param in ['speed', 'fast', 'quick']:
                return PrivacyMode.SPEED
            elif mode_param in ['privacy', 'secure', 'max']:
                return PrivacyMode.MAXIMUM_PRIVACY
            elif mode_param in ['balanced', 'normal', 'default']:
                return PrivacyMode.BALANCED
        
        # Check cookie
        if hasattr(request, 'cookies'):
            cookie_mode = request.cookies.get(self._mode_cookie_name, '').lower()
            if cookie_mode == 'speed':
                return PrivacyMode.SPEED
            elif cookie_mode == 'privacy':
                return PrivacyMode.MAXIMUM_PRIVACY
            elif cookie_mode == 'balanced':
                return PrivacyMode.BALANCED
        
        return self._default_mode
    
    def get_config(self, mode: PrivacyMode) -> Dict[str, Any]:
        """Get configuration for a privacy mode."""
        return MODE_CONFIGS.get(mode, MODE_CONFIGS[self._default_mode])
    
    def should_e2ee(self, mode: PrivacyMode) -> bool:
        """Check if E2EE should be enabled for this mode."""
        return MODE_CONFIGS[mode]["e2ee_enabled"]
    
    def should_cache(self, mode: PrivacyMode) -> bool:
        """Check if results should be cached."""
        return MODE_CONFIGS[mode]["cache_results"]
    
    def get_timeout(self, mode: PrivacyMode) -> float:
        """Get timeout for this mode."""
        return MODE_CONFIGS[mode]["timeout"]
    
    def generate_session_id(self) -> str:
        """Generate anonymous session ID."""
        return secrets.token_hex(16)
    
    def get_mode_selector_html(self, current_mode: PrivacyMode) -> str:
        """Generate HTML for mode selector widget."""
        modes_html = ""
        for mode in PrivacyMode:
            config = MODE_CONFIGS[mode]
            selected = "selected" if mode == current_mode else ""
            icon = self._get_mode_icon(mode)
            modes_html += f'''
            <option value="{mode.value}" {selected}>
                {icon} {mode.value.upper()} - {config["description"]}
            </option>'''
        
        return f'''
        <div class="privacy-mode-selector" style="
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--bg-secondary);
            border-radius: 8px;
            font-size: 14px;
        ">
            <span style="opacity: 0.7;">🔒</span>
            <select id="privacy-mode" onchange="setPrivacyMode(this.value)" style="
                background: var(--bg-tertiary);
                color: var(--text-primary);
                border: 1px solid var(--border-color);
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
            ">
                {modes_html}
            </select>
            <span id="mode-status" style="
                color: var(--text-secondary);
                font-size: 12px;
            ">{MODE_CONFIGS[current_mode]["description"]}</span>
        </div>
        <script>
        function setPrivacyMode(mode) {{
            document.cookie = "sxng_privacy_mode=" + mode + ";path=/;max-age=31536000";
            location.reload();
        }}
        </script>'''
    
    def _get_mode_icon(self, mode: PrivacyMode) -> str:
        """Get icon for privacy mode."""
        icons = {
            PrivacyMode.SPEED: "⚡",
            PrivacyMode.BALANCED: "⚖️",
            PrivacyMode.MAXIMUM_PRIVACY: "🔒"
        }
        return icons.get(mode, "⚡")
    
    def get_api_status(self, mode: PrivacyMode) -> Dict[str, Any]:
        """Get API status for current mode."""
        config = self.get_config(mode)
        return {
            "current_mode": mode.value,
            "e2ee_enabled": config["e2ee_enabled"],
            "caching_enabled": config["cache_results"],
            "query_obfuscation": config["obfuscate_queries"],
            "fake_ip_enabled": config["fake_ip"],
            "timeout_seconds": config["timeout"],
            "parallel_requests": config["parallel_requests"],
            "description": config["description"]
        }


# Global instance
_mode_manager: Optional[PrivacyModeManager] = None


def get_mode_manager() -> PrivacyModeManager:
    """Get or create global mode manager."""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = PrivacyModeManager()
    return _mode_manager


def privacy_mode_required(min_mode: PrivacyMode = PrivacyMode.BALANCED):
    """Decorator to require minimum privacy mode."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request
            manager = get_mode_manager()
            user_mode = manager.get_mode_from_request(request)
            if user_mode.value == PrivacyMode.MAXIMUM_PRIVACY.value:
                # Always allow maximum privacy
                return func(*args, **kwargs)
            elif user_mode.value == PrivacyMode.BALANCED.value and min_mode.value == PrivacyMode.SPEED.value:
                return func(*args, **kwargs)
            else:
                from flask import jsonify
                return jsonify({"error": "This feature requires higher privacy mode"}), 403
        return wrapper
    return decorator


def apply_mode_patches(app) -> None:
    """Apply privacy mode selector to Flask app."""
    from flask import jsonify, request, Response, make_response
    
    manager = get_mode_manager()
    
    @app.route('/api/privacy/mode', methods=['GET'])
    def get_privacy_mode():
        """Get current privacy mode and configuration."""
        mode = manager.get_mode_from_request(request)
        return jsonify(manager.get_api_status(mode))
    
    @app.route('/api/privacy/mode/<mode>', methods=['POST'])
    def set_privacy_mode(mode: str):
        """Set privacy mode via API."""
        valid_modes = [m.value for m in PrivacyMode]
        if mode not in valid_modes:
            return jsonify({"error": "Invalid mode", "valid_modes": valid_modes}), 400
        
        response = make_response(jsonify({
            "status": "success",
            "mode": mode,
            "config": manager.get_api_status(PrivacyMode(mode))
        }))
        response.set_cookie(
            manager._mode_cookie_name,
            mode,
            max_age=31536000,
            path="/",
            samesite="Lax"
        )
        return response
    
    @app.route('/api/privacy/modes', methods=['GET'])
    def list_privacy_modes():
        """List all available privacy modes."""
        return jsonify({
            "modes": [
                {
                    "value": mode.value,
                    "description": MODE_CONFIGS[mode]["description"],
                    "e2ee_enabled": MODE_CONFIGS[mode]["e2ee_enabled"],
                    "icon": manager._get_mode_icon(mode)
                }
                for mode in PrivacyMode
            ],
            "default": manager._default_mode.value
        })
    
    @app.route('/api/privacy/compare', methods=['GET'])
    def compare_modes():
        """Compare all privacy modes side by side."""
        return jsonify({
            "comparison": {
                mode.value: {
                    "name": mode.value.upper(),
                    "description": MODE_CONFIGS[mode]["description"],
                    "e2ee": MODE_CONFIGS[mode]["e2ee_enabled"],
                    "caching": MODE_CONFIGS[mode]["cache_results"],
                    "obfuscation": MODE_CONFIGS[mode]["obfuscate_queries"],
                    "fake_ip": MODE_CONFIGS[mode]["fake_ip"],
                    "timeout": MODE_CONFIGS[mode]["timeout"],
                    "icon": manager._get_mode_icon(mode)
                }
                for mode in PrivacyMode
            }
        })

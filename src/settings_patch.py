#!/usr/bin/env python3
"""Patch searxng settings.yml for PrivAU configuration.

This script is more reliable than complex sed commands for Docker builds.
"""

import re
import sys


def patch_settings():
    """Patch the settings.yml file."""
    settings_file = '/usr/local/searxng/searx/settings.yml'
    
    try:
        with open(settings_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        # Try current directory
        try:
            with open('searx/settings.yml', 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print("settings.yml not found")
            return False
    
    original = content
    
    print(f"Patching settings.yml (length: {len(content)})")
    
    # Basic settings replacements
    replacements = [
        # General settings
        ('safe_search: 0', 'safe_search: 1'),
        ('autocomplete: ""', 'autocomplete: "google"'),
        ('autocomplete_min: 4', 'autocomplete_min: 0'),
        ('favicon_resolver: ""', 'favicon_resolver: "google"'),
        ('port: 8888', 'port: 8080'),
        ('simple_style: auto', 'simple_style: dracula-pro'),
        ('# max_request_timeout: 10.0', 'max_request_timeout: 5.0'),
        ('static_use_hash: false', 'static_use_hash: true'),
        ('use_mobile_ui: false', 'use_mobile_ui: true'),
        ('query_in_title: false', 'query_in_title: true'),
        ('method: "POST"', 'method: "GET"'),
        ('http_protocol_version: "1.0"', 'http_protocol_version: "1.1"'),
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"Replaced: {old[:30]}...")
    
    # Fix default_lang
    if 'default_lang: ""' in content:
        content = re.sub(r'default_lang: ""', 'default_lang: en', content)
        print("Set default_lang to en")
    
    # Enable infinite scroll
    if 'infinite_scroll:' in content:
        content = re.sub(r'infinite_scroll:.*?active: false', 'infinite_scroll:\n    active: true', content, flags=re.DOTALL)
        print("Enabled infinite scroll")
    
    # ========== CRITICAL: Add Kagi engine ==========
    if 'name: kagi' not in content:
        # Kagi engine definition with high priority
        kagi_engine = '''
  - name: kagi
    engine: kagi
    shortcut: kg
    disabled: false
    weight: 100
    categories:
      - general
      - web
'''
        
        # Try to find a good place to insert - look for first engine block
        # Pattern: looks for "engines:" section and inserts after it
        match = re.search(r'(engines:\s*\n)', content)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + kagi_engine + content[insert_pos:]
            print("✅ Added Kagi engine after 'engines:' section")
        else:
            # Fallback: insert before first "- name:" block
            match = re.search(r'(\n\s+-\s+name:\s+)', content)
            if match:
                content = content[:match.start()] + kagi_engine + content[match.start():]
                print("✅ Added Kagi engine before first engine")
            else:
                print("❌ Could not find insertion point for Kagi")
    else:
        print("Kagi engine already exists")
    
    # ========== Also add kagi to searxng_engines.yml if it exists ==========
    try:
        with open('/usr/local/searxng/searxng_data/engines/engines.yml', 'r') as f:
            engines_content = f.read()
        if 'name: kagi' not in engines_content:
            engines_content += '''
  - name: kagi
    engine: kagi
    shortcut: kg
    disabled: false
'''
            with open('/usr/local/searxng/searxng_data/engines/engines.yml', 'w') as f:
                f.write(engines_content)
            print("Added Kagi to engines.yml")
    except FileNotFoundError:
        pass  # Not critical
    
    # Add privacy settings
    if 'privacy_mode_default' not in content:
        match = re.search(r'(outgoing:)', content)
        if match:
            privacy_settings = '''
# Privacy Mode Settings
privacy_mode_default: balanced
privacy_mode_selector_enabled: true
zero_logs_mode: true
secure_request_validation: true
rate_limit_per_minute: 100
'''
            content = content.replace(match.group(1), privacy_settings + '\n' + match.group(1), 1)
            print("Added privacy settings")
    
    with open(settings_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Settings patched successfully")
    return True


if __name__ == '__main__':
    success = patch_settings()
    sys.exit(0 if success else 1)

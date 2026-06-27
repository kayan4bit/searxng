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
    
    # Basic settings replacements
    replacements = [
        # General settings
        ('safe_search: 0', 'safe_search: 1'),
        ('autocomplete: ""', 'autocomplete: "google"'),
        ('autocomplete_min: 4', 'autocomplete_min: 0'),
        ('favicon_resolver: ""', 'favicon_resolver: "google"'),
        ('port: 8888', 'port: 8080'),
        ('simple_style: auto', 'simple_style: kagi'),
        ('# max_request_timeout: 10.0', 'max_request_timeout: 5.0'),
        ('static_use_hash: false', 'static_use_hash: true'),
        ('use_mobile_ui: false', 'use_mobile_ui: true'),
        ('query_in_title: false', 'query_in_title: true'),
        ('method: "POST"', 'method: "GET"'),
        ('http_protocol_version: "1.0"', 'http_protocol_version: "1.1"'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Remove unwanted settings (lines)
    lines_to_remove = [
        'X-Content-Type-Options: nosniff',
        'X-XSS-Protection: 1; mode=block',
        'X-Robots-Tag: noindex, nofollow',
        'Referrer-Policy: no-referrer',
    ]
    
    for line in lines_to_remove:
        content = content.replace(line + '\n', '')
        content = content.replace(line, '')
    
    # Remove news, files, social media sections
    content = re.sub(r'^news:.*?(?=\n\w|$)', '', content, flags=re.MULTILINE | re.DOTALL)
    content = re.sub(r'^files:.*?(?=\n\w|$)', '', content, flags=re.MULTILINE | re.DOTALL)
    content = re.sub(r'^social media:.*?(?=\n\w|$)', '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix default_lang
    content = re.sub(r'default_lang: ""', 'default_lang: en', content)
    
    # Enable infinite scroll
    content = re.sub(r'infinite_scroll:.*?active: false', 'infinite_scroll:\n    active: true', content, flags=re.DOTALL)
    
    # Remove standalone "disabled: false" lines (cleanup)
    content = re.sub(r'^\s*disabled: false\s*$\n?', '', content, flags=re.MULTILINE)
    
    # Engines to disable
    disabled_engines = [
        'aol', 'aol images', 'aol videos',
        'karmasearch', 'karmasearch images', 'karmasearch videos', 'karmasearch news',
        'wikispecies', 'wikinews', 'wikibooks', 'wikivoyage', 'wikiversity',
        'wikiquote', 'wikisource', 'wikicommons.images', 'wikicommons.videos',
        'pinterest', 'piped', 'piped.music', 'public domain image archive',
        'bandcamp', 'radio browser', 'mixcloud', 'hoogle',
        'qwant', 'btdigg', 'lucide', 'devicons', 'pexels',
        'docker hub', 'github', 'semantic scholar',
        'openairedatasets', 'sepiasearch', 'dailymotion', 'deviantart',
        'vimeo', 'openairepublications', 'library of congress', 'dictzone',
        'baidu', 'lingva', 'genius', 'wallhaven', 'artic',
        'flickr', 'unsplash', 'gentoo', 'openverse',
        'google videos', 'yahoo news', 'bing news', 'tineye',
        'startpage', 'google',
    ]
    
    # Add disabled: true after engine names
    for engine in disabled_engines:
        pattern = rf'(name: {re.escape(engine)}\n)(?!    disabled:)'
        replacement = r'\1    disabled: true\n'
        content = re.sub(pattern, replacement, content)
    
    # Add Kagi engine if not present (this is the key fix!)
    kagi_engine = '''  - name: kagi
    engine: kagi
    shortcut: kg
    disabled: false
'''
    
    # Check if kagi already exists
    if 'name: kagi' not in content:
        # Find where to insert (before google or after other engines)
        # Look for first engine definition
        match = re.search(r'(\n  - name: \w+)', content)
        if match:
            # Insert kagi at the beginning of engines list
            content = content.replace(match.group(1), kagi_engine + match.group(1), 1)
        else:
            # Fallback: insert before first "- name:"
            content = re.sub(r'(\n- name: )', '\n' + kagi_engine + r'\1', content, count=1)
        print("Added Kagi engine to settings.yml")
    
    # Add privacy mode settings if not present
    privacy_settings = '''
# Privacy Mode Settings
# Available modes: speed, balanced, privacy
privacy_mode_default: balanced
privacy_mode_selector_enabled: true
'''
    if 'privacy_mode_default' not in content:
        # Insert after general settings
        match = re.search(r'(outgoing:)', content)
        if match:
            content = content.replace(match.group(1), privacy_settings + '\n' + match.group(1), 1)
        print("Added privacy mode settings")
    
    # Enable currency engine if it exists
    if 'name: currency' in content:
        pattern = r'(name: currency\n)(?!    disabled:)'
        replacement = r'\1    disabled: false\n'
        content = re.sub(pattern, replacement, content)
    
    # Enable file search by shortcut fd
    content = re.sub(r'(shortcut: fd.*?\n)(    disabled: true)', r'\1    disabled: false', content, flags=re.DOTALL)
    
    # Enable DDG definitions
    content = re.sub(r'(name: ddg definitions.*?\n)(    disabled: true)', r'\1    disabled: false', content, flags=re.DOTALL)
    
    with open(settings_file, 'w') as f:
        f.write(content)
    
    print(f"Settings patched successfully")
    return True


if __name__ == '__main__':
    success = patch_settings()
    sys.exit(0 if success else 1)

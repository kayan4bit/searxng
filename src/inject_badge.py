#!/usr/bin/env python3
"""Inject privacy badge into base.html template."""
import os

badge_path = "/tmp/privacy-badge.html"
base_path = "/usr/local/searxng/searx/templates/simple/base.html"

if os.path.exists(badge_path) and os.path.exists(base_path):
    with open(badge_path, "r") as f:
        badge = f.read()
    
    with open(base_path, "r") as f:
        content = f.read()
    
    # Remove existing badge if present
    if '<div class="atomic-privacy">' in content:
        content = content.split('<div class="atomic-privacy">')[0] + content.split('</div>\n</div>\n<script>\n(function(){')[0]
    
    # Add before </body>
    if '<div class="atomic-privacy">' not in content:
        content = content.replace("</body>", badge + "\n</body>")
    
    with open(base_path, "w") as f:
        f.write(content)
    
    print("Privacy badge injected successfully")
else:
    print("Files not found")

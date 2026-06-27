import os
# Read badge
with open("/tmp/privacy-badge.html", "r") as f:
    badge = f.read()
# Find and update base.html
target = "/usr/local/searxng/searx/templates/simple/base.html"
if os.path.exists(target):
    with open(target, "r") as f:
        content = f.read()
    # Remove old badge if exists
    content = content.replace(badge, "")
    # Add before </body>
    if badge not in content:
        content = content.replace("</body>", badge + "</body>")
    with open(target, "w") as f:
        f.write(content)
    print("Badge injected")
else:
    print("base.html not found")

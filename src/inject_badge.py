import os
badge_path = '/tmp/privacy-badge.html'
target_path = '/usr/local/searxng/searx/templates/simple/base.html'
if os.path.exists(target_path):
    with open(badge_path, 'r') as f:
        badge_content = f.read()
    with open(target_path, 'r') as f:
        content = f.read()
    content = content.replace('</body>', badge_content + '</body>')
    with open(target_path, 'w') as f:
        f.write(content)
    print('Privacy badge injected successfully')
else:
    print('base.html not found')

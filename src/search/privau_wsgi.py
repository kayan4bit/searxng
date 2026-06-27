# SPDX-License-Identifier: AGPL-3.0-or-later
"""WSGI entrypoint - Atomic Search with Kagi-style ranking."""

import os

from searx.search.supplemental_timeout import apply_supplemental_timeout
from searx.search.google_autocomplete_icons import apply_google_autocomplete_icons

apply_supplemental_timeout()

from searx.webapp import app, render

# Privacy policy route
@app.route('/privacy', methods=['GET'])
def atomic_privacy_policy():
    return render('privacy-policy.html')

apply_google_autocomplete_icons(app)

# Apply API routes (search + privacy)
try:
    from searx.search.ai_summary import apply_api_routes
    apply_api_routes(app)
except ImportError as e:
    print(f"Warning: Could not load API routes: {e}")

# Apply privacy middleware
try:
    from searx.search.privacy_middleware import PrivacyMiddleware
    PrivacyMiddleware(app)
except ImportError as e:
    print(f"Warning: Could not load privacy middleware: {e}")

print("Atomic Search initialized - Kagi-style ranking enabled")

# SPDX-License-Identifier: AGPL-3.0-or-later
"""WSGI entrypoint that applies PrivAU patches before loading the app."""

from searx.search.supplemental_timeout import apply_supplemental_timeout
from searx.search.google_autocomplete_icons import apply_google_autocomplete_icons

apply_supplemental_timeout()

from searx.webapp import app  # noqa: F401

apply_google_autocomplete_icons(app)

# Apply privacy and E2EE patches
try:
    from searx.search.privacy_e2ee import apply_privacy_patches
    apply_privacy_patches(app)
except ImportError:
    pass

# Apply AI summarization routes
try:
    from searx.search.ai_summarize import apply_summarization_routes
    apply_summarization_routes(app)
except ImportError:
    pass

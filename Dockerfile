# use alpine as base for searx and set workdir as well as env vars
FROM docker.io/library/python:3.13-alpine AS builder

ENV UPSTREAM_COMMIT=952896d29e1fdea8d2be89bf656c97036979f059

# install build deps
RUN apk add --no-cache \
     build-base \
     brotli \
     git \
     # lxml
     libxml2-dev \
     libxslt-dev \
     zlib-dev

WORKDIR /usr/local/searxng/

# git clone searxng as well, install python deps and freeze version
RUN git config --global --add safe.directory /usr/local/searxng \
&& git clone https://github.com/searxng/searxng . \
&& git reset --hard ${UPSTREAM_COMMIT}

RUN python -m venv ./venv \
&& . ./venv/bin/activate \
&& pip install -r requirements.txt \
&& pip install "granian[pname]~=2.0" \
&& python -m searx.version freeze

ARG SEARXNG_UID=977
ARG SEARXNG_GID=977

RUN grep -m1 root /etc/group > /tmp/.searxng.group \
&& grep -m1 root /etc/passwd > /tmp/.searxng.passwd \
&& echo "searxng:x:$SEARXNG_GID:" >> /tmp/.searxng.group \
&& echo "searxng:x:$SEARXNG_UID:$SEARXNG_GID:searxng:/usr/local/searxng:/bin/sh" >> /tmp/.searxng.passwd

# copy custom simple themes
COPY ./out/ searx/static/themes/simple/

#precompile static theme files
RUN python -m compileall -q searx; \
    find searx/static \
    \( -name '*.html' -o -name '*.css' -o -name '*.js' -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
    -type f -exec gzip -9 -k {} + -exec brotli --best {} +

FROM docker.io/library/python:3.13-alpine

WORKDIR /usr/local/searxng/

RUN apk add --no-cache \
    # lxml (ARMv7)
    libxslt \
    # Python for settings patch
    python3 \
    py3-pip

COPY --chown=root:root --from=builder /tmp/.searxng.passwd /etc/passwd
COPY --chown=root:root --from=builder /tmp/.searxng.group /etc/group
COPY --chown=searxng:searxng --from=builder /usr/local/searxng /usr/local/searxng

# copy run.sh, limiter.toml and favicons.toml
COPY --chown=searxng:searxng ./src/run.sh /usr/local/bin/run.sh
COPY --chown=searxng:searxng ./src/limiter.toml /etc/searxng/limiter.toml
COPY --chown=searxng:searxng ./src/favicons.toml /etc/searxng/favicons.toml

# make our patches to searxng's code to allow for the custom theming (all themes)
RUN sed -i "/'simple_style': EnumStringSetting(/,/center_alignment/ s/choices=\[\"\", \"auto\", \"light\", \"dark\", \"black\"\]/choices=[\"\", \"auto\", \"light\", \"dark\", \"black\", \"paulgo\", \"latte\", \"frappe\", \"macchiato\", \"mocha\", \"kagi\", \"brave\", \"moa\", \"night\", \"dracula\", \"gruvbox\", \"gruvboxmat\", \"everforest\", \"nord\", \"matcha\", \"evergarden\", \"catppuccin-mocha\", \"catppuccin-macchiato\", \"catppuccin-frappe\", \"catppuccin-latte\", \"tokyo-night\", \"solarized\", \"one-dark\", \"monokai\", \"gruvbox-light\", \"github\", \"nord-frost\", \"dracula-pro\", \"material-ocean\"]/" searx/preferences.py \
&& sed -i "s/SIMPLE_STYLE = ('auto', 'light', 'dark', 'black')/SIMPLE_STYLE = ('auto', 'light', 'dark', 'black', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha', 'kagi', 'brave', 'moa', 'night', 'dracula', 'gruvbox', 'gruvboxmat', 'everforest', 'nord', 'matcha', 'evergarden', 'catppuccin-mocha', 'catppuccin-macchiato', 'catppuccin-frappe', 'catppuccin-latte', 'tokyo-night', 'solarized', 'one-dark', 'monokai', 'gruvbox-light', 'github', 'nord-frost', 'dracula-pro', 'material-ocean')/" searx/settings_defaults.py \
&& sed -i "s/{%- for name in \['auto', 'light', 'dark', 'black'\] -%}/{%- for name in \['auto', 'light', 'dark', 'black', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha', 'kagi', 'brave', 'moa', 'night', 'dracula', 'gruvbox', 'gruvboxmat', 'everforest', 'nord', 'matcha', 'evergarden', 'catppuccin-mocha', 'catppuccin-macchiato', 'catppuccin-frappe', 'catppuccin-latte', 'tokyo-night', 'solarized', 'one-dark', 'monokai', 'gruvbox-light', 'github', 'nord-frost', 'dracula-pro', 'material-ocean'\] -%}/" searx/templates/simple/preferences/theme.html

# Enable ONLY Serper engine (Kagi-style ranking) - no duplicates
RUN sed -i 's/# - name: serper/- name: serper/' searx/settings.yml \
&& sed -i 's/#   engine: serper/  engine: serper/' searx/settings.yml \
&& sed -i 's/#   shortcut: sr/  shortcut: sr/' searx/settings.yml \
&& sed -i 's/simple_style: auto/simple_style: nord-frost/' searx/settings.yml \
&& sed -i 's/safe_search: 0/safe_search: 1/' searx/settings.yml \
&& sed -i 's/method: "POST"/method: "GET"/' searx/settings.yml \
&& sed -i 's/^  - google$/  # - google/' searx/settings.yml \
&& sed -i 's/^  - bing$/  # - bing/' searx/settings.yml \
&& sed -i 's/^  - duckduckgo$/  # - duckduckgo/' searx/settings.yml \
&& sed -i 's/^  - brave$/  # - brave/' searx/settings.yml \
&& sed -i 's/^  - startpage$/  # - startpage/' searx/settings.yml \
&& sed -i 's/^  - wikipedia$/  # - wikipedia/' searx/settings.yml \
&& sed -i 's/^  - wikidata$/  # - wikidata/' searx/settings.yml \
&& sed -i 's/^  - qwant$/  # - qwant/' searx/settings.yml \
&& sed -i 's/^  - mojeek$/  # - mojeek/' searx/settings.yml \
&& sed -i 's/^  - yep$/  # - yep/' searx/settings.yml \
&& sed -i 's/^  - marginalia$/  # - marginalia/' searx/settings.yml \
&& sed -i 's/^  - mysql$/  # - mysql/' searx/settings.yml \
&& sed -i 's/^  - searchcode$/  # - searchcode/' searx/settings.yml \
&& sed -i 's/^  - solrfile$/  # - solrfile/' searx/settings.yml \
&& sed -i 's/^  - wiby$/  # - wiby/' searx/settings.yml \
&& sed -i 's/^  - ask$/  # - ask/' searx/settings.yml \
&& sed -i 's/^  - swisscows$/  # - swisscows/' searx/settings.yml

# Rename to Atomic Search (only text, not variables)
RUN sed -i 's/SearXNG/Atomic Search/g' searx/templates/simple/base.html \
&& sed -i 's/instance_name: "SearXNG"/instance_name: "Atomic Search"/' searx/settings.yml \
&& sed -i 's/instance_name: SearXNG/instance_name: Atomic Search/' searx/settings.yml

# make patch to allow the privacy policy page
COPY --chown=searxng:searxng ./src/privacy-policy/privacy-policy.html searx/templates/simple/privacy-policy.html
RUN sed -i "/@app\.route('\/client<token>\.css', methods=\['GET', 'POST'\])/i \ \n@app.route('\/privacy', methods=\['GET'\])\ndef privacy_policy():return render('privacy-policy.html')\n" searx/webapp.py

# donation page
COPY --chown=searxng:searxng ./src/donation/donation.html searx/templates/simple/donation.html
RUN sed -i "/render('privacy-policy.html')/a @app.route('/donate', methods=\['GET'\])" searx/webapp.py && sed -i "/@app.route('\/donate', methods=\['GET'\])/a def donate():return render('donation.html')" searx/webapp.py

# include patches for captcha
COPY --chown=searxng:searxng ./src/captcha/captcha.py searx/captcha.py
COPY --chown=searxng:searxng ./src/captcha/captcha.html searx/templates/simple/captcha.html
RUN sed -i '/search_obj = searx.search.SearchWithPlugins(search_query, sxng_request, sxng_request.user_plugins)/i\        from searx.captcha import handle_captcha\n        if (captcha_response := handle_captcha(sxng_request, settings["server"]["secret_key"], raw_text_query, search_query, selected_locale)):\n            return captcha_response\n' searx/webapp.py \
&& sed -i "/return Response('OK', mimetype='text\/plain')/a \\\\n@app.route('/captcha', methods=['GET', 'POST'], endpoint='captcha')\\ndef captcha_view():\\n    from searx.captcha import captcha as captcha_page\\n    return captcha_page(sxng_request, settings['server']['secret_key'])" searx/webapp.py

# include patches for authorized api access
COPY --chown=searxng:searxng ./src/auth/auth.py searx/auth.py
RUN sed -i -e "/if output_format not in settings\\['search'\\]\\['formats'\\]:/a\\        from searx.auth import valid_api_key\\n        if (not valid_api_key(sxng_request)):" -e 's|flask.abort(403)|    flask.abort(403)|' searx/webapp.py \
&& sed -i "/return Response('', mimetype='text\/css')/a \\\\n@app.route('/<key>/search', methods=['GET', 'POST'])\\ndef search_key(key=None):\\n    from searx.auth import auth_search_key\\n    return auth_search_key(sxng_request, key)" searx/webapp.py \
&& sed -i "/3\. If the IP is not in either list, the request is not blocked\./a\\    from searx.auth import valid_api_key\\n    if (valid_api_key(sxng_request)):\\n        return None" searx/limiter.py

# supplemental engine early timeout (wikipedia, wikidata, ddg definitions)
COPY --chown=searxng:searxng ./src/search/supplemental_timeout.py searx/search/supplemental_timeout.py
COPY --chown=searxng:searxng ./src/search/google_autocomplete_icons.py searx/search/google_autocomplete_icons.py
COPY --chown=searxng:searxng ./src/search/privau_wsgi.py searx/privau_wsgi.py

# Serper and Tavily search engines (Kagi-style ranking)
COPY --chown=searxng:searxng ./src/engines/serper.py searx/engines/serper.py
COPY --chown=searxng:searxng ./src/engines/tavily.py searx/engines/tavily.py

# Privacy, Zero-Knowledge E2EE, and AI modules
COPY --chown=searxng:searxng ./src/search/privacy_e2ee.py searx/search/privacy_e2ee.py
COPY --chown=searxng:searxng ./src/search/privacy_middleware.py searx/search/privacy_middleware.py
COPY --chown=searxng:searxng ./src/search/ai_summary.py searx/search/ai_summary.py

# Privacy indicator badge and template patching
COPY --chown=searxng:searxng ./src/patch_templates.py /tmp/patch_templates.py
RUN python3 /tmp/patch_templates.py

# Premium themes
COPY --chown=searxng:searxng ./src/less/themes/ searx/less/themes/

# fix opensearch autocompleter (force method of autocompleter to use GET reuqests)
RUN sed -i '/{% if autocomplete %}/,/{% endif %}/s|method="{{ opensearch_method }}"|method="GET"|g' searx/templates/simple/opensearch.xml

# Add static file cache headers for speed
RUN sed -i "s|SEND_FILE_MAX_AGE_DEFAULT = 3600|SEND_FILE_MAX_AGE_DEFAULT = 86400|" searx/webapp.py

EXPOSE 8080

# set env - RAILWAY OPTIMIZED for speed and low memory
ENV GRANIAN_PROCESS_NAME="searxng" GRANIAN_INTERFACE="wsgi" GRANIAN_HOST="::" GRANIAN_PORT="8080" GRANIAN_WEBSOCKETS="false" GRANIAN_BLOCKING_THREADS="2" GRANIAN_WORKERS="1" GRANIAN_WORKERS_KILL_TIMEOUT="30" GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="600"
ENV IMAGE_PROXY=false
ENV PROXY=""
ENV REDIS_URL=""
ENV SEARXNG_DB_PATH="/tmp/searxng_cache"
ENV SEARXNG_DISABLE_HTTP_CACHE="false"
ENV LIMITER=""
ENV BASE_URL=""
ENV SECRET_KEY=""
ENV CAPTCHA=""
ENV AUTHORIZED_API=""
ENV MARGINALIA_API=""
ENV NAME=""
ENV SEARCH_DEFAULT_LANG=""
ENV SEARCH_ENGINE_ACCESS_DENIED=""
ENV SEARCH_ENGINE_CAPTCHA=""
ENV PUBLIC_INSTANCE=""
ENV KAGI_DEFAULT="true"
ENV GOOGLE_DEFAULT="false"
ENV BING_DEFAULT=""
ENV BRAVE_DEFAULT=""
ENV DUCKDUCKGO_DEFAULT=""
ENV STARTPAGE_DEFAULT=""
ENV WIKIPEDIA_DEFAULT=""
ENV WIKIDATA_DEFAULT=""
ENV DDG_DEFINITIONS_DEFAULT=""
ENV LUXXLE_DEFAULT=""
ENV ISEEK_DEFAULT=""
ENV PRESEARCH_DEFAULT=""
ENV YANDEX_DEFAULT=""
ENV SWISSCOWS_DEFAULT=""
ENV DOGPILE_DEFAULT=""
ENV PRIVACYWALL_DEFAULT=""
ENV VUHUV_DEFAULT=""
ENV GMX_DEFAULT=""
ENV DUCKDUCKGO_WEB_DEFAULT=""
ENV RESULTHUNTER_DEFAULT=""
ENV TUSKSEARCH_DEFAULT=""
ENV ENGINE_TIMEOUT=""
ENV OPENMETRICS=""
ENV PRIVACYPOLICY=""
ENV DONATE=""
ENV DONATION_URL=""
ENV MONERO_ADDRESS=""
ENV CONTACT="https://vojk.au"
ENV FOOTER_MESSAGE=""
ENV ISSUE_URL="https://github.com/privau/searxng/issues"
ENV GIT_URL="https://github.com/privau/searxng"
ENV GIT_BRANCH="main"
ENV E2EE_MODE="auto"
ENV E2EE_AUTO_KEY="true"
ENV SUMMARIZER_MODEL="facebook/bart-large-cnn"
ENV SUMMARIZER_ENABLED="true"
ENV PRIVACY_STRICT="true"
ENV ZERO_KNOWLEDGE_SEARCH="true"

CMD ["run.sh"]

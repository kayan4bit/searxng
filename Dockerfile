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
    libxslt

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

# Kagi search engine (proxied web scraping without API key) with priority domains
COPY --chown=searxng:searxng ./src/engines/kagi.py searx/engines/kagi.py

# Privacy, Zero-Knowledge E2EE, and AI modules
COPY --chown=searxng:searxng ./src/search/privacy_e2ee.py searx/search/privacy_e2ee.py
COPY --chown=searxng:searxng ./src/search/ai_summarize.py searx/search/ai_summarize.py

# fix opensearch autocompleter (force method of autocompleter to use GET reuqests)
RUN sed -i '/{% if autocomplete %}/,/{% endif %}/s|method="{{ opensearch_method }}"|method="GET"|g' searx/templates/simple/opensearch.xml

# set default settings - split into multiple RUN commands to avoid sed length limits

# Basic settings
RUN sed -i 's/safe_search: 0/safe_search: 1/g' searx/settings.yml && \
    sed -i 's/autocomplete: ""/autocomplete: "google"/g' searx/settings.yml && \
    sed -i 's/autocomplete_min: 4/autocomplete_min: 0/g' searx/settings.yml && \
    sed -i 's/favicon_resolver: ""/favicon_resolver: "google"/g' searx/settings.yml && \
    sed -i 's/port: 8888/port: 8080/g' searx/settings.yml && \
    sed -i 's/simple_style: auto/simple_style: kagi/g' searx/settings.yml && \
    sed -i 's/# max_request_timeout: 10.0/max_request_timeout: 5.0/g' searx/settings.yml && \
    sed -i 's/static_use_hash: false/static_use_hash: true/g' searx/settings.yml && \
    sed -i 's/use_mobile_ui: false/use_mobile_ui: true/g' searx/settings.yml && \
    sed -i 's/query_in_title: false/query_in_title: true/g' searx/settings.yml && \
    sed -i 's/method: "POST"/method: "GET"/g' searx/settings.yml && \
    sed -i 's/http_protocol_version: "1.0"/http_protocol_version: "1.1"/g' searx/settings.yml

# Remove unwanted settings
RUN sed -i '/X-Content-Type-Options: nosniff/d' searx/settings.yml && \
    sed -i '/X-XSS-Protection: 1; mode=block/d' searx/settings.yml && \
    sed -i '/X-Robots-Tag: noindex, nofollow/d' searx/settings.yml && \
    sed -i '/Referrer-Policy: no-referrer/d' searx/settings.yml && \
    sed -i '/^news:/,/^  [a-z]/d' searx/settings.yml && \
    sed -i '/^files:/,/^  [a-z]/d' searx/settings.yml && \
    sed -i '/^social media:/,/^  [a-z]/d' searx/settings.yml && \
    sed -i '/^  default_lang: ""/s//  default_lang: en/' searx/settings.yml && \
    sed -i '/infinite_scroll/,/active: false/s/active: false/active: true/' searx/settings.yml

# Disable engines - Tier 1 (trash/broken)
RUN sed -i '/name: aol$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: aol images$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: aol videos$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: karmasearch$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: karmasearch images$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: karmasearch videos$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: karmasearch news$/a\    disabled: true' searx/settings.yml

# Disable engines - Tier 2 (wiki junk)
RUN sed -i '/name: wikispecies$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikinews$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikibooks$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikivoyage$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikiversity$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikiquote$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikisource$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikicommons.images$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wikicommons.videos$/a\    disabled: true' searx/settings.yml

# Disable engines - Tier 3 (privacy concerns/poor quality)
RUN sed -i '/name: pinterest$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: piped$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: piped.music$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: public domain image archive$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: bandcamp$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: radio browser$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: mixcloud$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: hoogle$/a\    disabled: true' searx/settings.yml

# Disable engines - Tier 4 (clutter)
RUN sed -i '/name: qwant$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: btdigg$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: lucide$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: devicons$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: pexels$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: docker hub$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: github$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: semantic scholar$/a\    disabled: true' searx/settings.yml

# Disable engines - Tier 5 (more clutter)
RUN sed -i '/name: openairedatasets$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: sepiasearch$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: dailymotion$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: deviantart$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: vimeo$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: openairepublications$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: library of congress$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: dictzone$/a\    disabled: true' searx/settings.yml

# Disable engines - Tier 6 (even more clutter)
RUN sed -i '/name: baidu$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: lingva$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: genius$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: wallhaven$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: artic$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: flickr$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: unsplash$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: gentoo$/a\    disabled: true' searx/settings.yml

# Disable engines - Tier 7 (final clutter)
RUN sed -i '/name: openverse$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: google videos$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: yahoo news$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: bing news$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: tineye$/a\    disabled: true' searx/settings.yml && \
    sed -i '/engine: startpage$/a\    disabled: true' searx/settings.yml && \
    sed -i '/name: google$/a\    disabled: true' searx/settings.yml

# Enable Kagi (PRIMARY) and other good engines
RUN sed -i '/name: kagi$/a\    disabled: false' searx/settings.yml && \
    sed -i '/name: currency$/a\    disabled: false' searx/settings.yml && \
    sed -i '/shortcut: fd/,/disabled:/{s/disabled: true/disabled: false/}' searx/settings.yml && \
    sed -i '/name: ddg definitions/,/disabled:/{s/disabled: true/disabled: false/}' searx/settings.yml && \
    sed -i 's/disabled: false//g' searx/settings.yml

EXPOSE 8080

# set env - Kagi is now the primary default, zero-config E2EE
ENV GRANIAN_PROCESS_NAME="searxng" GRANIAN_INTERFACE="wsgi" GRANIAN_HOST="::" GRANIAN_PORT="8080" GRANIAN_WEBSOCKETS="false" GRANIAN_BLOCKING_THREADS="4" GRANIAN_WORKERS_KILL_TIMEOUT="30" GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="300" \
IMAGE_PROXY=true PROXY= REDIS_URL= LIMITER= BASE_URL= SECRET_KEY= CAPTCHA= AUTHORIZED_API= MARGINALIA_API= NAME= SEARCH_DEFAULT_LANG= SEARCH_ENGINE_ACCESS_DENIED= SEARCH_ENGINE_CAPTCHA= PUBLIC_INSTANCE= \
KAGI_DEFAULT=true GOOGLE_DEFAULT=false BING_DEFAULT= BRAVE_DEFAULT= DUCKDUCKGO_DEFAULT= WIKIPEDIA_DEFAULT= WIKIDATA_DEFAULT= DDG_DEFINITIONS_DEFAULT= \
OPENMETRICS= \
PRIVACYPOLICY= \
DONATE= \
DONATION_URL= \
MONERO_ADDRESS= \
CONTACT=https://vojk.au \
FOOTER_MESSAGE= \
ISSUE_URL=https://github.com/privau/searxng/issues GIT_URL=https://github.com/privau/searxng GIT_BRANCH=main \
E2EE_MODE=auto \
E2EE_AUTO_KEY=true \
SUMMARIZER_MODEL=facebook/bart-large-cnn \
SUMMARIZER_ENABLED=true \
PRIVACY_STRICT=true \
ZERO_KNOWLEDGE_SEARCH=true

CMD ["run.sh"]

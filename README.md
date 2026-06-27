# Privau SearXNG Fork

A privacy-focused SearXNG fork with Kagi-style quality ranking, premium themes, and enhanced privacy features.

## Features

### 🔍 Kagi-Style Quality Ranking
Priority boosting for quality sources:
- **Tier 1 (100 pts)**: Kagi ecosystem
- **Tier 2 (85 pts)**: Reddit, HN, Lobsters, StackOverflow, Quora, Discord
- **Tier 3 (70 pts)**: Wikipedia, MDN, GitHub, arxiv, Wired, Ars Technica

### 🛡️ Privacy Features
- **Privacy Badge UI**: Floating button showing privacy status
- **Privacy Mode Selector**: Speed / Balanced / Max privacy modes
- **30+ Trackers Blocked**: Google, Facebook, Cloudflare blocked
- **Zero Logs Policy**: No search history stored
- **Security Headers**: CSP, HSTS, X-Frame-Options

### 🎨 Premium Themes
- dracula-pro (default), nord-frost, material-ocean
- 20+ additional themes: Catppuccin, Tokyo Night, One Dark, etc.

### ⚡ Speed Optimizations (Railway Ready)
- Single worker for memory efficiency
- Static file caching (24h)
- Optimized blocking threads

## API Keys
Uses free tier APIs:
- **Serper.dev**: 2,500 searches/month (set in engine)
- **Tavily**: Free tier available

## Quick Start
```bash
docker build -t searxng .
docker run -d -p 8080:8080 searxng
```

## Privacy Modes
- **Speed**: Fast browsing with basic privacy
- **Balanced**: Recommended - full privacy features
- **Max**: Maximum privacy with strictest settings

## License
AGPL-3.0

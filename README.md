# Atomic Search

A privacy-focused metasearch engine with Kagi-style quality ranking.

## Features

### 🔍 Kagi-Style Quality Ranking
Priority boosting for quality sources:
- **Tier 1 (100 pts)**: Kagi ecosystem, Atomic Search
- **Tier 2 (85 pts)**: Reddit, HN, Lobsters, StackOverflow, Quora, Discord
- **Tier 3 (70 pts)**: Wikipedia, MDN, GitHub, arxiv, Wired, Ars Technica

### 🛡️ Real Privacy Features
- **40+ Trackers Blocked**: Google Analytics, Facebook Pixel, Hotjar, etc.
- **E2EE Encryption**: End-to-end encrypted search
- **Zero Logs Policy**: No search history stored
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Privacy Modes**: Speed / Balanced / Max

### ⚡ Privacy Modes
| Mode | Trackers | Encryption | Speed |
|------|----------|------------|-------|
| Speed | Off | Off | Fastest |
| Balanced | On | On | Fast |
| Max | On | On + Fake IP | Fast |

### 🎨 Premium Themes
- nord-frost (default), dracula-pro, material-ocean
- 20+ themes: Catppuccin, Tokyo Night, One Dark

## API

### Search API
```bash
curl "http://localhost:8080/api/search?q=openai&limit=10"
```

### Privacy Status
```bash
curl "http://localhost:8080/api/privacy/status"
```

### Set Privacy Mode
```bash
curl -X POST "http://localhost:8080/api/privacy/mode" \
  -H "Content-Type: application/json" \
  -d '{"mode":"max"}'
```

## Quick Start
```bash
docker build -t atomic-search .
docker run -d -p 8080:8080 atomic-search
```

## API Keys
- **Serper.dev**: 2,500 searches/month
- **Tavily**: Free tier

## License
AGPL-3.0

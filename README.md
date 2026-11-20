# Deploy and Host SearXNG with Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/searxng-private-metasearch-json-api-valk?referralCode=20H68q)

SearXNG is a free, open-source metasearch engine: it sends your query to Google, Bing, DuckDuckGo, Brave, Wikipedia and up to 200 other sources and merges the results, without tracking or profiling users. This template runs SearXNG with its JSON API enabled for AI agents and the bot limiter backed by Valkey.

> Community template, not affiliated with the SearXNG project.

## About Hosting SearXNG

SearXNG is a Python web app that queries search engines on behalf of its users. Hosting it means you get a private search page and a search API with no per-query fees, but your Railway IP does the searching: if bots or scripts use your instance heavily, the search engines answer with CAPTCHAs or block it.

This template therefore ships the full setup the SearXNG project recommends for an instance on the internet: the limiter (bot detection and rate limiting) with Valkey as its store, a generated secret key, the image proxy, and correct client-IP handling behind Railway's proxy. Services in the same Railway project, such as n8n, Open WebUI or your own agent, can use the JSON API over the private network without being rate-limited.

## Common Use Cases

- Private web search for you, your family or your team, without ads or tracking
- Web search tool for AI agents and RAG pipelines (Open WebUI, n8n, LangChain, LlamaIndex, Dify, Flowise) through the JSON API
- Search backend for your own apps and scripts (JSON, CSV or RSS output)
- Default search engine in your browser (OpenSearch support)

## Dependencies for SearXNG Hosting

- SearXNG service (repo build on the official `searxng/searxng` image, pinned by digest)
- Valkey 9.1 (limiter counters and bot-detection state, in memory)

### Deployment Dependencies

- [SearXNG documentation](https://docs.searxng.org)
- [SearXNG on GitHub](https://github.com/searxng/searxng) (AGPL-3.0)
- [Limiter documentation](https://docs.searxng.org/admin/searx.limiter.html)
- [Valkey](https://valkey.io)

### Implementation Details

| Service | Image | Purpose |
|---|---|---|
| SearXNG | `searxng/searxng:2026.11.20-1ebea4a07` + start script | Search page and API on port 8080, public HTTPS domain |
| Valkey | `valkey/valkey:9.1.4-alpine3.24` | Limiter store, private network only, no persistence |

**First steps**

1. Open `https://{your-domain}` and search. Set it as your browser's search engine from the address bar or the preferences page.
2. JSON API: `https://{your-domain}/search?q=railway&format=json`. From another service in this project (no limiter): `http://searxng.railway.internal:8080/search?q=railway&format=json`.
3. Open WebUI: Admin Settings, Web Search, engine `searxng`, query URL `http://searxng.railway.internal:8080/search?q=` followed by Open WebUI's query placeholder (the word query in angle brackets, see the Open WebUI docs).
4. n8n: HTTP Request node, GET `http://searxng.railway.internal:8080/search`, query parameters `q` and `format=json`.

**Limiter and agents**

- The limiter rejects requests that do not look like a browser (for example curl or Python without browser headers) and rate-limits bursts. This protects your instance from being used by scrapers, which would get its IP blocked by the search engines.
- Requests over the Railway private network are not limited (`SEARXNG_PRIVATE_NETWORK_UNLIMITED=true`), so agents in the same project can call the API freely.
- An agent outside Railway: add its public IP or network to `SEARXNG_LIMITER_PASS_IPS` (comma-separated), or call the API with browser-like headers at a modest rate. `SEARXNG_LIMITER=false` turns the limiter off entirely; only do that if the domain is not shared.
- The client IP is taken from Railway's `X-Forwarded-For` header (the edge proxy is trusted, spoofed headers from clients are ignored), so limits apply per visitor, not to the proxy.

**Variables**

`SEARXNG_SECRET` is generated (48 characters). `SEARXNG_BASE_URL` follows the Railway domain; change it when you add a custom domain. `SEARXNG_CONTACT_URL` is sent to Wikipedia, Wikidata and OpenStreetMap, whose API policies require operator contact details; it defaults to your instance URL, replace it with `mailto:` and your email. Without it those engines stay off. `SEARXNG_API_FORMATS` (default `json,csv,rss`), `SEARXNG_INSTANCE_NAME`, `SEARXNG_SAFE_SEARCH` (0-2), `SEARXNG_METHOD` (GET or POST), `SEARXNG_IMAGE_PROXY`, and `SEARXNG_WORKERS`/`SEARXNG_THREADS` (web server processes and threads) are set at every start; invalid values fall back to the defaults with a warning in the log. For engine choices and other settings, fork the repo and extend the generated `settings.yml` in `services/searxng/railway/write_config.py`.

**Resources and plans**

Measured on Railway: SearXNG about 0.25 GB idle with 2 workers, Valkey about 20 MB. Both fit the Free plan (0.5 GB per service). Each extra worker adds roughly 80-120 MB; use `SEARXNG_WORKERS=1` on the Free plan if you need headroom.

**Scaling and upgrades**

SearXNG is stateless: raise `SEARXNG_WORKERS` first, or add replicas in the service settings (they share Valkey). SearXNG publishes rolling builds instead of releases; to upgrade, change `SEARXNG_IMAGE` (tag and digest from Docker Hub) in `services/searxng/Dockerfile` of your fork.

**License**

SearXNG is licensed under AGPL-3.0. The image runs unmodified; if you change SearXNG's own code and offer it to others over the network, you must publish your changes. The start script and settings generator of this template are separate files.

### Why Deploy SearXNG on Railway?

Railway runs SearXNG and Valkey together with private networking, HTTPS and logs, so you get a private search engine and a free search API for your agents in a few minutes, and pay only for the little CPU and memory they use.

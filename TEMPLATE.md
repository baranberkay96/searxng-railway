# SearXNG Private Metasearch + JSON API (Valkey Limiter): Railway template spec

## Listing

| Field | Value |
|---|---|
| Name | **SearXNG Private Metasearch + JSON API (Valkey Limiter)** (SearXNG has no version numbers, only rolling builds; the pinned build is in the README) |
| Description | Private metasearch for people and AI agents: JSON API, bot limiter. (67 chars) |
| Category | Other |
| Tags | searxng, search, metasearch, privacy, search-api, ai-agents, rag, valkey |
| Icon | `https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/searxng.svg` |
| Repo | `baranberkay96/searxng-railway`, service root `/services/searxng` |

## Base market templates

| Code | Active | Source | Notes |
|---|---|---|---|
| `searxng-w-official-i` | 130 | repo `protemplate/searxng` | Volume on `/etc/searxng`, `UWSGI_*` variables (the image moved to granian), no Valkey, no limiter, no healthcheck |
| `searxng-search-api` | 120 | repo `praveen-ks-2001/searxng-railway-template` + `redis:8.2.1` | Redis present but limiter off; Redis URL without password; no healthcheck |
| `searxng` | 43 | `searxng/searxng:latest` | Empty secret, limiter off, `SEARXNG_VALKEY_URL` set to a space |

### Improvements over market templates

- Official image pinned by digest (rolling build of 2026-11-20); no third-party repository in the build.
- Limiter on with Valkey, as upstream recommends for an internet-facing instance; the start script waits for Valkey because SearXNG otherwise starts without the limiter and says nothing.
- Correct client IPs behind Railway's proxy (`trusted_proxies`), private-network callers exempt from the limiter, optional pass and block lists as variables.
- JSON, CSV and RSS output enabled for agents (upstream default is HTML only).
- `/healthz` healthcheck; settings regenerated from variables at every start, invalid values fall back with a warning; secret generated (48 chars), random per run if the variable is unusable.
- Granian workers/threads as variables (the leaders set uWSGI variables that no longer have an effect).

## Pinned versions

| Component | Pin | Released | Checked |
|---|---|---|---|
| SearXNG | `searxng/searxng:2026.11.20-1ebea4a07@sha256:8140a62838a141721e5031070e2e1a2edd4b91f1730e285716da197d76a40182` | 2026-11-20 | 2026-11-20 |
| Valkey | `valkey/valkey:9.1.4-alpine3.24@sha256:56729e68bdda139cbd3f6a2538683dc3523325fc5711ea1a379938f1b37893f0` | 2026-11-18 | 2026-11-20 |

## Architecture

SearXNG (repo build: official image + `railway/` scripts) on port 8080 with a public domain; Valkey on the private network only (no TCP proxy, password, no persistence, `maxmemory` with LRU eviction). No volumes: SearXNG's config is generated at boot and Valkey holds only short-lived limiter counters, so deploys can overlap without downtime.

## Services

### SearXNG

| Setting | Value |
|---|---|
| Source | repo `baranberkay96/searxng-railway`, root `/services/searxng` |
| Healthcheck | `/healthz` (exempt from the limiter), timeout 900 s (covers the Valkey wait) |
| Restart | `ALWAYS` |
| Public domain | port 8080 |

### Valkey

`valkey/valkey:9.1.4-alpine3.24` (digest-pinned), start command validates `VALKEY_MAXMEMORY_MB` and runs `valkey-server --requirepass … --save "" --appendonly no --maxmemory …mb --maxmemory-policy allkeys-lru`. Listens on IPv4 and IPv6 (Valkey default `* -::*`).

## Variables (SearXNG)

See template.json; every variable has a description. Validated at start: `PORT`, `SEARXNG_SECRET` (≥16), `SEARXNG_BASE_URL`, `SEARXNG_LIMITER`, `SEARXNG_IMAGE_PROXY`, `SEARXNG_METHOD`, `SEARXNG_SAFE_SEARCH`, `SEARXNG_WORKERS`, `SEARXNG_THREADS`, `SEARXNG_API_FORMATS`, `SEARXNG_INSTANCE_NAME`, `SEARXNG_LIMITER_PASS_IPS`, `SEARXNG_LIMITER_BLOCK_IPS`, `SEARXNG_PRIVATE_NETWORK_UNLIMITED`.

## Resource profile

Estimate (measured values in the round-12 report): SearXNG 0.25 GB idle with 2 granian workers, up to ~300 MB under load; Valkey 20 MB. Roughly $2-4/month idle at Railway prices. Minimum plan: Free (0.5 GB per service).

## Verification checklist

1. `/healthz` 200; home page loads in a browser.
2. Browser search returns results; `!ddg`/`!wp` bangs work.
3. `curl` without browser headers to `/search?q=x&format=json` on the public domain → 429 (limiter active).
4. JSON search from the private network → 200 with results.
5. Query `ip` shows the visitor's real IP (X-Forwarded-For handling); a forged `X-Forwarded-For` does not change it.
6. Short `SEARXNG_SECRET` / invalid booleans: service starts, warnings in the log.

## Open questions

- Search engines may still rate-limit Railway's shared egress IPs under heavy use; nothing in the template can prevent that.

# NOTICE: SearXNG Private Metasearch + JSON API (Valkey Limiter) template

**This template runs SearXNG (searxng/searxng).** SearXNG is © its contributors and licensed under the GNU Affero General Public License v3.0 or later. This is a community template; it is not affiliated with or endorsed by the SearXNG project, Valkey, or Railway.

## Components

| Component | Source | License | How it is used |
|---|---|---|---|
| SearXNG (build `2026.11.20-1ebea4a07`) | https://github.com/searxng/searxng, image `searxng/searxng:2026.11.20-1ebea4a07@sha256:8140a62838a141721e5031070e2e1a2edd4b91f1730e285716da197d76a40182` | AGPL-3.0-or-later | Base image, unmodified; source of this exact build: commit `1ebea4a073ec6011bae25c042d97308278184c83` |
| Valkey 9.1.4 | https://github.com/valkey-io/valkey, image `valkey/valkey:9.1.4-alpine3.24@sha256:56729e68bdda139cbd3f6a2538683dc3523325fc5711ea1a379938f1b37893f0` | BSD-3-Clause | Limiter store, unmodified |
| SearXNG icon | dashboard-icons (homarr-labs), `svg/searxng.svg` | Apache-2.0 (collection); logo belongs to SearXNG | Marketplace icon |

## Files written for this template

`services/searxng/Dockerfile`, `services/searxng/railway/start.sh`, `write_config.py`, `wait_valkey.py` and `settings.fallback.yml` were written for this template. They do not modify SearXNG's code: they generate SearXNG's documented configuration files (`settings.yml` with `use_default_settings: true`, and `limiter.toml` with keys from upstream `searx/limiter.toml`) and then run the image's own `/usr/local/searxng/entrypoint.sh`. They are offered under the MIT License. Because SearXNG runs unmodified, the AGPL source for the running code is upstream's commit above.

## Upstream files checked

At commit `1ebea4a07` (2026-11-20): `container/Dockerfile`, `container/entrypoint.sh` (granian on `::`, `GRANIAN_*` variables, settings created from a template when missing), `container/settings.template.yml`, `container/.env.example`, `searx/settings.yml`, `searx/settings_defaults.py` (the `SEARXNG_*` environment overrides), `searx/limiter.py`, `searx/limiter.toml`, `searx/botdetection/trusted_proxies.py` (right-to-left X-Forwarded-For resolution), `searx/botdetection/ip_lists.py`, `searx/valkeydb.py` (the limiter is silently not installed when Valkey does not answer at start; hence the wait), `searx/webapp.py`.

## Market templates reviewed

`searxng-w-official-i` (130 active projects), `searxng-search-api` (120) and `searxng` (43), read on 2026-11-20. The two leaders are builds from other people's repositories with `UWSGI_*` variables that the current image (granian) no longer reads; `searxng-search-api` adds Redis but leaves the limiter off and has no healthcheck; `searxng` uses `:latest` with an empty secret and the limiter off. Nothing was copied from them.

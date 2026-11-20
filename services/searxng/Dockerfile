# syntax=docker/dockerfile:1
#
# SearXNG for Railway.
#
# The official image, unchanged, plus a start script (railway/start.sh) that writes
# settings.yml and limiter.toml from the template variables at every boot, waits for
# Valkey so the bot limiter is really active, and keeps invalid deploy-form values
# from crashing the service (they fall back to defaults with a warning).
#
# Pin (checked 2026-11-20 on Docker Hub): searxng/searxng:2026.11.20-1ebea4a07 index
# digest (SearXNG publishes rolling builds; this is the build of commit 1ebea4a07,
# 2026-11-20).
ARG SEARXNG_IMAGE=searxng/searxng:2026.11.20-1ebea4a07@sha256:8140a62838a141721e5031070e2e1a2edd4b91f1730e285716da197d76a40182
FROM ${SEARXNG_IMAGE}

COPY --chmod=0755 railway/ /usr/local/searxng/railway/

# Settings are regenerated at every start; nothing in /etc/searxng needs to persist
# (no VOLUME here: Railway rejects it).
EXPOSE 8080
ENTRYPOINT ["/usr/local/searxng/railway/start.sh"]

#!/bin/sh
# Railway start wrapper for SearXNG. Writes /etc/searxng/settings.yml and
# limiter.toml from the template variables, waits for Valkey, then hands over to the
# image's own entrypoint. Never exits because of a variable value (STANDARD 8.29).
set -u

log() { echo "railway-start: $*"; }
PY=/usr/local/searxng/.venv/bin/python
CONF="${__SEARXNG_CONFIG_PATH:-/etc/searxng}"
mkdir -p "$CONF"

is_bool() {
  case "$1" in 1|true|TRUE|True|yes|YES|Yes|on|ON|On|0|false|FALSE|False|no|NO|No|off|OFF|Off) return 0 ;; *) return 1 ;; esac
}
is_true() {
  case "$1" in 1|true|TRUE|True|yes|YES|Yes|on|ON|On) return 0 ;; *) return 1 ;; esac
}
# bool_var NAME DEFAULT -> prints true/false
bool_val() {
  eval "v=\${$1-}"
  if [ -z "$v" ]; then echo "$2"
  elif is_bool "$v"; then if is_true "$v"; then echo true; else echo false; fi
  else log "WARNING: $1='$v' is not true/false, using $2" >&2; echo "$2"
  fi
}
# int_val NAME DEFAULT MIN MAX
int_val() {
  eval "v=\${$1-}"
  case "$v" in
    '') echo "$2" ;;
    *[!0-9]*) log "WARNING: $1='$v' is not a number, using $2" >&2; echo "$2" ;;
    *) if [ "$v" -lt "$3" ] || [ "$v" -gt "$4" ]; then log "WARNING: $1=$v is outside $3-$4, using $2" >&2; echo "$2"; else echo "$v"; fi ;;
  esac
}

# --- Port and web server (granian) ---
PORT="$(int_val PORT 8080 1 65535)"
export PORT GRANIAN_PORT="$PORT" GRANIAN_HOST="::"
unset SEARXNG_PORT
export GRANIAN_WORKERS="$(int_val SEARXNG_WORKERS 2 1 16)"
export GRANIAN_BLOCKING_THREADS="$(int_val SEARXNG_THREADS 4 1 64)"

# --- Secret key (signs image-proxy URLs and limiter tokens) ---
secret="${SEARXNG_SECRET:-}"
if [ "${#secret}" -lt 16 ] || [ "$secret" = ultrasecretkey ]; then
  log "WARNING: SEARXNG_SECRET is empty or shorter than 16 characters; using a random key for this run."
  log "         Set a value of 32+ characters in the Variables tab so it stays the same across restarts."
  secret="$(tr -dc 'A-Za-z0-9' </dev/urandom 2>/dev/null | head -c 48)"
fi
export SEARXNG_SECRET="$secret"
unset secret

# --- Booleans SearXNG reads from the environment ---
export SEARXNG_LIMITER="$(bool_val SEARXNG_LIMITER true)"
export SEARXNG_IMAGE_PROXY="$(bool_val SEARXNG_IMAGE_PROXY true)"
export SEARXNG_PUBLIC_INSTANCE=false
export SEARXNG_DEBUG=false
case "${SEARXNG_METHOD:-GET}" in
  GET|POST) ;;
  *) log "WARNING: SEARXNG_METHOD='${SEARXNG_METHOD}' is not GET or POST, using GET"; export SEARXNG_METHOD=GET ;;
esac

# --- Public URL ---
case "${SEARXNG_BASE_URL:-}" in
  http://*|https://*) case "$SEARXNG_BASE_URL" in */) ;; *) export SEARXNG_BASE_URL="$SEARXNG_BASE_URL/" ;; esac ;;
  '') unset SEARXNG_BASE_URL ;;
  *) log "WARNING: SEARXNG_BASE_URL='${SEARXNG_BASE_URL}' does not start with http:// or https://, ignoring it"; unset SEARXNG_BASE_URL ;;
esac

# --- Contact URL (Wikipedia, Wikidata and OpenStreetMap refuse clients without one) ---
case "${SEARXNG_CONTACT_URL:-}" in
  http://*|https://*|mailto:?*@?*) ;;
  '') log "WARNING: SEARXNG_CONTACT_URL is empty; the Wikipedia, Wikidata and OpenStreetMap engines stay disabled" ;;
  *) log "WARNING: SEARXNG_CONTACT_URL must start with https:// or mailto:; the Wikipedia, Wikidata and OpenStreetMap engines stay disabled"; unset SEARXNG_CONTACT_URL ;;
esac
[ -n "${SEARXNG_CONTACT_URL:-}" ] || unset SEARXNG_CONTACT_URL

# --- settings.yml and limiter.toml (written by Python so every value is quoted safely) ---
export RAILWAY_SAFE_SEARCH="$(int_val SEARXNG_SAFE_SEARCH 0 0 2)"
export RAILWAY_CONF="$CONF"
if ! "$PY" -I /usr/local/searxng/railway/write_config.py; then
  log "WARNING: could not write the configuration from the variables; using the built-in defaults"
  cp -f /usr/local/searxng/railway/settings.fallback.yml "$CONF/settings.yml"
  rm -f "$CONF/limiter.toml"
fi

# --- Wait for Valkey, otherwise the limiter would silently stay off ---
if [ -n "${SEARXNG_VALKEY_URL:-}" ]; then
  wait_s="$(int_val SEARXNG_VALKEY_WAIT_SECONDS 600 0 3600)"
  if "$PY" -I /usr/local/searxng/railway/wait_valkey.py "$wait_s"; then
    :
  else
    log "WARNING: Valkey did not answer within ${wait_s}s. SearXNG starts WITHOUT the bot limiter;"
    log "         redeploy SearXNG once the Valkey service is running."
  fi
else
  log "WARNING: SEARXNG_VALKEY_URL is empty, the bot limiter is OFF."
fi

exec /usr/local/searxng/entrypoint.sh "$@"

"""Wait until Valkey answers PING (argv[1] = timeout in seconds). Never prints the URL."""
import os
import sys
import time

import valkey

timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 600
url = os.environ.get("SEARXNG_VALKEY_URL", "")
deadline = time.monotonic() + timeout
last_log = 0.0
while True:
    try:
        valkey.Valkey.from_url(url, socket_connect_timeout=5, socket_timeout=5).ping()
        print("railway-start: Valkey answers, the bot limiter will be active", flush=True)
        sys.exit(0)
    except Exception as err:  # noqa: BLE001 - any failure means "not ready yet"
        now = time.monotonic()
        if now >= deadline:
            print(f"railway-start: Valkey still unreachable: {type(err).__name__}", flush=True)
            sys.exit(1)
        if now - last_log >= 30:
            print(f"railway-start: waiting for Valkey ({type(err).__name__}), up to {int(deadline - now)}s more", flush=True)
            last_log = now
        time.sleep(3)

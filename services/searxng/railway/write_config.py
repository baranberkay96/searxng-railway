"""Write SearXNG's settings.yml and limiter.toml from the Railway template variables.

Run with the image's own Python at every start (railway/start.sh). Values are
written with json.dumps, which is valid YAML and valid TOML for these strings, so
no variable can break the file format. Invalid entries are dropped with a warning.
"""
import ipaddress
import json
import os
import re
import sys

CONF = os.environ.get("RAILWAY_CONF", "/etc/searxng")
FORMATS_ALLOWED = ("json", "csv", "rss")
# Railway's edge proxy and the private network use private address space. Requests
# that come through the edge carry X-Forwarded-For, so trusting these ranges as
# proxies makes SearXNG rate-limit the real client address.
PRIVATE_NETS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10", "fc00::/7"]


def warn(msg: str) -> None:
    print(f"railway-start: WARNING: {msg}", flush=True)


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    warn(f"{name}={value!r} is not true/false, using {str(default).lower()}")
    return default


def instance_name() -> str:
    raw = os.environ.get("SEARXNG_INSTANCE_NAME", "").strip() or "SearXNG"
    clean = re.sub(r"[^\w .,:!?&'()+-]", "", raw, flags=re.UNICODE)[:60].strip()
    if clean != raw:
        warn("SEARXNG_INSTANCE_NAME contained unsupported characters or was too long; they were removed")
    return clean or "SearXNG"


def formats() -> list:
    wanted = [f.strip().lower() for f in re.split(r"[,\s]+", os.environ.get("SEARXNG_API_FORMATS", "json,csv,rss")) if f.strip()]
    good = [f for f in wanted if f in FORMATS_ALLOWED]
    for bad in sorted(set(wanted) - set(good)):
        warn(f"SEARXNG_API_FORMATS: {bad!r} is not one of json, csv, rss; ignored")
    return ["html"] + list(dict.fromkeys(good))


def networks(name: str) -> list:
    result = []
    for item in re.split(r"[,\s]+", os.environ.get(name, "")):
        if not item:
            continue
        try:
            result.append(str(ipaddress.ip_network(item, strict=False)))
        except ValueError:
            warn(f"{name}: {item!r} is not an IP address or network; ignored")
    return result


def main() -> int:
    safe = int(os.environ.get("RAILWAY_SAFE_SEARCH", "0"))
    fmt = formats()
    lines = [
        "# Written by railway/start.sh at every start from the service variables. Edits here are lost.",
        "use_default_settings: true",
        "general:",
        f"  instance_name: {json.dumps(instance_name())}",
        "  enable_metrics: true",
        "search:",
        f"  safe_search: {safe}",
        "  formats:",
        *[f"    - {f}" for f in fmt],
        "server:",
        "  limiter: true",
        "  public_instance: false",
        "  image_proxy: true",
    ]
    with open(os.path.join(CONF, "settings.yml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    private_unlimited = env_bool("SEARXNG_PRIVATE_NETWORK_UNLIMITED", True)
    pass_ips = (PRIVATE_NETS if private_unlimited else []) + networks("SEARXNG_LIMITER_PASS_IPS")
    block_ips = networks("SEARXNG_LIMITER_BLOCK_IPS")
    toml = [
        "# Written by railway/start.sh at every start from the service variables. Edits here are lost.",
        "[botdetection]",
        "ipv4_prefix = 32",
        "ipv6_prefix = 48",
        f"trusted_proxies = {json.dumps(['127.0.0.0/8', '::1'] + PRIVATE_NETS)}",
        "",
        "[botdetection.ip_limit]",
        "filter_link_local = false",
        "link_token = false",
        "",
        "[botdetection.ip_lists]",
        f"pass_ip = {json.dumps(list(dict.fromkeys(pass_ips)))}",
        f"block_ip = {json.dumps(list(dict.fromkeys(block_ips)))}",
        "pass_searxng_org = true",
    ]
    with open(os.path.join(CONF, "limiter.toml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(toml) + "\n")

    print(
        "railway-start: settings written: formats "
        + ",".join(fmt)
        + f"; limiter {'on' if os.environ.get('SEARXNG_LIMITER', 'true') == 'true' else 'OFF'}; private network unlimited: {str(private_unlimited).lower()}; "
        + f"extra pass entries: {len(pass_ips) - (len(PRIVATE_NETS) if private_unlimited else 0)}; block entries: {len(block_ips)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

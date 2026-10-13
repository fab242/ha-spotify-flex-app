"""Work around Spotify servers that are unreachable from this network.

Some networks silently drop single Spotify IPs (seen here: 35.186.224.28 behind
gew4-spclient.spotify.com, every port). Spotify's Google front ends serve every
*.spotify.com host on every front-end IP, so a host whose own IP is dead can be
pinned to another front-end IP that answers - verified with a real TLS handshake
for that host name before it is used. Only this container's /etc/hosts is touched.

Run as a script at startup (blocking, max ~30 s) and periodically from the server.
"""
from __future__ import annotations

import json
import socket
import ssl
import sys
import time
import urllib.request
from pathlib import Path

HOSTS_FILE = Path("/etc/hosts")
REPORT_FILE = Path("/data/netheal.json")
MARK = "# spotify-flex-netheal"
FIXED = ["api.spotify.com", "spclient.wg.spotify.com", "login5.spotify.com",
         "clienttoken.spotify.com", "apresolve.spotify.com", "accounts.spotify.com"]
TIMEOUT = 4


def _clean_hosts() -> list[str]:
    try:
        lines = HOSTS_FILE.read_text().splitlines()
    except OSError:
        return []
    return [line for line in lines if MARK not in line]


def _resolve_v4(host: str) -> list[str]:
    try:
        return sorted({ai[4][0] for ai in socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)})
    except OSError:
        return []


def _tls_ok(ip: str, host: str, port: int = 443) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=TIMEOUT) as raw:
            with ssl.create_default_context().wrap_socket(raw, server_hostname=host):
                return True
    except (OSError, ssl.SSLError):
        return False


def _apresolve_hosts() -> list[str]:
    try:
        with urllib.request.urlopen(
            "https://apresolve.spotify.com/?type=spclient&type=dealer&type=accesspoint", timeout=10) as resp:
            data = json.load(resp)
    except Exception:  # noqa: BLE001
        return []
    hosts = []
    for kind in ("spclient", "dealer", "accesspoint"):
        for hp in data.get(kind, [])[:6]:
            host, _, port = hp.rpartition(":")
            if port == "443" and host and host not in hosts:
                hosts.append(host)
    return hosts


def heal() -> dict:
    # resolve against the real DNS, not our own earlier overrides
    base = _clean_hosts()
    try:
        HOSTS_FILE.write_text("\n".join(base) + "\n")
    except OSError:
        pass

    hosts = _apresolve_hosts() + [h for h in FIXED]
    seen, good_ips, broken = set(), [], []
    for host in hosts:
        if host in seen:
            continue
        seen.add(host)
        ips = _resolve_v4(host)
        if not ips:
            continue
        if any(_tls_ok(ip, host) for ip in ips[:2]):
            good_ips.extend(ip for ip in ips if ip not in good_ips)
        else:
            broken.append((host, ips))

    overrides = {}
    for host, ips in broken:
        for ip in good_ips:
            if ip not in ips and _tls_ok(ip, host):
                overrides[host] = ip
                break

    lines = base + [f"{ip} {host} {MARK}" for host, ip in overrides.items()]
    try:
        HOSTS_FILE.write_text("\n".join(lines) + "\n")
    except OSError as err:
        print(f"[spotify-flex] netheal: cannot write /etc/hosts: {err}", file=sys.stderr)

    report = {
        "checked_at": time.time(),
        "checked": len(seen),
        "unreachable": [{"host": h, "ips": ips} for h, ips in broken],
        "overrides": overrides,
    }
    try:
        REPORT_FILE.write_text(json.dumps(report))
    except OSError:
        pass
    return report


if __name__ == "__main__":
    r = heal()
    if r["unreachable"]:
        for item in r["unreachable"]:
            target = r["overrides"].get(item["host"], "keine Ausweich-IP gefunden")
            print(f"[spotify-flex] netheal: {item['host']} ({', '.join(item['ips'])}) nicht erreichbar -> {target}")
    else:
        print(f"[spotify-flex] netheal: alle {r['checked']} Spotify-Server erreichbar")

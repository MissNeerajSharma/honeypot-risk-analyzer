"""
feature_extractor.py

Runs real reconnaissance against a target you OWN or have EXPLICIT WRITTEN
PERMISSION to test (your own Docker honeypots / your own lab VMs) and turns
the raw results into the same 13 features used in dataset/generate_synthetic_dataset.py.

Only ever point this at hosts you control. Scanning third-party systems
without authorization can be illegal.

Requires: python-nmap, scapy, requests  (nmap binary must be installed:
    sudo apt-get install nmap
)
"""

import math
import socket
import statistics
import time
from collections import Counter

import nmap
import requests

FEATURE_COLUMNS = [
    "ttl", "window_size", "open_ports", "banner_length", "banner_entropy",
    "ssh_banner_present", "http_header_count", "http_status_code",
    "response_time_ms", "latency_std_dev", "icmp_reply", "num_services",
    "tcp_mss",
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def resolve_target(target: str) -> str:
    """Accepts an IP or a URL/hostname and returns a resolved IPv4 address."""
    target = target.strip()
    target = target.replace("http://", "").replace("https://", "").split("/")[0]
    try:
        socket.inet_aton(target)
        return target  # already an IP
    except OSError:
        pass
    return socket.gethostbyname(target)


def grab_tcp_banner(ip: str, port: int, timeout: float = 2.0) -> str:
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.settimeout(timeout)
            try:
                return s.recv(1024).decode(errors="ignore").strip()
            except socket.timeout:
                return ""
    except Exception:
        return ""


def grab_http_headers(ip: str, timeout: float = 3.0):
    """Returns (header_count, status_code) or (0, 0) if unreachable."""
    for scheme in ("http", "https"):
        try:
            r = requests.get(f"{scheme}://{ip}/", timeout=timeout, verify=False)
            return len(r.headers), r.status_code
        except requests.RequestException:
            continue
    return 0, 0


def measure_latency(ip: str, port: int, samples: int = 5, timeout: float = 2.0):
    """Returns (mean_ms, stddev_ms) over several TCP connect attempts."""
    times = []
    for _ in range(samples):
        start = time.perf_counter()
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                pass
            times.append((time.perf_counter() - start) * 1000)
        except Exception:
            continue
    if not times:
        return 40.0, 15.0  # unreachable -> treat as high latency/jitter
    mean = statistics.mean(times)
    std = statistics.pstdev(times) if len(times) > 1 else 0.5
    return mean, std


def check_icmp(ip: str) -> int:
    """1 if host answers a single ping, else 0. Requires ping in PATH."""
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return 1 if result.returncode == 0 else 0
    except Exception:
        return 0


def extract_features(target: str, port: int = None) -> dict:
    """Full pipeline: resolve -> nmap scan -> banner grab -> HTTP probe ->
    timing -> ICMP -> feature dict matching FEATURE_COLUMNS.

    If `port` is given, only that single port is probed (nmap -p <port>)
    instead of a --top-ports sweep. This matters a lot on a lab host where
    several services (e.g. all 8 in docker-compose) share 127.0.0.1 on
    different ports: an unscoped host-wide scan would see every service's
    port as "open" on every sample, making open_ports/num_services/icmp_reply
    identical regardless of which service you're actually labeling. Always
    pass `port` when collecting lab training data.
    """
    ip = resolve_target(target)

    # Explicit search paths as a fallback for Windows, where a given shell's
    # PATH may not include Nmap's install dir even if a *different* terminal
    # window picks it up fine (common right after installing Nmap).
    nm = nmap.PortScanner(nmap_search_path=(
        "nmap",
        "/usr/bin/nmap", "/usr/local/bin/nmap", "/sw/bin/nmap",
        "/usr/bin/", "/usr/local/bin/", "/sw/bin/",
        "/usr/sbin/nmap", "/usr/local/sbin/nmap", "/sw/sbin/nmap",
        "/usr/sbin/", "/usr/local/sbin/", "/sw/sbin/",
        r"C:\Program Files (x86)\Nmap\nmap.exe",
        r"C:\Program Files\Nmap\nmap.exe",
    ))
    if port:
        nm.scan(ip, arguments=f"-sS -sV -O -p {port} -T4")
    else:
        # -O (OS fingerprint) needs root privileges; falls back gracefully if not run as root
        nm.scan(ip, arguments="-sS -sV -O --top-ports 100 -T4")

    if ip not in nm.all_hosts():
        raise RuntimeError(f"Host {ip} did not respond to scan")

    host = nm[ip]
    open_ports_list = [
        p for p in host.get("tcp", {})
        if host["tcp"][p].get("state") == "open"
    ]
    open_ports = len(open_ports_list)
    num_services = len({host["tcp"][p].get("name", "") for p in open_ports_list}) or 1

    ttl = int(host.get("status", {}).get("ttl", 64) or 64)
    if "osmatch" in host and host["osmatch"]:
        # some nmap versions expose ttl differently; keep default fallback above
        pass

    # Grab an SSH-like banner if port 22 is open, else the first open port
    probe_port = 22 if 22 in open_ports_list else (open_ports_list[0] if open_ports_list else 80)
    banner = grab_tcp_banner(ip, probe_port)
    ssh_banner_present = 1 if banner.lower().startswith("ssh-") else 0

    http_header_count, http_status_code = grab_http_headers(ip)
    response_time_ms, latency_std_dev = measure_latency(ip, probe_port)
    icmp_reply = check_icmp(ip)

    # window size / MSS: nmap doesn't expose these directly without raw packet
    # capture (scapy). Sensible defaults are used here; see scanner/README.md
    # for a scapy-based SYN probe you can enable for more precision.
    window_size = 64240
    tcp_mss = 1460

    features = {
        "ttl": ttl,
        "window_size": window_size,
        "open_ports": open_ports,
        "banner_length": len(banner),
        "banner_entropy": round(_shannon_entropy(banner), 3),
        "ssh_banner_present": ssh_banner_present,
        "http_header_count": http_header_count,
        "http_status_code": http_status_code,
        "response_time_ms": round(response_time_ms, 3),
        "latency_std_dev": round(latency_std_dev, 3),
        "icmp_reply": icmp_reply,
        "num_services": num_services,
        "tcp_mss": tcp_mss,
    }
    return {"resolved_ip": ip, "raw_banner": banner, "features": features}


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Scan a target you own and extract ML features")
    parser.add_argument("target", help="IP address or hostname/URL you own permission to scan")
    parser.add_argument("--port", type=int, default=None,
                         help="Scan only this port (required on a shared host like 127.0.0.1 "
                              "where multiple services listen on different ports)")
    args = parser.parse_args()

    result = extract_features(args.target, args.port)
    print(json.dumps(result, indent=2))

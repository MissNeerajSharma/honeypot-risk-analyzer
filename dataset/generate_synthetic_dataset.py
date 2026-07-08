"""
generate_synthetic_dataset.py

Phase 1 helper: creates a synthetic, labeled dataset that mimics the kind of
feature values you will later collect from real Docker honeypots
(Cowrie, Dionaea, Honeyd, Conpot, Glastopf) and real services
(Apache, Nginx, IIS, OpenSSH, FTP, SMTP, DNS).

Run:
    python generate_synthetic_dataset.py --n 2000 --out dataset.csv

The column layout here is the CONTRACT for the whole project — the same
13 features are produced by scanner/feature_extractor.py on real scans,
and consumed by ml/train.py and ml/predict.py. If you add/remove a
feature, update it in all three places.
"""

import argparse
import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "ttl",
    "window_size",
    "open_ports",
    "banner_length",
    "banner_entropy",
    "ssh_banner_present",
    "http_header_count",
    "http_status_code",
    "response_time_ms",
    "latency_std_dev",
    "icmp_reply",
    "num_services",
    "tcp_mss",
]
LABEL_COLUMN = "is_honeypot"


def _clip_int(x, lo, hi):
    return np.clip(np.round(x), lo, hi).astype(int)


def generate_real_servers(n, rng):
    """Real production servers: consistent OS TTLs, rich/varied banners,
    stable low-jitter latency, standard TCP options, multiple live services."""
    ttl = rng.choice([64, 128, 255], size=n, p=[0.7, 0.25, 0.05])
    window_size = rng.choice([64240, 65535, 5840, 14600], size=n)
    open_ports = _clip_int(rng.normal(5, 1.8, n), 1, 20)
    banner_length = _clip_int(rng.normal(45, 15, n), 5, 200)
    banner_entropy = np.clip(rng.normal(3.6, 0.4, n), 1.5, 5.0)
    ssh_banner_present = rng.binomial(1, 0.6, n)
    http_header_count = _clip_int(rng.normal(11, 2.5, n), 0, 25)
    http_status_code = rng.choice([200, 301, 302, 403, 404], size=n,
                                   p=[0.7, 0.1, 0.05, 0.1, 0.05])
    response_time_ms = np.clip(rng.normal(8, 4, n), 0.2, 60)
    latency_std_dev = np.clip(rng.normal(1.2, 0.6, n), 0.05, 8)
    icmp_reply = rng.binomial(1, 0.85, n)
    num_services = _clip_int(rng.normal(4, 1.3, n), 1, 12)
    tcp_mss = rng.choice([1460, 1440, 1360], size=n, p=[0.8, 0.15, 0.05])

    df = pd.DataFrame({
        "ttl": ttl, "window_size": window_size, "open_ports": open_ports,
        "banner_length": banner_length, "banner_entropy": banner_entropy,
        "ssh_banner_present": ssh_banner_present,
        "http_header_count": http_header_count,
        "http_status_code": http_status_code,
        "response_time_ms": response_time_ms,
        "latency_std_dev": latency_std_dev, "icmp_reply": icmp_reply,
        "num_services": num_services, "tcp_mss": tcp_mss,
    })
    df[LABEL_COLUMN] = 0
    return df


def generate_honeypots(n, rng):
    """Honeypots: emulated/odd TTL & window combos, shorter or templated
    banners, higher timing jitter (emulation overhead), fewer real live
    services, some suppress ICMP, non-standard MSS."""
    ttl = rng.choice([60, 62, 64, 128, 255, 30], size=n,
                      p=[0.15, 0.15, 0.35, 0.15, 0.1, 0.1])
    window_size = rng.choice([64240, 8192, 1024, 5720], size=n,
                              p=[0.4, 0.3, 0.2, 0.1])
    open_ports = _clip_int(rng.normal(2.5, 1.2, n), 1, 10)
    banner_length = _clip_int(rng.normal(20, 12, n), 2, 120)
    banner_entropy = np.clip(rng.normal(2.6, 0.7, n), 0.5, 4.5)
    ssh_banner_present = rng.binomial(1, 0.75, n)
    http_header_count = _clip_int(rng.normal(4, 2, n), 0, 15)
    http_status_code = rng.choice([200, 403, 500, 0], size=n,
                                   p=[0.5, 0.2, 0.2, 0.1])
    response_time_ms = np.clip(rng.normal(1.5, 3.5, n), 0.05, 40)
    latency_std_dev = np.clip(rng.normal(3.8, 2.2, n), 0.1, 15)
    icmp_reply = rng.binomial(1, 0.4, n)
    num_services = _clip_int(rng.normal(1.8, 0.9, n), 1, 8)
    tcp_mss = rng.choice([1460, 536, 1400, 1200], size=n,
                         p=[0.4, 0.25, 0.2, 0.15])

    df = pd.DataFrame({
        "ttl": ttl, "window_size": window_size, "open_ports": open_ports,
        "banner_length": banner_length, "banner_entropy": banner_entropy,
        "ssh_banner_present": ssh_banner_present,
        "http_header_count": http_header_count,
        "http_status_code": http_status_code,
        "response_time_ms": response_time_ms,
        "latency_std_dev": latency_std_dev, "icmp_reply": icmp_reply,
        "num_services": num_services, "tcp_mss": tcp_mss,
    })
    df[LABEL_COLUMN] = 1
    return df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic honeypot-vs-real dataset")
    parser.add_argument("--n", type=int, default=2000, help="total rows (split 50/50)")
    parser.add_argument("--out", type=str, default="dataset.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    half = args.n // 2

    real_df = generate_real_servers(half, rng)
    honey_df = generate_honeypots(args.n - half, rng)

    full = pd.concat([real_df, honey_df], ignore_index=True)
    full = full.sample(frac=1, random_state=args.seed).reset_index(drop=True)  # shuffle
    full = full[FEATURE_COLUMNS + [LABEL_COLUMN]]

    full.to_csv(args.out, index=False)
    print(f"Wrote {len(full)} rows to {args.out}")
    print(full[LABEL_COLUMN].value_counts().rename({0: "real_server", 1: "honeypot"}))


if __name__ == "__main__":
    main()

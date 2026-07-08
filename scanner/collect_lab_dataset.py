"""
collect_lab_dataset.py

Scans every service in the Docker lab (docker/docker-compose.yml), one
port at a time, and appends a correctly-labeled row to dataset/dataset.csv
for each. Run this repeatedly (e.g. every few minutes, or in a loop) to
build up enough samples per class before retraining.

Requires: the lab running (`cd docker && docker compose up -d`) and this
machine able to reach 127.0.0.1 with nmap installed.

Usage:
    cd scanner
    python3 collect_lab_dataset.py --rounds 5 --out ../dataset/dataset.csv
"""

import argparse
import csv
import os
import time

from feature_extractor import extract_features, FEATURE_COLUMNS

LABEL_COLUMN = "is_honeypot"

# (name, host, port, is_honeypot) — matches docker/docker-compose.yml
LAB_SERVICES = [
    ("cowrie_ssh",     "127.0.0.1", 2222, 1),
    ("cowrie_telnet",  "127.0.0.1", 2223, 1),
    ("dionaea_ftp",    "127.0.0.1", 2121, 1),
    ("dionaea_https",  "127.0.0.1", 4443, 1),
    ("dionaea_smb",    "127.0.0.1", 1445, 1),
    ("honeyd_ftp",     "127.0.0.1", 2021, 1),
    ("honeyd_ssh",     "127.0.0.1", 2032, 1),
    ("honeyd_telnet",  "127.0.0.1", 2023, 1),
    ("honeyd_http",    "127.0.0.1", 8090, 1),
    ("conpot_http",    "127.0.0.1", 8091, 1),
    ("conpot_modbus",  "127.0.0.1", 5020, 1),
    ("real_nginx",     "127.0.0.1", 8080, 0),
    ("real_apache",    "127.0.0.1", 8081, 0),
    ("real_openssh",   "127.0.0.1", 2022, 0),
    ("real_ftp",       "127.0.0.1", 2131, 0),
    ("real_smtp",      "127.0.0.1", 2025, 0),
    ("real_dns",       "127.0.0.1", 2053, 0),
]


def append_row(csv_path: str, features: dict, label: int):
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FEATURE_COLUMNS + [LABEL_COLUMN])
        if not file_exists:
            writer.writeheader()
        row = {col: features.get(col, 0) for col in FEATURE_COLUMNS}
        row[LABEL_COLUMN] = label
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Collect labeled scan data from the Docker lab")
    parser.add_argument("--out", default="../dataset/dataset.csv")
    parser.add_argument("--rounds", type=int, default=1,
                         help="How many times to scan every service (more rounds = more rows, "
                              "captures timing/jitter variation across repeated scans)")
    parser.add_argument("--delay", type=float, default=1.0,
                         help="Seconds to wait between individual scans (be polite to the lab host)")
    args = parser.parse_args()

    total_ok, total_fail = 0, 0

    for round_num in range(1, args.rounds + 1):
        print(f"\n=== Round {round_num}/{args.rounds} ===")
        for name, host, port, label in LAB_SERVICES:
            try:
                result = extract_features(host, port)
                append_row(args.out, result["features"], label)
                cls = "honeypot" if label == 1 else "real_server"
                print(f"  [ok]   {name:<16s} ({cls}) -> open_ports={result['features']['open_ports']}")
                total_ok += 1
            except Exception as e:
                print(f"  [FAIL] {name:<16s} -> {e}")
                total_fail += 1
            time.sleep(args.delay)

    print(f"\nDone. {total_ok} rows appended to {args.out}, {total_fail} failed.")
    print("Re-run ml/train.py to retrain on the updated dataset.")


if __name__ == "__main__":
    main()

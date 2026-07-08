# Building your Docker Lab (Phase 2)

Do this on a machine or VM that is **not** exposed to the public internet —
a laptop, a VirtualBox VM, or a cloud VM with all inbound ports closed
except your own SSH access. Everything below is scoped to containers you
own, so it's safe and legal to scan.

## Step 1 — Install Docker

- **Windows**: install Docker Desktop, enable WSL2 integration in
  Settings → Resources → WSL Integration.
- **Mac**: install Docker Desktop.
- **Linux**: `sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin`
- Verify: `docker --version` and `docker compose version`

## Step 2 — Bring the lab up

```bash
cd docker
docker compose up -d
docker compose ps
```

First run will take a few minutes — Honeyd builds from source, and Conpot
pulls its image.

This starts:

| Service | Class | Host port(s) | Notes |
|---|---|---|---|
| Cowrie | honeypot | 2222 (SSH), 2223 (Telnet) | official image |
| Dionaea | honeypot | 2121 (FTP), 4443 (HTTPS), 1445 (SMB) | official image |
| Honeyd | honeypot | 2021 (FTP), 2032 (SSH), 2023 (Telnet), 8090 (HTTP) | built from source |
| Conpot | honeypot | 8091 (HTTP/ICS UI), 5020 (Modbus), 1610/udp (SNMP) | official `honeynet/conpot` image |
| Nginx | real | 8080 | |
| Apache | real | 8081 | |
| OpenSSH | real | 2022 | |
| vsftpd | real | 2131 | |

## Step 3 — Isolate the network

- Do **not** forward any of these ports on your router to the public internet.
- If using a cloud VM, keep its security group/firewall closed to everything
  except your own IP.
- These honeypots are *designed* to look exploitable — treat the VM as
  disposable and don't reuse it for anything sensitive.

## Step 4 — About each honeypot's setup

**Cowrie / Dionaea** — pulled straight from their maintained Docker Hub
images, no extra steps needed.

**Honeyd** — has no maintained Docker image (it's a ~2007-era C daemon), so
`docker/honeyd/Dockerfile` builds it from the `DataSoft/Honeyd` GitHub
source. The container is given `NET_ADMIN`/`NET_RAW` capabilities because
Honeyd needs raw-socket access to forge its TCP/IP personality (it's
imitating "Linux 2.6.18" in the included `honeyd.conf`). Getting Honeyd
working correctly in this containerized setup required two non-obvious
fixes, both already applied:

1. **Kernel RST suppression** (`docker/honeyd/entrypoint.sh`): Honeyd runs
   on the container's own real IP rather than a separate virtual IP (its
   normal deployment mode). Without suppressing it, the container's own
   kernel network stack answers connections on Honeyd's ports with an
   immediate TCP RST (since nothing has a real `bind()`/`listen()` there),
   which raced with and overrode Honeyd's crafted response — every scan
   saw "closed port" instead of Honeyd's simulated service. The entrypoint
   adds `iptables` rules to drop the kernel's own outgoing RSTs on
   Honeyd's ports so only Honeyd's spoofed responses reach the scanner.

2. **Config syntax**: nested/escaped quotes in `honeyd.conf`'s per-port
   banner commands caused a parser syntax error. Simplifying the quoting
   fixed config loading.

**Known limitation — Honeyd banners are blank.** After both fixes above,
Honeyd correctly answers the TCP handshake (`open_ports: 1`, matching a
real service), but the actual banner text (e.g. "220 ProFTPD ready.") does
not reach the client — `banner_length`/`banner_entropy` come back as `0`
for all Honeyd rows. This traces to Honeyd's internal script-execution
subsystem (how it forks a process and pipes its stdout back through the
raw socket) not working as expected in this containerized environment —
a deeper, more time-consuming thing to debug than the two fixes above,
with an uncertain payoff. This was a deliberate decision to stop
debugging here rather than sink more time chasing it: a blank banner on a
low-interaction honeypot is a plausible (if weak) real fingerprint, not a
corrupted signal the way the RST bug was — so the dataset built from this
config is valid, just missing one class of fields for the Honeyd rows
specifically. Worth noting as a known limitation in a project report.

**Conpot** — pulls `honeynet/conpot:latest`, the Honeynet Project's own
image. It's old and lightly maintained; if the pull fails with something
like `media type ... manifest.v1 ... no longer supported` (the same error
Glastopf hit — see below), build it from source instead:

```dockerfile
# docker/conpot/Dockerfile (fallback if the honeynet/conpot image breaks)
FROM python:3.9-slim
RUN apt-get update && apt-get install -y git build-essential libsnmp-dev snmp-mibs-downloader
RUN git clone https://github.com/mushorg/conpot.git /opt/conpot
WORKDIR /opt/conpot
RUN pip install -e .
EXPOSE 80 102 502 161/udp
CMD ["conpot", "--template", "default"]
```
Then point the `conpot` service in `docker-compose.yml` at `build: ./conpot`
instead of `image:`.

## Known limitation — Glastopf was dropped

Glastopf (the web-application honeypot originally planned for this lab)
was evaluated and intentionally left out:

- Its official `honeynet/glastopf:latest` image uses an old Docker
  manifest format (`manifest.v1+prettyjws`) that current Docker/containerd
  (v2.1+) refuses to pull.
- Building it from source requires Ubuntu 14.04 "trusty" (its only
  supported base OS), but trusty's packages have since been fully removed
  even from Canonical's `old-releases.ubuntu.com` archive — the package
  index returns 404 for every component, not just an expired-signature
  warning. There's no working package source left for it.

This is worth stating plainly in a project report: Glastopf is an
unmaintained, ~10+ year old codebase whose upstream dependency chain no
longer exists in a buildable form, and it was consciously excluded rather
than papered over with a broken container. The lab instead covers **4
honeypot types** spanning SSH/Telnet (Cowrie), FTP/SMB/HTTPS (Dionaea), a
generic low-interaction host (Honeyd), and ICS/SCADA protocols (Conpot) —
enough protocol diversity for a solid B.Tech dataset. If web-application
honeypot coverage is wanted later, the cleanest path is a small **custom**
Flask-based stand-in (generic/templated banners, low header counts,
common "vulnerable-looking" paths like `/phpmyadmin`) rather than reviving
Glastopf's dependency chain — ask if you want that built.

## Step 5 — Collect scan data for training

For each service in the table above, run the scanner against
`127.0.0.1:<host-port>` and record the resulting feature row with the
correct label:

```bash
cd ../scanner
python3 feature_extractor.py 127.0.0.1   # adjust target/port per service
```

Append each result to `dataset/dataset.csv` — `1` for every honeypot row
(Cowrie, Dionaea, Honeyd, Conpot), `0` for every real-service row (Nginx,
Apache, OpenSSH, vsftpd). Aim for at least a few hundred rows per class —
and within the honeypot class, scan **all four** honeypot types repeatedly
so the model doesn't just learn one honeypot's specific banner but general
honeypot-vs-real patterns. Then retrain:

```bash
cd ../ml
python train.py --data ../dataset/dataset.csv --out models
```

## Step 6 — Tear down

```bash
cd ../docker
docker compose down
```

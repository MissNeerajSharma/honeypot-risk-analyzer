# AI-Based Honeypot Detection System

Paste an IP or a URL into the dashboard → it's resolved via DNS → scanned →
features are extracted → a trained Random Forest / XGBoost model decides
**Real Server** or **Honeypot**, with a confidence score.

This is your Phase 1 deliverable: a fully working end-to-end pipeline
running on **synthetic dummy data**, so every part of the system (scanner
code, ML training, API, React dashboard) is real and testable before your
Docker lab exists. Swap in real lab data later with zero architecture
changes.

```
ai-honeypot-detection/
├── dataset/
│   └── generate_synthetic_dataset.py   # Phase 1 dummy data generator
├── scanner/
│   └── feature_extractor.py            # REAL nmap/socket scan → features
├── ml/
│   ├── train.py                        # trains + compares RF and XGBoost
│   ├── predict.py                      # scores one feature set
│   └── models/                         # saved .pkl models + metrics.json
├── backend/
│   └── app.py                          # FastAPI: /resolve /analyze /analyze/demo
├── frontend/                           # React + Vite dashboard
├── docker/
│   ├── docker-compose.yml              # Phase 2 lab: honeypots + real services
│   └── README.md                       # lab setup walkthrough
└── requirements.txt
```

## Quick start (Phase 1 — dummy data, no lab needed)

**1. Python environment**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Generate the synthetic dataset and train the model**

```bash
cd dataset
python generate_synthetic_dataset.py --n 2000 --out dataset.csv
cd ../ml
python train.py --data ../dataset/dataset.csv --out models
```

This prints accuracy/precision/recall/F1/ROC-AUC for both Random Forest
and XGBoost, saves both models plus `models/best_model.pkl`
(whichever wins on ROC-AUC), and prints feature importances.

**3. Start the backend API**

```bash
cd ../backend
uvicorn app:app --reload --port 8000
```

Check it's alive: `curl http://127.0.0.1:8000/health`

**4. Start the React dashboard**

```bash
cd ../frontend
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). Leave the mode
switch on **Dummy Data**, type any IP/hostname, click **Analyze**, and
watch the pipeline trace light up: Target → DNS Resolve → Port Scan →
Feature Extract → ML Model → Verdict.

## Moving to Phase 2 — real scans against your own lab

1. Follow `docker/README.md` to bring up Cowrie/Dionaea (honeypots) and
   Nginx/Apache/OpenSSH/vsftpd (real services) in isolated containers.
2. Run `scanner/feature_extractor.py` against each container, log the
   feature rows into `dataset/dataset.csv` with the correct
   `is_honeypot` label, and re-run `ml/train.py`.
3. Flip the dashboard's mode switch to **Real Scan** — this calls
   `/analyze` instead of `/analyze/demo`, which runs the real
   `scanner/feature_extractor.py` pipeline (needs the `nmap` binary
   installed and, for OS fingerprinting, root/administrator privileges).
4. **Only ever point Real Scan at hosts you own or have explicit written
   permission to test.** Scanning third-party systems without
   authorization can violate laws, policies, or terms of service.

## Roadmap / advanced features (from the original project brief)

- **Explainable AI (SHAP)** — the dashboard currently shows the model's
  overall top feature importances as a lightweight stand-in. Swap in real
  per-prediction SHAP values in `ml/predict.py` (add `shap.TreeExplainer`,
  already listed as an optional dependency) once you're ready.
- **Deep learning track** — LSTM over raw packet sequences, or CNN over
  traffic represented as images, as an alternative to engineered features.
- **Real-time monitoring** — wrap `scanner/feature_extractor.py` in a loop
  over a watchlist of IPs with alerting.
- **Ensemble model** — combine Random Forest + XGBoost + a small neural
  net with a voting classifier (`sklearn.ensemble.VotingClassifier`).

## Feature schema (used consistently everywhere)

`ttl, window_size, open_ports, banner_length, banner_entropy,
ssh_banner_present, http_header_count, http_status_code, response_time_ms,
latency_std_dev, icmp_reply, num_services, tcp_mss`

If you add or remove a feature, update it in all four places:
`dataset/generate_synthetic_dataset.py`, `scanner/feature_extractor.py`,
`ml/train.py`, `ml/predict.py`.

## Ethical note

Only scan systems you own or have explicit permission to test. Internet-wide
scanning or probing third-party systems without authorization can violate
laws, policies, or terms of service.

import React, { useEffect, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

const METRIC_ROWS = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'precision', label: 'Precision' },
  { key: 'recall', label: 'Recall' },
  { key: 'f1', label: 'F1 Score' },
  { key: 'roc_auc', label: 'ROC-AUC' },
]

const HONEYPOTS = ['Cowrie', 'Dionaea', 'Honeyd', 'Conpot']
const REAL_SERVICES = ['Nginx', 'Apache', 'OpenSSH', 'vsftpd', 'Postfix', 'BIND9']

export default function Metrics() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/metrics`)
      .then((res) => {
        if (!res.ok) throw new Error('no metrics yet')
        return res.json()
      })
      .then(setMetrics)
      .catch(() => setError(true))
  }, [])

  return (
    <section className="metrics" id="metrics">
      <div className="section-inner">
        <div className="section-eyebrow">Model &amp; Dataset</div>
        <h2 className="section-title">Trained on real traffic, not just theory.</h2>
        <p className="section-lede">
          Both models are trained on scans collected from a live lab of
          honeypots and production-style services, then compared head to
          head. The better one on ROC-AUC is what the console actually runs.
        </p>

        {error && (
          <div className="metrics-empty">
            No training metrics available yet. Run <code>ml/train.py</code> to
            generate them.
          </div>
        )}

        {metrics && (
          <div className="metrics-grid">
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Random Forest</th>
                  <th>XGBoost</th>
                </tr>
              </thead>
              <tbody>
                {METRIC_ROWS.map((row) => (
                  <tr key={row.key}>
                    <td>{row.label}</td>
                    <td className={metrics.best_model === 'random_forest' ? 'best' : ''}>
                      {(metrics.random_forest[row.key] * 100).toFixed(1)}%
                    </td>
                    <td className={metrics.best_model === 'xgboost' ? 'best' : ''}>
                      {(metrics.xgboost[row.key] * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="metrics-best-note">
              Best model in production: <strong>{metrics.best_model === 'random_forest' ? 'Random Forest' : 'XGBoost'}</strong>
            </div>
          </div>
        )}

        <div className="coverage">
          <div className="coverage-group">
            <div className="coverage-label">Honeypot types in the training lab</div>
            <div className="coverage-chips">
              {HONEYPOTS.map((h) => (
                <span key={h} className="chip chip-honeypot">{h}</span>
              ))}
            </div>
          </div>
          <div className="coverage-group">
            <div className="coverage-label">Real services in the training lab</div>
            <div className="coverage-chips">
              {REAL_SERVICES.map((s) => (
                <span key={s} className="chip chip-real">{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

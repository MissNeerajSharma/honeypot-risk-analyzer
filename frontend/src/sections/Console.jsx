import React, { useState, useRef, useEffect } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

const PIPELINE = [
  { key: 'target', label: 'Target' },
  { key: 'resolve', label: 'DNS Resolve' },
  { key: 'scan', label: 'Port Scan' },
  { key: 'extract', label: 'Feature Extract' },
  { key: 'model', label: 'Model' },
  { key: 'verdict', label: 'Verdict' },
]

const FEATURE_LABELS = {
  ttl: 'TTL',
  window_size: 'TCP Window',
  open_ports: 'Open Ports',
  banner_length: 'Banner Length',
  banner_entropy: 'Banner Entropy',
  ssh_banner_present: 'SSH Banner',
  http_header_count: 'HTTP Headers',
  http_status_code: 'HTTP Status',
  response_time_ms: 'Response (ms)',
  latency_std_dev: 'Latency σ',
  icmp_reply: 'ICMP Reply',
  num_services: 'Services',
  tcp_mss: 'TCP MSS',
}

export default function Console() {
  const [target, setTarget] = useState('')
  const [mode, setMode] = useState('demo') // 'demo' | 'real'
  const [consented, setConsented] = useState(false)
  const [step, setStep] = useState(-1)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  useEffect(() => () => clearInterval(timerRef.current), [])

  const needsConsent = mode === 'real' && !consented
  const canAnalyze = target.trim() && !loading && !needsConsent

  async function runAnalysis() {
    if (!canAnalyze) return
    setError(null)
    setResult(null)
    setLoading(true)
    setStep(0)

    let i = 0
    timerRef.current = setInterval(() => {
      i = Math.min(i + 1, PIPELINE.length - 2)
      setStep(i)
    }, 380)

    const endpoint = mode === 'real' ? '/analyze' : '/analyze/demo'

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: target.trim() }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Analysis failed')
      clearInterval(timerRef.current)
      setStep(PIPELINE.length - 1)
      setResult(data)
    } catch (e) {
      clearInterval(timerRef.current)
      setStep(-1)
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  const verdict = result?.verdict
  const isHoneypot = verdict?.is_honeypot
  const confidence = isHoneypot ? verdict?.honeypot_confidence : verdict?.real_server_confidence
  const explanation = verdict?.explanation || []

  return (
    <section className="console" id="console">
      <div className="section-inner">
        <div className="section-eyebrow">Live Tool</div>
        <h2 className="section-title">Run a classification.</h2>
        <p className="section-lede">
          Point it at a target and watch the pipeline execute step by step.
          Simulated Data needs nothing running locally; Live Scan calls your
          own backend and Nmap installation.
        </p>

        <div className="console-panel">
          <div className="console-controls">
            <div className="mode-toggle" role="tablist" aria-label="Scan mode">
              <button
                className={mode === 'demo' ? 'active' : ''}
                onClick={() => setMode('demo')}
                role="tab"
                aria-selected={mode === 'demo'}
              >
                Simulated Data
              </button>
              <button
                className={mode === 'real' ? 'active' : ''}
                onClick={() => setMode('real')}
                role="tab"
                aria-selected={mode === 'real'}
              >
                Live Scan
              </button>
            </div>

            <div className="target-input">
              <input
                type="text"
                placeholder="192.168.1.50  or  myhost.local"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && canAnalyze && runAnalysis()}
                spellCheck={false}
              />
              <button className="btn btn-primary" onClick={runAnalysis} disabled={!canAnalyze}>
                {loading ? 'Analyzing…' : 'Analyze'}
              </button>
            </div>
          </div>

          {mode === 'real' && (
            <label className="consent-check">
              <input
                type="checkbox"
                checked={consented}
                onChange={(e) => setConsented(e.target.checked)}
              />
              <span>
                I understand: only scan hosts I own or have explicit permission
                to test. Unauthorized scanning can violate laws or terms of service.
              </span>
            </label>
          )}

          <div className="pipeline" aria-label="Analysis pipeline">
            {PIPELINE.map((p, idx) => (
              <React.Fragment key={p.key}>
                <div className={`node ${idx <= step ? 'lit' : ''} ${idx === step && loading ? 'active' : ''}`}>
                  <div className="node-dot" />
                  <div className="node-label">{p.label}</div>
                </div>
                {idx < PIPELINE.length - 1 && (
                  <div className={`trace-line ${idx < step ? 'lit' : ''}`} />
                )}
              </React.Fragment>
            ))}
          </div>

          {error && <div className="error-banner">{error}</div>}

          {result && (
            <div className="results">
              <div className={`verdict-card ${isHoneypot ? 'honeypot' : 'real'}`}>
                <div className="verdict-label">
                  {isHoneypot ? 'HONEYPOT DETECTED' : 'REAL SERVER'}
                </div>
                <div className="verdict-confidence">
                  {(confidence * 100).toFixed(1)}<span>% confidence</span>
                </div>
                <div className="verdict-meta">
                  <span>Target: <strong>{result.input}</strong></span>
                  <span>Resolved IP: <strong>{result.resolved_ip}</strong></span>
                  <span>Mode: <strong>{result.mode === 'real_scan' ? 'live scan' : 'simulated data'}</strong></span>
                </div>
              </div>

              <div className="panels">
                <div className="panel">
                  <h3>Extracted Features</h3>
                  <table className="feature-table">
                    <tbody>
                      {Object.entries(result.features).map(([k, v]) => (
                        <tr key={k}>
                          <td className="fname">{FEATURE_LABELS[k] || k}</td>
                          <td className="fval">{String(v)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="panel">
                  <h3>Why the model leans this way</h3>
                  <p className="explain-note">
                    SHAP values show how much each feature pushed this specific
                    scan's prediction — not just what the model relies on in general.
                  </p>
                  <ul className="shap-list">
                    {explanation.map((item) => (
                      <li key={item.feature} className={`shap-item ${item.pushes_toward}`}>
                        <div className="shap-row">
                          <span className="shap-label">{item.label}</span>
                          <span className="shap-value">{String(item.value)}</span>
                        </div>
                        <div className="shap-bar-track">
                          <div
                            className={`shap-bar-fill ${item.pushes_toward}`}
                            style={{ width: `${Math.min(Math.abs(item.shap_contribution) * 20, 100)}%` }}
                          />
                        </div>
                        <div className="shap-push">
                          pushes toward{' '}
                          <strong>{item.pushes_toward === 'honeypot' ? 'Honeypot' : 'Real Server'}</strong>
                          {' '}({item.shap_contribution > 0 ? '+' : ''}{item.shap_contribution})
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

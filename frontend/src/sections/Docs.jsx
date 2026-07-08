import React from 'react'

const ENDPOINTS = [
  {
    method: 'GET',
    path: '/health',
    desc: 'Reports whether the API is up and whether a trained model is loaded.',
  },
  {
    method: 'POST',
    path: '/resolve',
    desc: 'Resolves an IP, hostname, or URL to an IPv4 address via DNS.',
    body: '{ "target": "example.com" }',
  },
  {
    method: 'POST',
    path: '/analyze',
    desc: 'Full live pipeline: resolve, scan, extract features, classify. Only scan hosts you own.',
    body: '{ "target": "192.168.1.50" }',
  },
  {
    method: 'POST',
    path: '/analyze/demo',
    desc: 'Same response shape as /analyze, using simulated data — no network calls made.',
    body: '{ "target": "192.168.1.50" }',
  },
  {
    method: 'GET',
    path: '/features',
    desc: 'Lists the 13 feature columns the model was trained on.',
  },
  {
    method: 'GET',
    path: '/metrics',
    desc: 'Returns the accuracy/precision/recall/F1/ROC-AUC comparison from the last training run.',
  },
]

export default function Docs() {
  return (
    <section className="docs" id="docs">
      <div className="section-inner">
        <div className="section-eyebrow">Reference</div>
        <h2 className="section-title">API endpoints.</h2>
        <p className="section-lede">
          The dashboard above is just one client of this API. Anything it can
          do, you can call directly.
        </p>

        <div className="docs-list">
          {ENDPOINTS.map((ep) => (
            <div className="docs-item" key={ep.path}>
              <div className="docs-item-head">
                <span className={`method-badge ${ep.method.toLowerCase()}`}>{ep.method}</span>
                <span className="docs-path">{ep.path}</span>
              </div>
              <p className="docs-desc">{ep.desc}</p>
              {ep.body && <pre className="docs-body">{ep.body}</pre>}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

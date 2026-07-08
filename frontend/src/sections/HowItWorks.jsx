import React from 'react'

const STEPS = [
  {
    n: '01',
    title: 'Target',
    body: 'Paste an IP address or a URL. No prior setup required.',
  },
  {
    n: '02',
    title: 'DNS Resolve',
    body: 'Hostnames are resolved to an IPv4 address before anything is touched.',
  },
  {
    n: '03',
    title: 'Port Scan',
    body: 'Nmap probes the target for open ports, service banners, and OS fingerprint.',
  },
  {
    n: '04',
    title: 'Feature Extraction',
    body: 'Raw scan output becomes 13 numeric signals — TTL, timing jitter, banner entropy, and more.',
  },
  {
    n: '05',
    title: 'Model',
    body: 'A Random Forest / XGBoost classifier trained on real honeypot and production traffic scores the signals.',
  },
  {
    n: '06',
    title: 'Verdict',
    body: 'A confidence score, plus the exact features (via SHAP) that drove the decision.',
  },
]

export default function HowItWorks() {
  return (
    <section className="how" id="how-it-works">
      <div className="section-inner">
        <div className="section-eyebrow">Pipeline</div>
        <h2 className="section-title">Six steps, one target.</h2>
        <p className="section-lede">
          Every scan goes through the same pipeline, in the same order. Nothing
          is hidden between the input you give it and the verdict you get back.
        </p>

        <div className="how-steps">
          {STEPS.map((s) => (
            <div className="how-step" key={s.n}>
              <div className="how-step-num">{s.n}</div>
              <div className="how-step-title">{s.title}</div>
              <div className="how-step-body">{s.body}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

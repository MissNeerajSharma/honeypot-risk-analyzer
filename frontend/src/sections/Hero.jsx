import React, { useEffect, useState } from 'react'

const SAMPLE_EVENTS = [
  { ip: '192.0.2.14', verdict: 'real_server', confidence: 96.2 },
  { ip: '198.51.100.6', verdict: 'honeypot', confidence: 91.4 },
  { ip: '203.0.113.28', verdict: 'real_server', confidence: 88.7 },
  { ip: '198.51.100.19', verdict: 'honeypot', confidence: 97.1 },
  { ip: '192.0.2.55', verdict: 'real_server', confidence: 99.0 },
  { ip: '203.0.113.4', verdict: 'honeypot', confidence: 82.3 },
  { ip: '198.51.100.41', verdict: 'real_server', confidence: 93.8 },
  { ip: '192.0.2.101', verdict: 'honeypot', confidence: 95.5 },
]

function timestamp() {
  const d = new Date()
  return d.toTimeString().slice(0, 8)
}

export default function Hero() {
  const [feed, setFeed] = useState([])

  useEffect(() => {
    let i = 0
    const push = () => {
      const sample = SAMPLE_EVENTS[i % SAMPLE_EVENTS.length]
      i += 1
      setFeed((prev) => [{ ...sample, time: timestamp(), key: Date.now() }, ...prev].slice(0, 6))
    }
    push()
    const interval = setInterval(push, 2200)
    return () => clearInterval(interval)
  }, [])

  const scrollToConsole = (e) => {
    e.preventDefault()
    document.getElementById('console')?.scrollIntoView({ behavior: 'smooth' })
  }
  const scrollToHow = (e) => {
    e.preventDefault()
    document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="hero" id="top">
      <div className="hero-grid">
        <div className="hero-copy">
          <div className="hero-eyebrow">NETWORK RECONNAISSANCE CLASSIFICATION</div>
          <h1 className="hero-title">
            Tell a honeypot from a real server —<br />before you engage it.
          </h1>
          <p className="hero-subhead">
            HoneyDec resolves a target, scans it, extracts the same signals a
            trained analyst would look for, and scores it with a model trained
            on real honeypot and production-service traffic. Every verdict
            comes with the exact features that drove it.
          </p>
          <div className="hero-actions">
            <a href="#console" className="btn btn-primary" onClick={scrollToConsole}>
              Open the Console
            </a>
            <a href="#how-it-works" className="btn btn-ghost" onClick={scrollToHow}>
              See how it works
            </a>
          </div>
        </div>

        <div className="hero-feed" aria-label="Live classification feed">
          <div className="hero-feed-header">
            <span>live classification feed</span>
            <span className="hero-feed-dot" />
          </div>
          <div className="hero-feed-body">
            {feed.map((f) => (
              <div key={f.key} className="hero-feed-row">
                <span className="hero-feed-time">{f.time}</span>
                <span className="hero-feed-ip">{f.ip}</span>
                <span className="hero-feed-arrow">→</span>
                <span className={`hero-feed-verdict ${f.verdict}`}>
                  {f.verdict === 'honeypot' ? 'honeypot' : 'real_server'}
                </span>
                <span className="hero-feed-confidence">{f.confidence.toFixed(1)}%</span>
              </div>
            ))}
          </div>
          <div className="hero-feed-footnote">simulated for illustration</div>
        </div>
      </div>
    </section>
  )
}

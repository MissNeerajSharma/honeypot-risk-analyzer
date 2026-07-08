import React from 'react'

const STACK = [
  { name: 'Nmap', role: 'Port scanning, service/version detection, OS fingerprinting' },
  { name: 'Python', role: 'Scanner, feature extraction, and training pipeline' },
  { name: 'scikit-learn', role: 'Random Forest classifier' },
  { name: 'XGBoost', role: 'Gradient-boosted classifier, compared head to head with Random Forest' },
  { name: 'SHAP', role: 'Per-prediction explainability — which features drove each verdict' },
  { name: 'FastAPI', role: 'Backend API connecting the scanner, model, and dashboard' },
  { name: 'React + Vite', role: 'This dashboard' },
  { name: 'Docker', role: 'Isolated lab of honeypots and real services used to build the dataset' },
]

export default function Stack() {
  return (
    <section className="stack" id="stack">
      <div className="section-inner">
        <div className="section-eyebrow">About</div>
        <h2 className="section-title">Built from a real lab, not a spreadsheet.</h2>
        <p className="section-lede">
          HoneyDec's training data comes from an isolated Docker lab running
          four honeypot types (Cowrie, Dionaea, Honeyd, Conpot) alongside six
          real production-style services (Nginx, Apache, OpenSSH, vsftpd,
          Postfix, BIND9). Each is scanned the same way a live target would be,
          and labeled with ground truth — because the container's identity is
          already known. That labeled data trains the classifier the console
          runs.
        </p>

        <div className="stack-grid">
          {STACK.map((item) => (
            <div className="stack-item" key={item.name}>
              <div className="stack-item-name">{item.name}</div>
              <div className="stack-item-role">{item.role}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

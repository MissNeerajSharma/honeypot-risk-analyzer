import React, { useEffect, useState } from 'react'

const LINKS = [
  { id: 'how-it-works', label: 'How It Works' },
  { id: 'console', label: 'Console' },
  { id: 'metrics', label: 'Metrics' },
  { id: 'stack', label: 'Stack' },
  { id: 'docs', label: 'Docs' },
]

export default function Nav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const scrollTo = (id) => (e) => {
    e.preventDefault()
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <header className={`nav ${scrolled ? 'nav-scrolled' : ''}`}>
      <div className="nav-inner">
        <a href="#top" className="nav-brand" onClick={scrollTo('top')}>
          <span className="nav-brand-mark" />
          HONEYDEC
        </a>
        <nav className="nav-links">
          {LINKS.map((l) => (
            <a key={l.id} href={`#${l.id}`} onClick={scrollTo(l.id)}>
              {l.label}
            </a>
          ))}
        </nav>
        <div className="nav-status">
          <span className="nav-status-dot" />
          system online
        </div>
      </div>
    </header>
  )
}

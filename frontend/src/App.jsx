import React from 'react'
import Nav from './sections/Nav.jsx'
import Hero from './sections/Hero.jsx'
import HowItWorks from './sections/HowItWorks.jsx'
import Console from './sections/Console.jsx'
import Metrics from './sections/Metrics.jsx'
import Stack from './sections/Stack.jsx'
import Docs from './sections/Docs.jsx'
import Footer from './sections/Footer.jsx'

export default function App() {
  return (
    <div className="site">
      <Nav />
      <main>
        <Hero />
        <HowItWorks />
        <Console />
        <Metrics />
        <Stack />
        <Docs />
      </main>
      <Footer />
    </div>
  )
}

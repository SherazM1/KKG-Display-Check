import Link from "next/link";
import { Suspense } from "react";
import { DisplayImagery } from "@/components/DisplayImagery";
import { SupportedDisplayFamilies } from "@/components/SupportedDisplayFamilies";
import { ApiStatus } from "@/components/ApiStatus";

export default function HomePage() {
  return (
    <main id="main" className="home page-width">
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy"><p className="eyebrow accent">Retail thinking. On display.</p><h1 id="hero-title">Great displays<br />start with<br /><em>clear direction.</em></h1><p className="hero-description">A considered space to shape your next retail display.</p><Link className="button" href="/project">Start New Project <span aria-hidden="true">↗</span></Link></div>
        <DisplayImagery />
      </section>
      <ol className="workflow" aria-label="Display planning workflow">{["Configure", "Estimate", "Visualize"].map((step, index) => <li key={step}><span className="eyebrow">0{index + 1}</span><span>{step}</span><span className="workflow-rule" aria-hidden="true" /></li>)}</ol>
      <Suspense fallback={<p className="muted">Loading display families…</p>}><SupportedDisplayFamilies /></Suspense>
      <Suspense><ApiStatus /></Suspense>
    </main>
  );
}

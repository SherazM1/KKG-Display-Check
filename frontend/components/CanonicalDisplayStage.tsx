export function CanonicalDisplayStage() {
  return (
    <section className="panel canonical-stage technical-grid" aria-labelledby="stage-title">
      <div className="stage-heading"><h2 id="stage-title" className="eyebrow">Canonical display</h2><span className="eyebrow muted">Stage / —</span></div>
      <div className="stage-empty"><span className="draft-cross" aria-hidden="true">+</span><h3>Select a display to begin</h3><p className="muted small">Your display view will appear here.</p></div>
      <div className="stage-footer eyebrow"><span>Display workspace</span><span>No display selected</span></div>
    </section>
  );
}

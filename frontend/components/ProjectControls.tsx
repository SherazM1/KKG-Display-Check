export function ProjectControls() {
  return (
    <section className="panel project-controls" aria-labelledby="controls-title">
      <div className="panel-heading"><span className="eyebrow">01 / Configure</span><h2 id="controls-title">Project details</h2></div>
      <p id="controls-note" className="muted small">Configuration controls are coming soon.</p>
      <fieldset disabled aria-describedby="controls-note"><legend className="sr-only">Display configuration</legend>
        <label htmlFor="project-name">Project name</label><input id="project-name" placeholder="Name your project" />
        <label htmlFor="display-family">Display family</label><select id="display-family" defaultValue=""><option value="">Select a display</option></select>
        <label htmlFor="configuration">Configuration</label><select id="configuration" defaultValue=""><option value="">Select a display first</option></select>
        <label htmlFor="baseline">Baseline size</label><select id="baseline" defaultValue=""><option value="">Select a display first</option></select>
      </fieldset>
      <p className="controls-footnote">Your display starts here.</p>
    </section>
  );
}

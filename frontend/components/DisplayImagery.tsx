// Replace this component's interior with approved KKG imagery when available.
// The abstract composition is decorative, not canonical display geometry.
export function DisplayImagery() {
  return (
    <figure className="imagery technical-grid" aria-label="Placeholder for future KKG display photography">
      <div className="imagery-top"><span>KKG / Display studies</span><span aria-hidden="true">+</span></div>
      <div className="abstract-composition" aria-hidden="true"><div className="abstract-sheet sheet-back" /><div className="abstract-sheet sheet-front" /><div className="abstract-line" /></div>
      <figcaption><span>Space for what’s next.</span><span className="eyebrow">Display imagery forthcoming</span></figcaption>
    </figure>
  );
}

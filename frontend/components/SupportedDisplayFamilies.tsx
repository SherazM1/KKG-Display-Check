import { getDisplays } from "@/lib/api";

export async function SupportedDisplayFamilies() {
  const result = await getDisplays();
  return (
    <section className="families" aria-labelledby="families-title">
      <div className="section-heading"><h2 id="families-title">Supported display families</h2><span className="eyebrow">The starting point</span></div>
      {result.ok && result.data.families.length > 0 ? (
        <ul className="family-list">{result.data.families.map((family) => <li key={family.id}>{family.label}<span aria-hidden="true">↗</span></li>)}</ul>
      ) : <p className="muted">{result.ok ? "No display families available." : "Display families are temporarily unavailable. Please try again later."}</p>}
    </section>
  );
}

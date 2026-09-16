import Link from "next/link";

export function AppHeader() {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="Display Check by KKG, home">
        <span className="brand-mark">KKG</span><span>Display Check<span className="brand-caption">Retail display workspace</span></span>
      </Link>
      <nav aria-label="Main navigation"><Link className="text-link" href="/project">Project workspace <span aria-hidden="true">↗</span></Link></nav>
    </header>
  );
}

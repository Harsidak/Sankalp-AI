/**
 * The frame every authenticated page shares: navbar, centred column, and a
 * header with the same eyebrow/title/subtitle rhythm as the dashboard.
 *
 * `actions` renders to the right of the title on wide screens and drops
 * beneath it on narrow ones.
 */

import Navbar from './Navbar';

export default function PageShell({ eyebrow, title, subtitle, actions, children }) {
  return (
    <div className="app-page">
      <Navbar />

      <main className="dashboard-container">
        <header className="page-head">
          <div>
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            <h1>{title}</h1>
            {subtitle && <p className="page-sub">{subtitle}</p>}
          </div>
          {actions && <div className="page-actions">{actions}</div>}
        </header>

        {children}
      </main>
    </div>
  );
}

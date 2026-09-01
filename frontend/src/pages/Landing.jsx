/**
 * Landing page.
 *
 * The hero is built as depth layers rather than a row of columns: the colossal
 * wordmark sits behind the aura orb, which the foreground copy then overlaps.
 * Everything below it is ordinary sectioned content revealed on scroll.
 */

import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useReveal } from '../hooks/useReveal';
import Navbar from '../components/layout/Navbar';
import AuraOrb from '../components/hero/AuraOrb';

const PILLARS = [
  {
    title: 'Daily check-in',
    body: 'One minute, one mood, one line about why. The database keeps you honest — a single check-in per day, enforced in the schema itself.',
    icon: (
      <path
        d="M12 3a9 9 0 1 0 9 9M8.5 12.5l2.5 2.5 6-7"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    ),
  },
  {
    title: 'Tagged journal',
    body: 'Write freely, then tag it. Entries and tags form a true many-to-many, so a single thought can belong to work, sleep and gratitude at once.',
    icon: (
      <path
        d="M5 4h9l5 5v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM14 4v5h5M8 13h8M8 17h5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    ),
  },
  {
    title: 'Habit streaks',
    body: 'Marking a habit done is an insert; undoing it is a delete. Current streak, longest streak and the near-misses are computed from that, live.',
    icon: (
      <path
        d="M12 3s5 4.5 5 9a5 5 0 0 1-10 0c0-1.6.6-3 1.4-4.2.5 1.2 1.3 2 2.3 2.2C10 8 12 6 12 3z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        fill="none"
      />
    ),
  },
  {
    title: 'Patterns, surfaced',
    body: 'Mood against sleep, streaks against weeks, tags against mood. Charts drawn by hand in SVG — no library between you and your own data.',
    icon: (
      <path
        d="M4 19V5M4 19h16M8 15l3.5-4.5L15 14l4-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    ),
  },
];

const STEPS = [
  {
    n: '01',
    title: 'Arrive',
    body: 'Log how the day actually felt on a five-point scale, with the hours you slept and a sentence of context.',
  },
  {
    n: '02',
    title: 'Unload',
    body: 'Write the entry you would otherwise carry around. Tag it so it can be found again by feeling, not by date.',
  },
  {
    n: '03',
    title: 'Repeat',
    body: 'Small habits, tracked without ceremony. The streak is the reward; breaking one is information, not failure.',
  },
  {
    n: '04',
    title: 'Reflect',
    body: 'When there is enough history, ask the AI what it notices. It reads your own entries back to you — nothing invented.',
  },
];

const AVATARS = ['#7c3aed', '#e9a06a', '#56b6c2', '#e8788a', '#6fe0c2'];

export default function Landing() {
  const { isAuthenticated } = useAuth();
  const pageRef = useReveal();

  return (
    <div className="landing-page" ref={pageRef}>
      <Navbar />

      {/* ============ Hero ============ */}
      <header className="hero">
        <div className="hero-wash" aria-hidden="true" />

        <div className="hero-stage">
          <h1 className="hero-mega">SANKALP</h1>
          <span className="hero-echo">FIND YOUR CALM</span>
          <AuraOrb className="hero-orb" />
        </div>

        <div className="hero-foot">
          <div>
            <p className="hero-lede">
              SankalpAI turns scattered days into something you can read. Check in, write
              it down, keep the small promises — then let the patterns speak for
              themselves.
            </p>

            <div className="hero-cta">
              <Link
                to={isAuthenticated ? '/dashboard' : '/signup'}
                className="btn btn-lg"
              >
                {isAuthenticated ? 'Open Dashboard' : 'Begin Your Practice'}
              </Link>
              <a href="#practice" className="btn-round" aria-label="See the practice">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path
                    d="M3 13L13 3M6 3h7v7"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </a>
            </div>

            <div className="hero-proof">
              <div className="avatar-stack">
                {AVATARS.map((color, i) => (
                  <span key={color} style={{ background: color }}>
                    {String.fromCharCode(65 + i * 3)}
                  </span>
                ))}
              </div>
              <p>
                Trusted by 10,000+ minds
                <br />
                building a steadier week
              </p>
            </div>
          </div>

          <h2 className="hero-headline">
            <span>Clarity</span>
            <span>That Powers</span>
            <span>Your Calm</span>
          </h2>
        </div>
      </header>

      {/* ============ The practice ============ */}
      <section className="section" id="practice">
        <div className="shell">
          <div className="section-head reveal">
            <p className="eyebrow">The Practice</p>
            <h2>Four habits, one quiet loop.</h2>
            <p>
              Nothing here asks for an hour of your day. Each piece takes a minute and
              feeds the next, so the picture builds itself while you are busy living.
            </p>
          </div>

          <div className="pillar-grid">
            {PILLARS.map((pillar, i) => (
              <article className="pillar reveal" key={pillar.title}>
                <span className="pillar-index">{String(i + 1).padStart(2, '0')}</span>
                <span className="pillar-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24">
                    {pillar.icon}
                  </svg>
                </span>
                <h3>{pillar.title}</h3>
                <p>{pillar.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ============ How it works ============ */}
      <section className="section band" id="how">
        <div className="shell">
          <div className="section-head reveal">
            <p className="eyebrow">How It Works</p>
            <h2>A week takes four minutes.</h2>
          </div>

          <div className="step-grid">
            {STEPS.map((step) => (
              <div className="step reveal" key={step.n}>
                <div className="step-num">{step.n}</div>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ Closing ============ */}
      <section className="shell">
        <div className="closing reveal">
          <h2>Start where you are.</h2>
          <p>
            No streak to catch up on, no backlog to clear. Log today, and tomorrow the
            chart has two points instead of one.
          </p>
          <Link to={isAuthenticated ? '/dashboard' : '/signup'} className="btn btn-lg">
            {isAuthenticated ? 'Go to Dashboard' : 'Create Your Account'}
          </Link>
        </div>
      </section>

      <footer className="site-footer">
        <div className="shell footer-inner">
          <span>&copy; {new Date().getFullYear()} SankalpAI</span>
          <div className="footer-links">
            <a href="#practice">Practice</a>
            <a href="#how">How it works</a>
            <Link to="/login">Sign in</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

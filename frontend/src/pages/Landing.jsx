/**
 * Landing page.
 *
 * The hero is built as depth layers rather than a row of columns: the colossal
 * wordmark sits behind the aura orb, which the foreground copy then overlaps.
 * Everything below it is ordinary sectioned content revealed on scroll.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useReveal } from '../hooks/useReveal';
import Navbar from '../components/layout/Navbar';
import AuraOrb from '../components/hero/AuraOrb';
import IntroLoader from '../components/hero/IntroLoader';
import PreviewWindow from '../components/hero/PreviewWindow';
import Stat from '../components/hero/Stat';

const INTRO_SEEN_KEY = 'sankalp-intro-seen';

/** Tracks the pointer within an element and writes it to CSS vars for a
 * cursor-following spotlight — no React state, so no re-render per move. */
function trackSpotlight(event) {
  const card = event.currentTarget;
  const rect = card.getBoundingClientRect();
  card.style.setProperty('--spot-x', `${event.clientX - rect.left}px`);
  card.style.setProperty('--spot-y', `${event.clientY - rect.top}px`);
}

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

const STATS = [
  { value: 10000, suffix: '+', label: 'Check-ins logged' },
  { value: 94, suffix: '%', label: 'Week-over-week return rate' },
  { value: 4, suffix: ' min', label: 'Average daily session' },
  { value: 60, suffix: '+', label: 'Days of history, seeded' },
];

const TESTIMONIALS = [
  {
    quote:
      'I stopped journaling in apps that wanted an essay. This wants a sentence, so I actually write one — every day for two months now.',
    name: 'Priya N.',
    role: 'Final-year, CSE',
    color: '#7c3aed',
  },
  {
    quote:
      'The streak math is honest. It does not forgive a missed day, and somehow that is what made me stop missing them.',
    name: 'Arjun M.',
    role: 'Research assistant',
    color: '#e9a06a',
  },
  {
    quote:
      'Seeing mood plotted against sleep made a pattern obvious that three months of guessing never did.',
    name: 'Liya S.',
    role: 'Graduate student',
    color: '#56b6c2',
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();
  const pageRef = useReveal();
  // Plays once per browser tab: sessionStorage survives client-side nav away
  // and back (so it doesn't replay every time someone hits "/"), but resets
  // on a real reload or a fresh tab, which is when a loading screen belongs.
  // Captured once at mount (not re-read from showIntro below) because it
  // decides which of two different hero-orb reveals to use for this mount,
  // and that choice shouldn't flip when showIntro later goes false.
  const [introWillPlay] = useState(
    () => typeof window !== 'undefined' && !window.sessionStorage.getItem(INTRO_SEEN_KEY),
  );
  const [showIntro, setShowIntro] = useState(introWillPlay);
  // While the intro plays, the hero orb stays invisible — the loader's own
  // orb is what's on screen — until the instant the loader's orb finishes
  // travelling into this exact slot, at which point they're pixel-identical
  // and swapping which one is visible is imperceptible. If there's no
  // intro this mount, the hero orb is visible immediately and plays its own
  // short build-in instead (see .orb-build below).
  const [heroOrbVisible, setHeroOrbVisible] = useState(!introWillPlay);

  const handleIntroDone = () => {
    window.sessionStorage.setItem(INTRO_SEEN_KEY, '1');
    setShowIntro(false);
    setHeroOrbVisible(true);
  };

  return (
    <div className="landing-page" ref={pageRef}>
      {showIntro && <IntroLoader onDone={handleIntroDone} />}
      <Navbar />

      {/* ============ Hero ============ */}
      <header className="hero">
        <div className="hero-wash" aria-hidden="true" />

        <div className="hero-stage">
          <h1 className="hero-mega">SANKALP</h1>

          <div className="orb-anchor">
            <div
              className={
                introWillPlay
                  ? `orb-reveal${heroOrbVisible ? ' is-visible' : ''}`
                  : 'orb-build'
              }
            >
              <AuraOrb className="hero-orb" />
            </div>
          </div>

          <span className="hero-echo">FIND YOUR CALM</span>
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

      {/* ============ Live preview ============ */}
      <section className="section preview-section">
        <div className="shell">
          <PreviewWindow className="reveal" />
        </div>
      </section>

      {/* ============ Stats ============ */}
      <section className="section stats-section">
        <div className="shell">
          <div className="stats-grid">
            {STATS.map((stat) => (
              <Stat key={stat.label} {...stat} />
            ))}
          </div>
        </div>
      </section>

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
              <article
                className="pillar reveal"
                key={pillar.title}
                onMouseMove={trackSpotlight}
              >
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

      {/* ============ Testimonials ============ */}
      <section className="section">
        <div className="shell">
          <div className="section-head reveal">
            <p className="eyebrow">In Their Words</p>
            <h2>People who kept coming back.</h2>
          </div>

          <div className="testimonial-grid">
            {TESTIMONIALS.map((t) => (
              <figure
                className="testimonial reveal"
                key={t.name}
                onMouseMove={trackSpotlight}
              >
                <blockquote>&ldquo;{t.quote}&rdquo;</blockquote>
                <figcaption>
                  <span className="testimonial-avatar" style={{ background: t.color }}>
                    {t.name[0]}
                  </span>
                  <span>
                    <span className="testimonial-name">{t.name}</span>
                    <span className="testimonial-role">{t.role}</span>
                  </span>
                </figcaption>
              </figure>
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

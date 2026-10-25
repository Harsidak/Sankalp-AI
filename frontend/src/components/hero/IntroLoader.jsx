/**
 * IntroLoader — a full-screen splash that plays once, before the home page
 * reveals.
 *
 * Three beats, not two:
 *   1. Form  — stars scattered around the edges streak inward and are
 *      absorbed as the orb grows at the centre of the screen (reuses
 *      AuraOrb's own SVG, so the art is identical to the hero's real orb).
 *      A ring traces its own completion in lockstep, and a soft flash marks
 *      the moment the orb finishes solidifying.
 *   2. Travel — the backdrop and every decoration (ring, stars) dissolve
 *      away together, *revealing* the home page rather than cutting to it.
 *      At the same time the now-formed orb — and only the orb — glides from
 *      the centre of the screen to the hero's real on-page orb slot,
 *      shrinking to match it en route. It is one continuous element making
 *      one continuous move, not two different orbs handing off.
 *   3. Dock — the moment the travelling orb's box exactly matches the hero
 *      orb's box, this unmounts and the real hero orb (kept invisible until
 *      this instant) is revealed in its place. Because the two rects are
 *      identical at that instant, the swap is imperceptible.
 *
 * The Landing page keeps rendering normally underneath this the entire
 * time — it is not a route or a data-loading gate, just a curtain in front
 * of a page that was already ready, with a hole cut for the orb to fly
 * through.
 */

import { useEffect, useRef, useState } from 'react';
import AuraOrb from './AuraOrb';

const PARTICLE_COUNT = 18;
const BUILD_MS = 2000;
const TRAVEL_MS = 700;

// Deterministic placement (angle evenly spaced, radius/size/timing jittered
// by index) so every load looks the same — no Math.random for a one-shot.
const PARTICLES = Array.from({ length: PARTICLE_COUNT }, (_, i) => {
  const angle = (i / PARTICLE_COUNT) * Math.PI * 2;
  const radius = 240 + ((i * 53) % 180);
  return {
    x: Math.round(Math.cos(angle) * radius),
    y: Math.round(Math.sin(angle) * radius),
    size: 2 + (i % 3),
    delay: (i % 9) * 0.1,
    duration: 0.95 + (i % 2) * 0.1,
  };
});

export default function IntroLoader({ onDone }) {
  const [closing, setClosing] = useState(false);
  const travelRef = useRef(null);

  // Owns the whole screen while it plays, so the page underneath shouldn't
  // scroll out from under it.
  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, []);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      onDone();
      return undefined;
    }

    const travelTimer = setTimeout(() => {
      const orbEl = travelRef.current;
      const heroSlot = document.querySelector('.orb-anchor');

      if (orbEl && heroSlot) {
        const from = orbEl.getBoundingClientRect();
        const to = heroSlot.getBoundingClientRect();
        const scale = to.width / from.width;
        const dx = to.left + to.width / 2 - (from.left + from.width / 2);
        const dy = to.top + to.height / 2 - (from.top + from.height / 2);
        orbEl.style.setProperty('--travel-x', `${dx}px`);
        orbEl.style.setProperty('--travel-y', `${dy}px`);
        orbEl.style.setProperty('--travel-scale', scale);
      }

      // Flips both the backdrop fade and the orb's travel transform on in
      // the same frame, so the screen clearing and the orb setting off
      // read as one beat.
      setClosing(true);
    }, BUILD_MS);

    const doneTimer = setTimeout(onDone, BUILD_MS + TRAVEL_MS);

    return () => {
      clearTimeout(travelTimer);
      clearTimeout(doneTimer);
    };
  }, [onDone]);

  return (
    <div className="intro-loader" aria-hidden="true">
      <div className={`intro-backdrop${closing ? ' is-fading' : ''}`} />

      <div className={`intro-decor${closing ? ' is-fading' : ''}`}>
        <svg className="intro-ring" viewBox="0 0 220 220">
          <circle cx="110" cy="110" r="100" />
        </svg>

        <div className="intro-flash" />

        <div className="intro-particles">
          {PARTICLES.map((p, i) => (
            <span
              key={i}
              className="intro-particle"
              style={{
                '--px': `${p.x}px`,
                '--py': `${p.y}px`,
                width: `${p.size}px`,
                height: `${p.size}px`,
                marginTop: `${-p.size / 2}px`,
                marginLeft: `${-p.size / 2}px`,
                animationDelay: `${p.delay}s`,
                animationDuration: `${p.duration}s`,
              }}
            />
          ))}
        </div>
      </div>

      <div className={`intro-orb-travel${closing ? ' is-traveling' : ''}`} ref={travelRef}>
        <div className="intro-orb-wrap">
          <AuraOrb className="intro-orb" />
        </div>
      </div>
    </div>
  );
}

/**
 * AuraOrb — the hero centrepiece.
 *
 * A glass sphere with a nebula suspended inside it and orbit rings around it,
 * drawn entirely in SVG so it stays sharp at any size and inherits the theme.
 *
 * Two motions are layered:
 *   - a slow "breath" (CSS keyframes) that never stops, which is the point of
 *     the whole thing;
 *   - a pointer parallax that we drive ourselves. We deliberately do NOT put
 *     the pointer position in React state: that would re-render the tree on
 *     every mousemove. Instead the raw target is written to a ref, and a single
 *     requestAnimationFrame loop eases the current value toward it and writes
 *     the transform straight to the node. The easing is what makes it feel like
 *     the orb has weight rather than being glued to the cursor.
 */

import { useEffect, useRef } from 'react';

/** Fraction of the remaining distance covered each frame. Lower = heavier. */
const EASING = 0.06;
/** Maximum translation in pixels at the edge of the viewport. */
const RANGE = 26;

export default function AuraOrb({ className = '' }) {
  const wrapRef = useRef(null);
  const target = useRef({ x: 0, y: 0 });
  const current = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const node = wrapRef.current;
    if (!node) return undefined;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reduced.matches) return undefined;

    const handleMove = (event) => {
      // Normalise the pointer to -1..1 across the viewport, then scale.
      const nx = (event.clientX / window.innerWidth) * 2 - 1;
      const ny = (event.clientY / window.innerHeight) * 2 - 1;
      target.current = { x: nx * RANGE, y: ny * (RANGE * 0.6) };
    };

    let frame = 0;
    const tick = () => {
      const { x: tx, y: ty } = target.current;
      const cur = current.current;

      cur.x += (tx - cur.x) * EASING;
      cur.y += (ty - cur.y) * EASING;

      node.style.transform = `translate3d(${cur.x.toFixed(2)}px, ${cur.y.toFixed(2)}px, 0)`;
      frame = requestAnimationFrame(tick);
    };

    window.addEventListener('pointermove', handleMove, { passive: true });
    frame = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener('pointermove', handleMove);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div ref={wrapRef} className={`aura-orb ${className}`.trim()} aria-hidden="true">
      <svg viewBox="0 0 520 520" role="presentation">
        <defs>
          {/* The glass body: bright at the upper-left, deep at the lower-right */}
          <radialGradient id="orb-glass" cx="36%" cy="30%" r="78%">
            <stop offset="0%" stopColor="#f6f2ff" stopOpacity="0.95" />
            <stop offset="38%" stopColor="#c9b6ff" stopOpacity="0.85" />
            <stop offset="72%" stopColor="#7c3aed" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#2e1a7a" stopOpacity="0.98" />
          </radialGradient>

          {/* Rim light along the lower edge, the tell that it is a sphere */}
          <linearGradient id="orb-rim" x1="20%" y1="0%" x2="80%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
            <stop offset="45%" stopColor="#ffffff" stopOpacity="0" />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.75" />
          </linearGradient>

          <radialGradient id="orb-halo" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.5" />
            <stop offset="60%" stopColor="#8b5cf6" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
          </radialGradient>

          <radialGradient id="orb-spec" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
          </radialGradient>

          <filter id="orb-soften" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="18" />
          </filter>

          {/* Everything inside the sphere is clipped to it */}
          <clipPath id="orb-clip">
            <circle cx="260" cy="260" r="150" />
          </clipPath>
        </defs>

        {/* Halo */}
        <circle cx="260" cy="260" r="250" fill="url(#orb-halo)" className="orb-halo" />

        {/* Orbit rings — tilted ellipses, each turning at its own rate */}
        <g className="orb-rings" fill="none" strokeLinecap="round">
          <ellipse
            cx="260"
            cy="260"
            rx="228"
            ry="86"
            stroke="#7c3aed"
            strokeOpacity="0.28"
            transform="rotate(-22 260 260)"
          />
          <ellipse
            cx="260"
            cy="260"
            rx="205"
            ry="196"
            stroke="#7c3aed"
            strokeOpacity="0.16"
            strokeDasharray="3 12"
          />
          <ellipse
            cx="260"
            cy="260"
            rx="186"
            ry="72"
            stroke="#a78bfa"
            strokeOpacity="0.34"
            transform="rotate(28 260 260)"
          />
        </g>

        {/* The sphere itself, breathing */}
        <g className="orb-body">
          <circle cx="260" cy="260" r="150" fill="url(#orb-glass)" />

          {/* Nebula suspended inside — slow, offset drifts read as depth */}
          <g clipPath="url(#orb-clip)" filter="url(#orb-soften)" className="orb-nebula">
            <circle cx="205" cy="215" r="72" fill="#ffffff" fillOpacity="0.5" />
            <circle cx="315" cy="300" r="88" fill="#4c1d95" fillOpacity="0.65" />
            <circle cx="240" cy="330" r="60" fill="#6fe0c2" fillOpacity="0.3" />
            <circle cx="330" cy="200" r="52" fill="#ffb59b" fillOpacity="0.32" />
          </g>

          {/* Rim + highlights */}
          <circle
            cx="260"
            cy="260"
            r="150"
            fill="none"
            stroke="url(#orb-rim)"
            strokeWidth="2.5"
          />
          <ellipse
            cx="212"
            cy="196"
            rx="46"
            ry="30"
            fill="url(#orb-spec)"
            transform="rotate(-32 212 196)"
          />
          <circle cx="318" cy="336" r="10" fill="#ffffff" fillOpacity="0.35" />
        </g>

        {/* Motes drifting in the halo */}
        <g className="orb-motes" fill="#7c3aed">
          <circle cx="86" cy="188" r="4" />
          <circle cx="452" cy="228" r="5" />
          <circle cx="140" cy="392" r="3.5" />
          <circle cx="404" cy="404" r="4.5" />
        </g>
      </svg>
    </div>
  );
}

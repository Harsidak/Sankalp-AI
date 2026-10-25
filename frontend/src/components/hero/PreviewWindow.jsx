/**
 * PreviewWindow — a stylised glass "screen" showing what the dashboard feels
 * like, without shipping a real screenshot that would go stale the moment the
 * UI changes. Tilts upright as it scrolls into view; the tilt is driven by
 * scroll progress written straight to a CSS var, same no-re-render approach
 * as AuraOrb's pointer parallax.
 */

import { useEffect, useRef } from 'react';

const MOOD_POINTS = [38, 52, 44, 61, 58, 70, 66, 78, 82, 90];

function moodPath(points, w, h) {
  const stepX = w / (points.length - 1);
  const max = Math.max(...points);
  const min = Math.min(...points);
  const coords = points.map((p, i) => {
    const x = i * stepX;
    const y = h - ((p - min) / (max - min || 1)) * h;
    return [x, y];
  });
  return coords.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
}

export default function PreviewWindow({ className = '' }) {
  const wrapRef = useRef(null);

  useEffect(() => {
    const node = wrapRef.current;
    if (!node) return undefined;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;

    const handleScroll = () => {
      const rect = node.getBoundingClientRect();
      const vh = window.innerHeight;
      // 0 when the panel's top is at the viewport's bottom edge, 1 once its
      // centre has reached the viewport's centre — clamped either side.
      const raw = (vh - rect.top) / (vh * 0.6);
      const progress = Math.min(1, Math.max(0, raw));
      node.style.setProperty('--tilt-progress', progress.toFixed(3));
    };

    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const w = 280;
  const h = 110;

  return (
    <div ref={wrapRef} className={`preview-window ${className}`.trim()}>
      <div className="preview-chrome">
        <span className="preview-dot" style={{ background: '#e8788a' }} />
        <span className="preview-dot" style={{ background: '#e9a06a' }} />
        <span className="preview-dot" style={{ background: '#7fc08a' }} />
        <span className="preview-url">sankalp.ai/dashboard</span>
      </div>

      <div className="preview-body">
        <div className="preview-card preview-chart">
          <p className="preview-card-label">Mood, last 10 days</p>
          <svg viewBox={`0 0 ${w} ${h}`} width="100%" height="100%" preserveAspectRatio="none">
            <defs>
              <linearGradient id="preview-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#7c3aed" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path
              d={`${moodPath(MOOD_POINTS, w, h)} L${w},${h} L0,${h} Z`}
              fill="url(#preview-fill)"
            />
            <path
              d={moodPath(MOOD_POINTS, w, h)}
              fill="none"
              stroke="#7c3aed"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        <div className="preview-card preview-streak">
          <p className="preview-card-label">Current streak</p>
          <p className="preview-streak-num">17</p>
          <p className="preview-streak-sub">days running</p>
        </div>

        <div className="preview-card preview-journal">
          <p className="preview-card-label">Today&apos;s entry</p>
          <p className="preview-journal-line">
            &ldquo;Slower morning, but the walk helped more than I expected.&rdquo;
          </p>
          <div className="preview-tags">
            <span>sleep</span>
            <span>gratitude</span>
          </div>
        </div>
      </div>
    </div>
  );
}

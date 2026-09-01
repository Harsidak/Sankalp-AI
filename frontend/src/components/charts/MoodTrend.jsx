/**
 * MoodTrend — mood and energy over the trailing window, drawn by hand in SVG.
 *
 * Two things make this more than a polyline:
 *
 *   1. Days without a check-in arrive as null. Interpolating across them would
 *      invent data, so the series is split into runs of consecutive readings
 *      and each run is drawn as its own path — the line genuinely breaks.
 *   2. The curve is a Catmull-Rom spline converted to cubic béziers, which
 *      passes exactly through every point instead of rounding corners off the
 *      way a naive quadratic smoother does.
 *
 * The chart is drawn in a fixed 1000x320 user space and scaled by the
 * viewBox, so it is resolution-independent and needs no resize listener.
 */

import { useMemo, useState } from 'react';

const W = 1000;
const H = 320;
const PAD = { top: 24, right: 16, bottom: 34, left: 34 };

const MIN = 1;
const MAX = 5;

/** Split a series into runs of consecutive non-null readings. */
function toRuns(points, key) {
  const runs = [];
  let run = [];

  points.forEach((point, i) => {
    const value = point[key];
    if (value === null || value === undefined) {
      if (run.length) runs.push(run);
      run = [];
      return;
    }
    run.push({ i, value });
  });

  if (run.length) runs.push(run);
  return runs;
}

/**
 * Catmull-Rom through the given points, emitted as cubic béziers.
 * A single point becomes a dot (handled by the caller); two become a line.
 */
function splinePath(coords) {
  if (coords.length === 1) return '';
  if (coords.length === 2) {
    return `M${coords[0].x},${coords[0].y}L${coords[1].x},${coords[1].y}`;
  }

  let d = `M${coords[0].x},${coords[0].y}`;

  for (let i = 0; i < coords.length - 1; i += 1) {
    const p0 = coords[i - 1] || coords[i];
    const p1 = coords[i];
    const p2 = coords[i + 1];
    const p3 = coords[i + 2] || p2;

    // Tension 1/6 is the standard uniform Catmull-Rom to bézier conversion.
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;

    d += `C${c1x},${c1y} ${c2x},${c2y} ${p2.x},${p2.y}`;
  }

  return d;
}

export default function MoodTrend({ points = [] }) {
  const [hover, setHover] = useState(null);

  const geometry = useMemo(() => {
    const n = Math.max(points.length - 1, 1);
    const innerW = W - PAD.left - PAD.right;
    const innerH = H - PAD.top - PAD.bottom;

    const x = (i) => PAD.left + (i / n) * innerW;
    const y = (v) => PAD.top + innerH - ((v - MIN) / (MAX - MIN)) * innerH;

    const build = (key) =>
      toRuns(points, key).map((run) => ({
        coords: run.map((p) => ({ x: x(p.i), y: y(p.value) })),
        path: splinePath(run.map((p) => ({ x: x(p.i), y: y(p.value) }))),
      }));

    const mood = build('mood');

    // Area fill: only under runs long enough to have an area.
    const areas = mood
      .filter((run) => run.coords.length > 1)
      .map((run) => {
        const first = run.coords[0];
        const last = run.coords[run.coords.length - 1];
        return `${run.path}L${last.x},${H - PAD.bottom}L${first.x},${H - PAD.bottom}Z`;
      });

    return { x, y, mood, energy: build('energy'), areas };
  }, [points]);

  if (!points.length) {
    return <p className="chart-empty">No check-ins in this window yet.</p>;
  }

  const handleMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    // Map the pointer back into the chart's own 1000-unit coordinate space.
    const local = ((event.clientX - rect.left) / rect.width) * W;
    const n = Math.max(points.length - 1, 1);
    const ratio = (local - PAD.left) / (W - PAD.left - PAD.right);
    const index = Math.round(Math.min(Math.max(ratio, 0), 1) * n);
    setHover(index);
  };

  const active = hover === null ? null : points[hover];

  return (
    <div className="chart">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        onPointerMove={handleMove}
        onPointerLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id="mood-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.28" />
            <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Gridlines, one per mood level */}
        {[1, 2, 3, 4, 5].map((level) => (
          <g key={level}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={geometry.y(level)}
              y2={geometry.y(level)}
              className="chart-grid"
            />
            <text x={4} y={geometry.y(level) + 4} className="chart-axis">
              {level}
            </text>
          </g>
        ))}

        {geometry.areas.map((d) => (
          <path key={d} d={d} fill="url(#mood-area)" />
        ))}

        {geometry.energy.map((run) => (
          <path key={run.path || run.coords[0].x} d={run.path} className="chart-line is-energy" />
        ))}

        {geometry.mood.map((run) => (
          <path key={run.path || run.coords[0].x} d={run.path} className="chart-line is-mood" />
        ))}

        {/* Isolated readings would otherwise be invisible: a run of one has no path */}
        {geometry.mood
          .filter((run) => run.coords.length === 1)
          .map((run) => (
            <circle
              key={`${run.coords[0].x}-dot`}
              cx={run.coords[0].x}
              cy={run.coords[0].y}
              r="4"
              className="chart-dot"
            />
          ))}

        {active && active.mood !== null && (
          <g className="chart-cursor">
            <line
              x1={geometry.x(hover)}
              x2={geometry.x(hover)}
              y1={PAD.top}
              y2={H - PAD.bottom}
            />
            <circle cx={geometry.x(hover)} cy={geometry.y(active.mood)} r="6" />
          </g>
        )}
      </svg>

      <div className="chart-legend">
        <span className="key is-mood">Mood</span>
        <span className="key is-energy">Energy</span>
        {active && (
          <span className="chart-readout">
            {new Date(active.day).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
            })}
            {' — '}
            {active.mood === null
              ? 'no check-in'
              : `mood ${active.mood.toFixed(1)}, energy ${active.energy?.toFixed(1) ?? '—'}`}
          </span>
        )}
      </div>
    </div>
  );
}

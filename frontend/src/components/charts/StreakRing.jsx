/**
 * StreakRing — a progress ring driven by stroke-dashoffset.
 *
 * The trick is to make the dash pattern exactly one circumference long: the
 * offset then reads directly as "how much of the ring is missing", so the
 * animation is a single transitioned number rather than an arc path that has
 * to be recomputed on every render.
 */

const SIZE = 120;
const STROKE = 10;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function StreakRing({ value = 0, target = 7, color = 'var(--brand)', label }) {
  const ratio = target > 0 ? Math.min(value / target, 1) : 0;

  return (
    <div className="ring">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width={SIZE} height={SIZE}>
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="var(--border)"
          strokeWidth={STROKE}
        />
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - ratio)}
          transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
          className="ring-progress"
        />
      </svg>
      <div className="ring-label">
        <strong>{value}</strong>
        <span>{label ?? `of ${target}`}</span>
      </div>
    </div>
  );
}

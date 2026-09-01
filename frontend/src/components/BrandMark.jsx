/**
 * The SankalpAI mark: a resolve knot — one continuous stroke turning back on
 * itself — inside the aura ring. Uses currentColor so it inherits wherever it
 * is placed (dark nav, light nav, gradient panel).
 */

export default function BrandMark({ className = '' }) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label="SankalpAI"
    >
      <circle cx="16" cy="16" r="14.5" stroke="currentColor" strokeOpacity="0.35" />
      <path
        d="M22 10.5c-2.6-2.2-6.4-1.6-7.7 1.1-1.2 2.5.6 4.4 2.6 5.2 2.4 1 4 2.6 3 5.1-1.2 2.9-5.2 3.4-8 1.3"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <circle cx="16" cy="16" r="8" stroke="currentColor" strokeOpacity="0.25" />
    </svg>
  );
}

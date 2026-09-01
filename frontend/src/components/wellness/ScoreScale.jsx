/**
 * The 1-5 picker used for both mood and energy.
 *
 * Rendered as a radio group rather than five buttons so the arrow keys work
 * and a screen reader announces it as one question with five answers.
 */

export default function ScoreScale({ name, value, labels, onChange, tint = true }) {
  return (
    <div className="score-scale" role="radiogroup" aria-label={name}>
      {labels.map((label, index) => {
        const score = index + 1;
        const isActive = value === score;
        return (
          <button
            key={score}
            type="button"
            role="radio"
            aria-checked={isActive}
            className={`score-option${isActive ? ' is-active' : ''}`}
            style={tint ? { '--score-tint': `var(--mood-${score})` } : undefined}
            onClick={() => onChange(score)}
          >
            <span className="score-value">{score}</span>
            <span className="score-label">{label}</span>
          </button>
        );
      })}
    </div>
  );
}

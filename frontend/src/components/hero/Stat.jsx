import { useCountUp } from '../../hooks/useCountUp';

export default function Stat({ value, prefix = '', suffix = '', label }) {
  const [ref, display] = useCountUp(value);

  return (
    <div className="stat" ref={ref}>
      <span className="stat-value">
        {prefix}
        {display.toLocaleString()}
        {suffix}
      </span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

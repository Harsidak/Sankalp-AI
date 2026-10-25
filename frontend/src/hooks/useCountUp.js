/**
 * useCountUp — animates a number from 0 to `value` once its node enters the
 * viewport. Runs its own IntersectionObserver (one target, not the shared
 * reveal root) so it can read the eased progress every frame instead of only
 * a boolean. Returns a ref to attach and the current display value.
 */

import { useEffect, useRef, useState } from 'react';

const easeOutExpo = (t) => (t === 1 ? 1 : 1 - 2 ** (-10 * t));

export function useCountUp(value, { duration = 1400 } = {}) {
  const nodeRef = useRef(null);
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const node = nodeRef.current;
    if (!node) return undefined;

    if (
      typeof IntersectionObserver === 'undefined' ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      setDisplay(value);
      return undefined;
    }

    let frame = 0;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const start = performance.now();

          const tick = (now) => {
            const t = Math.min(1, (now - start) / duration);
            setDisplay(Math.round(easeOutExpo(t) * value));
            if (t < 1) frame = requestAnimationFrame(tick);
          };

          frame = requestAnimationFrame(tick);
          observer.unobserve(node);
        });
      },
      { threshold: 0.4 }
    );

    observer.observe(node);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value, duration]);

  return [nodeRef, display];
}

/**
 * useReveal — fade sections in as they enter the viewport.
 *
 * Returns a ref for a container. Every descendant carrying `.reveal` is
 * observed once and given `.is-visible` on entry, then unobserved: the effect
 * is a first impression, not a scroll toy, and re-animating on the way back up
 * is what makes these things feel cheap.
 *
 * A single observer serves all children, so adding sections to the page costs
 * nothing extra.
 */

import { useEffect, useRef } from 'react';

export function useReveal({ threshold = 0.15, stagger = 70 } = {}) {
  const containerRef = useRef(null);

  useEffect(() => {
    const root = containerRef.current;
    if (!root) return undefined;

    const targets = root.querySelectorAll('.reveal');

    // No IntersectionObserver, or the user prefers stillness: show everything.
    if (
      typeof IntersectionObserver === 'undefined' ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      targets.forEach((el) => el.classList.add('is-visible'));
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;

          // Siblings revealing together cascade rather than snapping in as a block.
          const siblings = [...entry.target.parentElement.children];
          const delay = Math.max(0, siblings.indexOf(entry.target)) * stagger;

          entry.target.style.transitionDelay = `${delay}ms`;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      },
      { threshold, rootMargin: '0px 0px -8% 0px' }
    );

    targets.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [threshold, stagger]);

  return containerRef;
}

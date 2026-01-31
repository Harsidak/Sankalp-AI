// Visual Effects Module

// 1. Tilt Effect for Cards
export function initTiltEffect() {
    const cards = document.querySelectorAll('.glass-panel');

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Set mouse position for glow effect
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);

            // Subtle rotation
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -2; // max -2deg
            const rotateY = ((x - centerX) / centerX) * 2;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
        });
    });
}

// 2. Navbar Scroll Effect
export function initNavbarScroll() {
    const nav = document.getElementById('main-nav');
    if (!nav) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            nav.classList.add('nav-glass', 'py-4');
            nav.classList.remove('py-6');
        } else {
            nav.classList.remove('nav-glass', 'py-4');
            nav.classList.add('py-6');
        }
    });
}

// 3. Scroll Reveal (Intersection Observer)
export function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-enter');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('section > div, .glass-panel').forEach(el => {
        el.style.opacity = '0'; // Initial state handled by css class if applied, but logic ensures it
        el.classList.add('transition-opacity');
        observer.observe(el);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initTiltEffect();
    initNavbarScroll();
    initScrollReveal();
});

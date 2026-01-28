/**
 * Sankalp Visual Effects Library
 * Implements: ASCII Text, Dither Background, Card Swap
 */

// --- ASCII Text Animation ---
class AsciiText {
    constructor(element) {
        this.element = element;
        this.originalText = element.innerText;
        this.chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdifghijklmnopqrstuvwxyz1234567890!@#$%^&*()_+";
        this.frameRequest = null;
        this.frame = 0;
        this.totalFrames = 40; // Duration of effect

        this.element.addEventListener('mouseover', () => this.startEffect());
        // Auto start once on load
        setTimeout(() => this.startEffect(), 500);
    }

    startEffect() {
        this.frame = 0;
        cancelAnimationFrame(this.frameRequest);
        this.animate();
    }

    animate() {
        this.frame++;
        const progress = this.frame / this.totalFrames;

        let output = '';
        for (let i = 0; i < this.originalText.length; i++) {
            if (i < Math.floor(this.originalText.length * progress)) {
                output += this.originalText[i];
            } else if (this.originalText[i] === ' ' || this.originalText[i] === '\n') {
                output += this.originalText[i];
            } else {
                output += this.chars[Math.floor(Math.random() * this.chars.length)];
            }
        }

        this.element.innerText = output;

        if (this.frame < this.totalFrames) {
            this.frameRequest = requestAnimationFrame(() => this.animate());
        } else {
            this.element.innerText = this.originalText; // Ensure clean finish
        }
    }
}

// --- Wave Background (Canvas) ---
// Props from User:
// R,G,B: 0.5 | Intensity: 4 | Amp: 0.3 | Freq: 3 | Speed: 0.05 | Mouse: 0.3
class WaveBackground {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');

        // Config
        this.config = {
            r: 0.5, g: 0.5, b: 0.5,
            intensity: 4,
            amplitude: 0.3,
            frequency: 3,
            speed: 0.05,
            mouseRadius: 0.3
        };

        this.time = 0;
        this.mouseX = 0;
        this.mouseY = 0;

        this.resize();
        window.addEventListener('resize', () => this.resize());
        window.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX / window.innerWidth;
            this.mouseY = e.clientY / window.innerHeight;
        });

        this.startLoop();
    }

    resize() {
        this.w = this.canvas.width = window.innerWidth;
        this.h = this.canvas.height = window.innerHeight;
    }

    startLoop() {
        const loop = () => {
            this.time += this.config.speed * 0.1;
            this.ctx.fillStyle = '#050511'; // Base dark
            this.ctx.fillRect(0, 0, this.w, this.h);

            // Draw Waves
            this.ctx.beginPath();

            // Generate multiple lines
            for (let i = 0; i < 5; i++) {
                this.drawWave(i);
            }

            requestAnimationFrame(loop);
        };
        loop();
    }

    drawWave(layerIndex) {
        const { r, g, b, intensity, amplitude, frequency } = this.config;

        this.ctx.beginPath();

        const segmentWidth = 10;
        const yBase = this.h * 0.5 + (layerIndex * 20);

        for (let x = 0; x <= this.w; x += segmentWidth) {
            // Normalized X (0 to 1)
            const nx = x / this.w;

            // Physics
            // Interaction with mouse
            const dx = nx - this.mouseX;
            const dist = Math.abs(dx);
            const mouseEffect = Math.max(0, this.config.mouseRadius - dist) * 100;

            const sine = Math.sin((nx * frequency * 10) + this.time + (layerIndex * 1.5));
            const yOffset = sine * (amplitude * 200) + mouseEffect;

            const y = yBase + yOffset;

            if (x === 0) this.ctx.moveTo(x, y);
            else this.ctx.lineTo(x, y);
        }

        // Color Calculation based on RGB props + Intensity
        // We'll map 0.5 to a mid-range color channel
        const alpha = (0.1 * intensity);
        const red = Math.floor(r * 255);
        const green = Math.floor(g * 255);
        const blue = Math.floor(b * 255) + (layerIndex * 20); // Add variation

        this.ctx.strokeStyle = `rgba(${red}, ${green}, ${blue}, ${alpha})`;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }
}

// --- Card Swap (Stacked Cards) ---
class CardSwap {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        this.cards = Array.from(this.container.querySelectorAll('.swap-card'));
        this.activeIndex = 0;

        // Initial Stack Order
        this.updateStack();

        // Bind clicks
        this.cards.forEach(card => {
            card.addEventListener('click', (e) => this.handleCardClick(e));
        });
    }

    handleCardClick(e) {
        const clickedCard = e.currentTarget;

        // Only allow clicking the top card
        if (clickedCard !== this.cards[this.cards.length - 1]) return;

        // Animate Out
        clickedCard.style.animation = "swapOut 0.6s cubic-bezier(0.25, 1, 0.5, 1) forwards";

        setTimeout(() => {
            // Move to bottom of DOM (back of stack)
            this.container.prepend(clickedCard);
            clickedCard.style.animation = ""; // Reset animation

            // Re-fetch array order
            this.cards = Array.from(this.container.querySelectorAll('.swap-card'));
            this.updateStack();
        }, 500);
    }

    updateStack() {
        // Render stack visual: Last item is top, others scaled down behind
        this.cards.forEach((card, index) => {
            const reverseIndex = this.cards.length - 1 - index; // 0 = top

            card.style.zIndex = index;
            card.style.transform = `scale(${1 - (reverseIndex * 0.05)}) translateY(${reverseIndex * -15}px)`;
            card.style.filter = reverseIndex === 0 ? 'blur(0px) brightness(1)' : `blur(${reverseIndex * 2}px) brightness(${1 - reverseIndex * 0.15})`;
            card.style.opacity = reverseIndex > 2 ? 0 : 1; // Hide deep cards
            card.style.pointerEvents = reverseIndex === 0 ? 'auto' : 'none';
        });
    }
}

// Auto-init logic
document.addEventListener('DOMContentLoaded', () => {
    // 1. ASCII on H1 spans
    document.querySelectorAll('[data-ascii]').forEach(el => new AsciiText(el));

    // 2. Wave Background (formerly Dither)
    if (document.getElementById('dither-canvas')) new WaveBackground('dither-canvas');

    // 3. Card Swap
    if (document.getElementById('card-stack-container')) new CardSwap('card-stack-container');
});

// --- FAQ Interaction ---
window.toggleFaq = (header) => {
    const item = header.parentElement;
    const isActive = item.classList.contains('active');

    // Close all
    document.querySelectorAll('.faq-item').forEach(el => el.classList.remove('active'));

    // Toggle clicked
    if (!isActive) {
        item.classList.add('active');
    }
};

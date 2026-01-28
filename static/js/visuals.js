/**
 * Sankalp Visual Effects Library
 * Implements: FAQ Interactions
 */

// --- FAQ Interaction ---
window.toggleFaq = (header) => {
    const item = header.parentElement;
    const itemContent = item.querySelector('.faq-answer');
    const isActive = item.classList.contains('active');

    // Close all
    document.querySelectorAll('.faq-item').forEach(el => {
        el.classList.remove('active');
        // Reset height if we were animating it (optional, but good for smooth accordion)
        // el.querySelector('.faq-answer').style.maxHeight = null; 
    });

    // Toggle clicked
    if (!isActive) {
        item.classList.add('active');
        // itemContent.style.maxHeight = itemContent.scrollHeight + "px";
    }
};

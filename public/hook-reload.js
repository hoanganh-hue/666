// public/hook-reload.js
// This file contains logic to reload the BeEF hook if it becomes unresponsive.

// This is a simplified example. In a real scenario, you'd monitor BeEF's
// communication (e.g., heartbeats) to determine unresponsiveness.

const HOOK_TIMEOUT = 60000; // 60 seconds
let lastHookActivity = Date.now();

function monitorHookActivity() {
    // In a real BeEF setup, BeEF's hooked browser JavaScript would update
    // a global variable or send a heartbeat. For this example, we'll just
    // simulate activity.
    // For a more robust solution, you'd need to inspect BeEF's internal workings.
    // For now, we'll assume the hook is active if the page is active.
    
    if (Date.now() - lastHookActivity > HOOK_TIMEOUT) {
        console.warn('BeEF hook appears unresponsive. Reloading page to re-inject hook.');
        window.location.reload(true); // Force reload from server
    }
}

// Update last activity on user interaction (simple heuristic)
document.addEventListener('mousemove', () => { lastHookActivity = Date.now(); });
document.addEventListener('keydown', () => { lastHookActivity = Date.now(); });

setInterval(monitorHookActivity, HOOK_TIMEOUT / 2); // Check every half timeout

console.log('BeEF Hook Reload script loaded.');
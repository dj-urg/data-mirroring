/**
 * Session Cleanup Handler
 * Ensures immediate cleanup when browser is closed or session ends
 */

document.addEventListener('DOMContentLoaded', function () {
    // Track session activity
    let sessionActive = true;
    let cleanupTriggered = false;

    // Function to trigger cleanup
    function triggerCleanup() {
        if (cleanupTriggered) return;
        cleanupTriggered = true;

        // Send cleanup request to server
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

        fetch('/cleanup-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ cleanup: true })
        }).catch(error => {
            console.log('Cleanup request failed (session may have already ended):', error);
        });
    }

    // Cleanup on page unload (browser close, navigation, refresh)
    window.addEventListener('beforeunload', function (e) {
        triggerCleanup();
    });

    // Cleanup on page visibility change (tab switch, minimize)
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            // Page is hidden, but don't cleanup yet - user might come back
            sessionActive = false;
        } else {
            // Page is visible again
            sessionActive = true;
        }
    });

    // Cleanup when page is hidden for more than 5 minutes
    let hiddenTimer;
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            hiddenTimer = setTimeout(() => {
                if (!sessionActive) {
                    triggerCleanup();
                }
            }, 300000); // 5 minutes
        } else {
            if (hiddenTimer) {
                clearTimeout(hiddenTimer);
            }
        }
    });

    // Cleanup on session timeout (30 minutes of inactivity)
    let inactivityTimer;
    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            triggerCleanup();
        }, 1800000); // 30 minutes
    }

    // Reset timer on user activity
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer, true);
    });

    // Initialize timer
    resetInactivityTimer();

    // Cleanup on explicit session end
    const endSessionBtn = document.querySelector('.end-session-btn');
    if (endSessionBtn) {
        endSessionBtn.addEventListener('click', function () {
            triggerCleanup();
        });
    }
});

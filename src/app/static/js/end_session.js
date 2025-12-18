/**
 * End Session Button Handler
 * Handles the confirmation dialog for ending the session
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find the end session button
    const endSessionBtn = document.querySelector('.end-session-btn');
    
    if (endSessionBtn) {
        endSessionBtn.addEventListener('click', function(e) {
            // Show confirmation dialog
            const confirmed = confirm('This will immediately delete all your data and end your session. Continue?');
            
            // If the user cancels, prevent navigation
            if (!confirmed) {
                e.preventDefault();
            }
        });
    }
});

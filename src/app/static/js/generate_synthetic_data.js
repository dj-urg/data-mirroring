document.addEventListener('DOMContentLoaded', function() {
    // Elements for form submission
    const generateButton = document.getElementById('generateButton');
    const personaTypeInput = document.getElementById('personaType');
    const activityLevelInput = document.getElementById('activityLevel');
    const outputFilenameInput = document.getElementById('outputFilename');
    const resultCard = document.getElementById('resultCard');
    const statsMessage = document.getElementById('statsMessage');
    const downloadLink = document.getElementById('downloadLink');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    // Ensure result card is hidden on page load
    // No inline styles - using Bootstrap classes instead
    resultCard.classList.add('d-none');
    
    // Setup card selection with animation
    setupCardSelection('.persona-card', personaTypeInput);
    setupCardSelection('.activity-card', activityLevelInput);
    setupCardSelection('.output-card', outputFilenameInput);
    
    // Function to handle card selection with improved animation
    function setupCardSelection(cardSelector, hiddenInput) {
        const cards = document.querySelectorAll(cardSelector);
        
        cards.forEach(card => {
            card.addEventListener('click', function() {
                // Remove selected class from all cards in the group with animation
                cards.forEach(c => {
                    if (c.classList.contains('selected')) {
                        c.classList.add('unselecting');
                        setTimeout(() => {
                            c.classList.remove('selected');
                            c.classList.remove('unselecting');
                        }, 200);
                    }
                });
                
                // Add selected class to clicked card with animation
                this.classList.add('selecting');
                setTimeout(() => {
                    this.classList.add('selected');
                    this.classList.remove('selecting');
                }, 50);
                
                // Update hidden input value
                hiddenInput.value = this.dataset.value;
            });
        });
    }

    generateButton.addEventListener('click', async function() {
        // Get values from hidden inputs
        const personaType = personaTypeInput.value;
        const activityLevel = activityLevelInput.value;
        const outputFilename = outputFilenameInput.value;

        // Validate that selections have been made
        if (!personaType || !activityLevel || !outputFilename) {
            // Show a more elegant error notification
            showNotification('Please make all selections', 'error');
            return;
        }

        try {
            // Add loading class to button for better UX
            generateButton.classList.add('loading');
            // Disable generate button and show loading spinner
            generateButton.disabled = true;
            generateButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Generating...';
            loadingSpinner.classList.remove('d-none');
            resultCard.classList.add('d-none'); // Ensure the result card is hidden during processing

            // Get CSRF token - Flask adds this to all forms
            const csrfToken = document.querySelector('input[name="csrf_token"]') ? 
                              document.querySelector('input[name="csrf_token"]').value : '';

            // Make an AJAX call to the backend to generate data
            const response = await fetch('/generate_synthetic_data_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    persona_type: personaType,
                    activity_level: activityLevel,
                    output_filename: outputFilename
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Data generation failed');
            }

            const result = await response.json();

            // Only show the result card if data generation was successful
            if (result && result.status === 'success') {
                // Get labels for the message
                const personaLabel = getPersonaLabel(personaType);
                const activityLabel = getActivityLabel(activityLevel);
                
                // Update result card with appropriate message based on file type
                if (outputFilename === 'liked_posts.json') {
                    statsMessage.textContent = `Generated ${result.total_likes} likes for a ${personaLabel} with ${activityLabel} activity.`;
                } else if (outputFilename === 'saved_posts.json') {
                    statsMessage.textContent = `Generated ${result.total_saves} saves for a ${personaLabel} with ${activityLabel} activity.`;
                } else if (outputFilename === 'videos_watched.json') {
                    statsMessage.textContent = `Generated ${result.total_watches} video watches for a ${personaLabel} with ${activityLabel} activity.`;
                }
                
                // Setup download link with the correct route
                downloadLink.href = `/download/${result.filename}`;
                
                // Animate the result card appearance using classes
                resultCard.classList.add('opacity-0');
                resultCard.classList.remove('d-none');
                setTimeout(() => {
                    resultCard.classList.remove('opacity-0');
                }, 10);
                
                // Scroll to result card with smooth animation
                resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                throw new Error('Data generation returned an invalid response');
            }

        } catch (error) {
            console.error('Error:', error);
            // Show error in result card with animation
            statsMessage.textContent = 'Failed to generate data: ' + error.message;
            resultCard.classList.add('opacity-0');
            resultCard.classList.remove('d-none');
            resultCard.querySelector('.alert').className = 'alert alert-danger'; // Change to error styling
            setTimeout(() => {
                resultCard.classList.remove('opacity-0');
            }, 10);
        } finally {
            // Remove loading class from button
            generateButton.classList.remove('loading');
            // Re-enable generate button and hide loading spinner
            generateButton.disabled = false;
            generateButton.innerHTML = '<i class="fas fa-cog me-2"></i> Generate Data';
            loadingSpinner.classList.add('d-none');
        }
    });
    
    // Helper functions to get human-readable labels
    function getPersonaLabel(value) {
        const labels = {
            'career': 'Career Professional',
            'fitness': 'Fitness Enthusiast',
            'traveler': 'Travel Blogger',
            'foodie': 'Food & Cooking Lover',
            'techie': 'Tech Enthusiast'
        };
        return labels[value] || value;
    }
    
    function getActivityLabel(value) {
        const labels = {
            'low': 'low (occasional user)',
            'medium': 'medium (regular user)',
            'high': 'high (power user)'
        };
        return labels[value] || value;
    }
    
    // Function to show elegant notifications
    function showNotification(message, type = 'info') {
        // Sanitize message to prevent XSS attacks
        const sanitizedMessage = typeof DOMPurify !== 'undefined' 
            ? DOMPurify.sanitize(message) 
            : message.replace(/[<>]/g, ''); // Basic fallback if DOMPurify not available
        
        // Validate type to prevent XSS in className
        const allowedTypes = ['info', 'error', 'success', 'warning'];
        const safeType = allowedTypes.includes(type) ? type : 'info';
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${safeType}`;
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas fa-${safeType === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            </div>
            <div class="notification-message">${sanitizedMessage}</div>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 4000);
    }
    
    // Add subtle animations to page elements
    function addPageAnimations() {
        // Fade in cards sequentially
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in');
            }, 100 * index);
        });
        
        // Subtle hover effects on cards
        const allCards = document.querySelectorAll('.persona-card, .activity-card, .output-card');
        allCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.classList.add('hover-effect');
            });
            card.addEventListener('mouseleave', function() {
                this.classList.remove('hover-effect');
            });
        });
    }
    
    // Initialize animations
    addPageAnimations();
});
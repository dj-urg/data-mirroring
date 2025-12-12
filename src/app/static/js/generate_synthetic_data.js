// generate_synthetic_data.js

// Trusted Types policy (if supported)
let ttPolicy = null;
if (window.trustedTypes) {
    ttPolicy = window.trustedTypes.createPolicy('default', {
        createHTML: (input) => DOMPurify.sanitize(input)
    });
} else {
    // console.warn("Trusted Types not supported...");
}

document.addEventListener('DOMContentLoaded', function () {
    const generateButton = document.getElementById('generateButton');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultCard = document.getElementById('resultCard');
    const statsMessage = document.getElementById('statsMessage');
    const downloadLink = document.getElementById('downloadLink');
    const closeOverlayBtn = document.getElementById('closeOverlayBtn');

    // --- Event Listeners for Platform Switching ---
    document.querySelectorAll('input[name="platform"]').forEach(input => {
        input.addEventListener('change', function () {
            updateSelectionState();
            updatePlatformVisibility(this.value);
        });
    });

    // --- Close Overlay Listener ---
    if (closeOverlayBtn) {
        closeOverlayBtn.addEventListener('click', function () {
            resultCard.classList.add('d-none');
        });
    }

    // --- Event Listeners for Styling Selected States ---
    const selectorGroups = ['persona', 'activity', 'output_filename'];
    selectorGroups.forEach(group => {
        document.querySelectorAll(`input[name="${group}"]`).forEach(input => {
            input.addEventListener('change', updateSelectionState);
        });
    });

    // --- Generate Button Listener ---
    if (generateButton) {
        generateButton.addEventListener('click', handleGenerate);
    }

    // Initialize View
    const checkedPlatform = document.querySelector('input[name="platform"]:checked');
    if (checkedPlatform) {
        updatePlatformVisibility(checkedPlatform.value);
    }
    updateSelectionState();

    // --- Functions ---

    function updateSelectionState() {
        // Clear all selected classes
        document.querySelectorAll('label.selection-label').forEach(lbl => {
            lbl.classList.remove('selected');
        });

        // Add selected class to checked inputs' parents
        document.querySelectorAll('input[type="radio"]:checked').forEach(input => {
            const label = input.closest('label');
            if (label) {
                label.classList.add('selected');
            }
        });
    }

    function updatePlatformVisibility(platform) {
        // Hide all platform specific output options
        document.querySelectorAll('.platform-specific').forEach(el => {
            el.classList.add('d-none');
            // Check if hidden input was checked, if so, uncheck it to ensure we don't submit wrong file
            const radio = el.querySelector('input[type="radio"]');
            if (radio && radio.checked) {
                radio.checked = false;
                el.classList.remove('selected');
            }
        });

        // Show options for the selected platform
        const visibleOptions = document.querySelectorAll(`.platform-specific.${platform}`);
        visibleOptions.forEach(el => {
            el.classList.remove('d-none');
        });

        // Select the first available option for this platform by default if none selected
        const currentOutput = document.querySelector('input[name="output_filename"]:checked');
        if (!currentOutput && visibleOptions.length > 0) {
            const firstOption = visibleOptions[0];
            const radio = firstOption.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                updateSelectionState();
            }
        }
    }

    async function handleGenerate() {
        // Collect Data directly from form
        const form = document.getElementById('personaForm');
        const formData = new FormData(form);

        const platform = formData.get('platform');
        const persona = formData.get('persona');
        const activity = formData.get('activity');
        const outputFilename = formData.get('output_filename');

        if (!platform || !persona || !activity || !outputFilename) {
            alert("Please select all options.");
            return;
        }

        // UI Loading
        generateButton.disabled = true;
        loadingSpinner.classList.remove('d-none');
        resultCard.classList.add('d-none');

        try {
            // Map form data to API expectation
            const payload = {
                platform: platform,
                persona_type: persona,
                activity_level: activity,
                output_filename: outputFilename
            };

            const response = await fetch('/generate_synthetic_data_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                let successMsg = `Successfully generated ${data.total_items} items for ${platform}.`;
                if (ttPolicy) {
                    statsMessage.innerHTML = ttPolicy.createHTML(successMsg);
                } else {
                    statsMessage.innerHTML = DOMPurify.sanitize(successMsg);
                }

                downloadLink.href = `/download/${data.filename}`;
                downloadLink.download = data.filename;

                resultCard.classList.remove('d-none');

                // Scroll to result
                resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                alert(data.error || "Generation failed.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred during generation.");
        } finally {
            generateButton.disabled = false;
            loadingSpinner.classList.add('d-none');
        }
    }
});
document.addEventListener('DOMContentLoaded', function() {
    const generateButton = document.getElementById('generateButton');
    const personaTypeSelect = document.getElementById('personaType');
    const activityLevelSelect = document.getElementById('activityLevel');
    const outputFilenameSelect = document.getElementById('outputFilename');
    const resultCard = document.getElementById('resultCard');
    const statsMessage = document.getElementById('statsMessage');
    const downloadLink = document.getElementById('downloadLink');

    generateButton.addEventListener('click', async function() {
        // Collect form data
        const personaType = personaTypeSelect.value;
        const activityLevel = activityLevelSelect.value;
        const outputFilename = outputFilenameSelect.value;

        try {
            // Disable generate button during processing
            generateButton.disabled = true;
            generateButton.textContent = 'Generating...';

            // Make an AJAX call to the backend to generate data
            const response = await fetch('/generate_synthetic_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    persona_type: personaType,
                    activity_level: activityLevel,
                    output_filename: outputFilename
                })
            });

            if (!response.ok) {
                throw new Error('Data generation failed');
            }

            const result = await response.json();

            // Update result card
            statsMessage.textContent = `Generated ${result.total_saves} saves, ${result.total_likes} likes, and ${result.total_watches} video watches for a ${personaType} persona with ${activityLevel} activity.`;
            
            // Setup download link
            downloadLink.href = `/download/${outputFilename}`;
            resultCard.style.display = 'block';

        } catch (error) {
            console.error('Error:', error);
            statsMessage.textContent = 'Failed to generate data. Please try again.';
            resultCard.style.display = 'block';
        } finally {
            // Re-enable generate button
            generateButton.disabled = false;
            generateButton.textContent = 'Generate Data';
        }
    });
});
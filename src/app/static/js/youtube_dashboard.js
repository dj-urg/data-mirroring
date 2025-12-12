document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const loader = document.querySelector(".loader"); // Get the loader element
    const loaderOverlay = document.querySelector(".loader-overlay"); // Get the overlay element
    const uploadButton = document.getElementById("uploadButton");

    // Check if all required elements exist
    if (!uploadForm || !fileInput || !loader || !uploadButton || !loaderOverlay) {
        console.warn("One or more elements not found. Skipping event listeners.");
        return;
    }

    // Hide the loader and overlay initially
    loader.classList.add("d-none");
    loaderOverlay.classList.add("d-none");

    // Add event listener for form submission
    uploadForm.addEventListener("submit", function (event) {
        // Validate file input
        if (fileInput.files.length === 0) {
            alert("Please select a file before uploading.");
            event.preventDefault(); // Prevent form submission
            return;
        }

        // Disable the upload button to prevent multiple submissions
        uploadButton.disabled = true;

        // Show the loader and overlay
        loader.classList.remove("d-none");
        loaderOverlay.classList.remove("d-none");

        // Optionally, disable the form itself (if needed)
        uploadForm.classList.add("disabled");
    });

    // --- Image Enlargement Functionality ---
    const visualizationDivs = document.querySelectorAll('#visualization, #month-heatmap, #day-heatmap, #time-heatmap');
    const body = document.body;
    let enlargedOverlay = null;

    visualizationDivs.forEach(function (div) {
        const img = div.querySelector('.visualization-image');
        if (img) {
            img.style.cursor = 'pointer'; // Indicate it's clickable
            img.addEventListener('click', function () {
                const imageUrl = this.src;
                createEnlargedImageOverlay(imageUrl);
            });
        }
    });

    function createEnlargedImageOverlay(imageUrl) {
        if (enlargedOverlay) {
            enlargedOverlay.remove();
        }

        enlargedOverlay = document.createElement('div');
        enlargedOverlay.classList.add('enlarged-image-overlay');

        const imageContainer = document.createElement('div');
        imageContainer.classList.add('enlarged-image-container');

        const enlargedImg = document.createElement('img');
        enlargedImg.src = imageUrl;
        enlargedImg.classList.add('enlarged-image');
        enlargedImg.alt = 'Enlarged Visualization';

        const closeButton = document.createElement('button');
        closeButton.classList.add('close-enlarged-image');
        closeButton.innerHTML = '&times;'; // Use an "X"

        closeButton.addEventListener('click', closeEnlargedImage);
        enlargedOverlay.addEventListener('click', function (event) {
            if (event.target === this) { // Close if clicked outside the image
                closeEnlargedImage();
            }
        });

        imageContainer.appendChild(enlargedImg);
        imageContainer.appendChild(closeButton);
        enlargedOverlay.appendChild(imageContainer);
        body.appendChild(enlargedOverlay);

        // Force reflow to trigger the transition
        void enlargedOverlay.offsetWidth;
        enlargedOverlay.classList.add('active');
        body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    function closeEnlargedImage() {
        if (enlargedOverlay) {
            enlargedOverlay.classList.remove('active');
            setTimeout(() => {
                if (enlargedOverlay) {
                    enlargedOverlay.remove();
                    enlargedOverlay = null;
                    body.style.overflow = ''; // Re-enable background scrolling
                }
            }, 300); // Match the CSS transition duration
        }
    }
});
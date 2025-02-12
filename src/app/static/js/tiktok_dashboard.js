document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");
    const loader = document.querySelector(".loader");
    const loaderOverlay = document.querySelector(".loader-overlay");

    // Ensure all required elements exist
    if (!uploadForm || !fileInput || !uploadButton || !loader || !loaderOverlay) {
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
});
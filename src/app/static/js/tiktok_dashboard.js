document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");
    const loader = document.getElementById("loader");

    if (!uploadForm || !fileInput || !uploadButton || !loader) {
        console.warn("One or more elements not found. Skipping event listeners.");
        return;
    }

    // Ensure the loader is initially hidden
    loader.classList.add("d-none");

    // Add event listener to show loader when the form is submitted
    uploadForm.addEventListener("submit", function () {
        if (fileInput.files.length === 0) {
            alert("Please select a file before uploading.");
            return false; // Prevent form submission
        }

        uploadButton.disabled = true;  // Prevent multiple submissions
        loader.classList.remove("d-none"); // Show loader
    });
});
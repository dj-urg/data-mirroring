document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");
    const loader = document.getElementById("loader");

    // Hide loader initially
    loader.classList.add("d-none");

    // Ensure proper file selection before submission
    uploadForm.addEventListener("submit", function () {
        loader.classList.remove("d-none");  // Show loader
    });
});
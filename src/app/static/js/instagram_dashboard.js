document.getElementById("dataTable").style.display = "block";
document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");
    const loader = document.getElementById("loader");

    // Ensure loader exists before trying to modify it
    if (loader) {
        loader.classList.add("d-none");  // Hide loader initially
    } else {
        console.warn("Loader element not found in the DOM.");
    }

    // Ensure proper file selection before submission
    uploadForm.addEventListener("submit", function () {
        if (loader) {
            loader.classList.remove("d-none");  // Show loader
        }
    });

    function toggleTable() {
        let tableDiv = document.getElementById("dataTable");
        if (tableDiv.style.display === "none") {
            tableDiv.style.display = "block";
        } else {
            tableDiv.style.display = "none";
        }
    };
    

    // Handle file input change
    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            uploadButton.disabled = false;  // Enable upload button when file is selected
        } else {
            uploadButton.disabled = true;  // Disable button if no file is selected
        }
    });
});

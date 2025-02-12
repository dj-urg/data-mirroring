document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");
    const loader = document.querySelector(".loader");
    const loaderOverlay = document.querySelector(".loader-overlay");

    // Ensure loader and overlay exist
    if (loader) {
        loader.classList.add("d-none"); // Hide loader initially
    } else {
        console.warn("Loader element not found in the DOM.");
    }
    if (loaderOverlay) {
        loaderOverlay.classList.add("d-none"); // Hide overlay initially
    } else {
        console.warn("Loader overlay not found in the DOM.");
    }

    // Ensure proper elements are available
    if (!uploadForm || !fileInput || !uploadButton) {
        console.warn("One or more required elements not found. Skipping event listeners.");
        return;
    }

    // Add event listener for form submission
    uploadForm.addEventListener("submit", function (event) {
        // Validate file input
        if (fileInput.files.length === 0) {
            alert("Please select a file before uploading.");
            event.preventDefault(); // Prevent form submission
            return;
        }

        // Show loader and overlay
        if (loader) {
            loader.classList.remove("d-none");
        }
        if (loaderOverlay) {
            loaderOverlay.classList.remove("d-none");
        }

        // Disable upload button to prevent multiple submissions
        uploadButton.disabled = true;
    });

    // Add event listener for file input change
    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            uploadButton.disabled = false; // Enable button when a file is selected
        } else {
            uploadButton.disabled = true; // Disable button if no file is selected
        }
    });

    // Toggle visibility of data table
    function toggleTable() {
        const tableDiv = document.getElementById("dataTable");
        if (tableDiv) {
            if (tableDiv.style.display === "none") {
                tableDiv.style.display = "block";
            } else {
                tableDiv.style.display = "none";
            }
        } else {
            console.warn("Data table element not found.");
        }
    }

    // Example usage of toggleTable
    document.getElementById("toggleTableButton")?.addEventListener("click", toggleTable);
});
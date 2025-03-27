document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadButton");
    const loader = document.querySelector(".loader");
    const loaderOverlay = document.querySelector(".loader-overlay");
    const supportedFiles = [
        'liked_posts.json', 
        'media.json', 
        'profile.json', 
        'saved_posts.json'
    ];

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

    // File validation function
    function validateFiles(files) {
        const invalidFiles = Array.from(files).filter(file => 
            !supportedFiles.includes(file.name)
        );

        if (invalidFiles.length > 0) {
            const invalidFileNames = invalidFiles.map(file => file.name).join(', ');
            alert(`Unsupported file(s): ${invalidFileNames}\n\nSupported files are: ${supportedFiles.join(', ')}`);
            fileInput.value = ''; // Clear the file input
            uploadButton.disabled = true;
            return false;
        }
        return true;
    }

    // Add event listener for form submission
    uploadForm.addEventListener("submit", function (event) {
        // Validate file input
        if (fileInput.files.length === 0) {
            alert("Please select a file before uploading.");
            event.preventDefault(); // Prevent form submission
            return;
        }

        // Additional file validation
        if (!validateFiles(fileInput.files)) {
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
            // Validate files before enabling upload
            if (validateFiles(fileInput.files)) {
                uploadButton.disabled = false; // Enable button when a valid file is selected
            }
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
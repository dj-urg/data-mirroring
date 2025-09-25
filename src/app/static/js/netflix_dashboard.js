// Netflix Dashboard JavaScript functionality
document.addEventListener("DOMContentLoaded", function () {
    // Elements
    const fileInput = document.getElementById("fileInput");
    const addFileButton = document.getElementById("addFileButton");
    const selectedFilesList = document.getElementById("selectedFilesList");
    const hiddenFileInputs = document.getElementById("hiddenFileInputs");
    const processButton = document.getElementById("processButton");
    const processDataForm = document.getElementById("processDataForm");
    const loader = document.querySelector(".loader");
    const loaderOverlay = document.querySelector(".loader-overlay");
    const visualizationDivs = document.querySelectorAll('#visualization, #month-heatmap, #day-heatmap, #time-heatmap');
    const body = document.body;
    let enlargedOverlay = null;

    // State management
    let filesAdded = 0;
    const selectedFiles = new Map(); // Map to store selected files by unique ID
    const supportedFiles = [
        'IndicatedPreferences.csv',
        'MyList.csv',
        'Ratings.csv',
        'SearchHistory.csv',
        'ViewingActivity.csv'
    ];

    // Initialize elements
    if (addFileButton) {
        addFileButton.disabled = true;
    }

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
    if (!fileInput) {
        console.warn("File input element not found. Skipping event listeners.");
        return;
    }

    // Event Handlers
    fileInput.addEventListener("change", function () {
        if (addFileButton) {
            addFileButton.disabled = fileInput.files.length === 0;
        }
    });

    if (addFileButton) {
        addFileButton.addEventListener("click", addSelectedFile);
    }

    if (processDataForm) {
        processDataForm.addEventListener("submit", function (event) {
            if (filesAdded === 0) {
                event.preventDefault();
                alert("Please add at least one file before processing data.");
                return;
            }

            if (loader) loader.classList.remove("d-none");
            if (loaderOverlay) loaderOverlay.classList.remove("d-none");
            if (processButton) processButton.disabled = true;
        });
    }

    // Functions
    function addSelectedFile() {
        // Validate file selection
        if (fileInput.files.length === 0) {
            return;
        }

        const file = fileInput.files[0];
        const fileId = generateUniqueId();
        const isSupported = supportedFiles.includes(file.name);

        // Add to selected files map
        selectedFiles.set(fileId, file);

        // Remove "no files" message if present
        const noFilesMessage = document.querySelector(".no-files-message");
        if (noFilesMessage) {
            noFilesMessage.remove();
        }

        // Create list item for file
        const listItem = document.createElement("li");
        listItem.setAttribute("data-file-id", fileId);
        listItem.className = "file-item";

        // File details
        const fileDetails = document.createElement("div");
        fileDetails.className = "file-details";

        const fileName = document.createElement("span");
        fileName.className = "file-name" + (isSupported ? "" : " unsupported");
        fileName.textContent = file.name;
        if (!isSupported) {
            fileName.title = "This file type may not be supported";
        }

        const fileSize = document.createElement("span");
        fileSize.className = "file-size";
        fileSize.textContent = formatFileSize(file.size);

        fileDetails.appendChild(fileName);
        fileDetails.appendChild(fileSize);

        // Remove button
        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.className = "remove-file-button";
        removeButton.textContent = "×";
        removeButton.setAttribute("aria-label", "Remove file");
        removeButton.addEventListener("click", function () {
            removeFile(fileId);
        });

        // Add elements to list item
        listItem.appendChild(fileDetails);
        listItem.appendChild(removeButton);

        // Add to visual list
        if (selectedFilesList) {
            selectedFilesList.appendChild(listItem);
        }

        // Create hidden file input for form submission
        createHiddenFileInput(fileId, file);

        // Update state
        filesAdded++;
        if (processButton) {
            processButton.disabled = filesAdded === 0;
        }

        // Reset file input for next selection
        fileInput.value = "";
        if (addFileButton) {
            addFileButton.disabled = true;
        }
    }

    function removeFile(fileId) {
        // Remove from DOM
        const listItem = document.querySelector(`li[data-file-id="${fileId}"]`);
        if (listItem) listItem.remove();

        // Remove hidden input
        const hiddenInput = document.querySelector(`input[data-file-id="${fileId}"]`);
        if (hiddenInput) hiddenInput.remove();

        // Remove from map
        selectedFiles.delete(fileId);

        // Update state
        filesAdded--;
        if (processButton) {
            processButton.disabled = filesAdded === 0;
        }

        // Show "no files" message if needed
        if (filesAdded === 0 && selectedFilesList) {
            const noFilesMessage = document.createElement("li");
            noFilesMessage.className = "no-files-message";
            noFilesMessage.textContent = "No files added yet";
            selectedFilesList.appendChild(noFilesMessage);
        }
    }

    function createHiddenFileInput(fileId, file) {
        if (!hiddenFileInputs) return;

        // Create a new file list object containing just this file
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);

        // Create hidden input
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "file";
        hiddenInput.name = "file"; // Name must match what your server expects
        hiddenInput.className = "d-none";
        hiddenInput.setAttribute("data-file-id", fileId);

        // Set files property with our file
        hiddenInput.files = dataTransfer.files;

        // Add to form
        hiddenFileInputs.appendChild(hiddenInput);
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function generateUniqueId() {
        return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Toggle visibility of data table - keeping this for backward compatibility
    window.toggleTable = function () {
        const tableDiv = document.getElementById("dataTable");
        if (tableDiv) {
            // Replace 'd-none' with your chosen class name if not using Bootstrap
            tableDiv.classList.toggle('d-none');
        } else {
            console.warn("Data table element not found.");
        }
    };

    // Image Enlargement Functionality
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
        enlargedOverlay.addEventListener('click', function(event) {
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

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add animation to cards when they come into view
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all cards
    document.querySelectorAll('.card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Handle download links
    document.querySelectorAll('a[href*="download"]').forEach(link => {
        link.addEventListener('click', function() {
            console.log('Download initiated:', this.href);
        });
    });

    // Add hover effects to visualization images
    document.querySelectorAll('img[alt*="Heatmap"], img[alt*="Genres"]').forEach(img => {
        img.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        img.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Handle responsive behavior
    function handleResize() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            if (window.innerWidth < 768) {
                card.classList.add('mobile-optimized');
            } else {
                card.classList.remove('mobile-optimized');
            }
        });
    }

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call
});
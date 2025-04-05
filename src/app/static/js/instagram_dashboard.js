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
    
    // State management
    let filesAdded = 0;
    const selectedFiles = new Map(); // Map to store selected files by unique ID
    const supportedFiles = [
        'liked_posts.json', 
        'media.json', 
        'profile.json', 
        'saved_posts.json',
        'videos_watched.json',
        'posts_viewed.json'
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
    fileInput.addEventListener("change", function() {
        if (addFileButton) {
            addFileButton.disabled = fileInput.files.length === 0;
        }
    });
    
    if (addFileButton) {
        addFileButton.addEventListener("click", addSelectedFile);
    }
    
    if (processDataForm) {
        processDataForm.addEventListener("submit", function(event) {
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
        removeButton.addEventListener("click", function() {
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
    window.toggleTable = function() {
        const tableDiv = document.getElementById("dataTable");
        if (tableDiv) {
            // Replace 'd-none' with your chosen class name if not using Bootstrap
            tableDiv.classList.toggle('d-none'); 
        } else {
            console.warn("Data table element not found.");
        }
    };
});
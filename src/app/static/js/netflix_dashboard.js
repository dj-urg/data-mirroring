/**
 * netflix_dashboard.js
 * 
 * Handles client-side processing of Netflix data exports.
 * 
 * CORE PRINCIPLE: NO DATA UPLOAD.
 * All processing (unzipping, parsing, filtering, rendering) happens in the browser's memory.
 * No network requests are made with the user's data.
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const zipInput = document.getElementById('zip-input');
    const folderInput = document.getElementById('folder-input');
    const profileSelect = document.getElementById('profile-select');
    const searchInput = document.getElementById('search-input');
    const downloadBtn = document.getElementById('download-btn');
    const downloadBtnText = downloadBtn.querySelector('i').nextSibling; // Text node after icon

    const errorMsg = document.getElementById('error-message');
    const successMsg = document.getElementById('success-message');
    const loadingSpinner = document.getElementById('loading-spinner');
    const dataContainer = document.getElementById('data-container');

    const summaryCount = document.getElementById('summary-count');
    const summaryDates = document.getElementById('summary-dates');
    const tableHead = document.querySelector('#viewing-activity-table thead tr');
    const tableBody = document.querySelector('#viewing-activity-table tbody');

    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');

    // --- State ---
    let allRows = [];
    let filteredRows = [];
    let headers = [];
    let currentProfile = '';
    let currentPage = 1;
    const PAGE_SIZE = 50;
    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

    // --- Event Listeners ---
    zipInput.addEventListener('change', handleZipUpload);
    folderInput.addEventListener('change', handleFolderUpload);
    profileSelect.addEventListener('change', handleProfileChange);
    searchInput.addEventListener('input', handleSearch);
    downloadBtn.addEventListener('click', handleDownload);
    prevPageBtn.addEventListener('click', () => changePage(-1));
    nextPageBtn.addEventListener('click', () => changePage(1));

    // --- File Handling Functions ---

    /**
     * Handle ZIP file upload using JSZip.
     */
    async function handleZipUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > MAX_FILE_SIZE) {
            showError(`File is too large. Maximum size is 50MB. (Selected: ${(file.size / 1024 / 1024).toFixed(2)}MB)`);
            e.target.value = ''; // Clear input
            return;
        }

        resetState();
        showLoading(true);

        try {
            const zip = new JSZip();
            const contents = await zip.loadAsync(file);

            // Find ViewingActivity.csv (case insensitive search)
            let csvFile = null;
            zip.forEach((relativePath, zipEntry) => {
                if (relativePath.toLowerCase().endsWith('viewingactivity.csv')) {
                    csvFile = zipEntry;
                }
            });

            if (!csvFile) {
                throw new Error("Could not find 'ViewingActivity.csv' inside the ZIP file.");
            }

            const csvText = await csvFile.async("string");
            processCsvData(csvText);

        } catch (err) {
            showError(err.message || "Failed to process ZIP file.");
            showLoading(false);
        } finally {
            // Clear input so same file can be selected again if needed
            zipInput.value = '';
        }
    }

    /**
     * Handle Folder upload (webkitdirectory).
     */
    function handleFolderUpload(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        resetState();
        showLoading(true);

        // Find ViewingActivity.csv
        const csvFile = files.find(f => f.name === 'ViewingActivity.csv');

        if (!csvFile) {
            showError("Could not find 'ViewingActivity.csv' in the selected folder.");
            showLoading(false);
            folderInput.value = '';
            return;
        }

        if (csvFile.size > MAX_FILE_SIZE) {
            showError(`File is too large. Maximum size is 50MB. (Selected: ${(csvFile.size / 1024 / 1024).toFixed(2)}MB)`);
            folderInput.value = '';
            showLoading(false);
            return;
        }

        const reader = new FileReader();
        reader.onload = function (event) {
            const csvText = event.target.result;
            processCsvData(csvText);
        };
        reader.onerror = function () {
            showError("Error reading the file.");
            showLoading(false);
        };
        reader.readAsText(csvFile);

        folderInput.value = '';
    }

    /**
     * Parse CSV text using PapaParse and update state.
     */
    function processCsvData(csvText) {
        Papa.parse(csvText, {
            header: true,
            skipEmptyLines: true,
            complete: function (results) {
                // Log errors if any
                if (results.errors.length > 0) {
                    console.warn("CSV Parsing Errors:", results.errors);
                }

                if (results.data.length === 0) {
                    if (results.errors.length > 0) {
                        showError("Failed to parse CSV file: " + results.errors[0].message);
                    } else {
                        showError("The CSV file appears to be empty.");
                    }
                    showLoading(false);
                    return;
                }

                allRows = results.data;
                headers = results.meta.fields;
                filteredRows = [...allRows];

                // Sort by Start Time descending if available
                if (headers.includes('Start Time')) {
                    filteredRows.sort((a, b) => {
                        const dateA = new Date(a['Start Time']);
                        const dateB = new Date(b['Start Time']);

                        // Handle invalid dates: push them to the end
                        if (isNaN(dateA) && isNaN(dateB)) return 0;
                        if (isNaN(dateA)) return 1;
                        if (isNaN(dateB)) return -1;

                        return dateB - dateA;
                    });
                    allRows = [...filteredRows]; // Update master list order too
                }

                let successMsgText = `Successfully loaded ${allRows.length} rows.`;
                if (results.errors.length > 0) {
                    successMsgText += ` Warning: ${results.errors.length} rows could not be parsed and were skipped.`;
                }
                showSuccess(successMsgText);
                downloadBtn.disabled = false;

                populateProfileSelect();
                updateFilters(); // Will handle summary and render
                showLoading(false);
                dataContainer.style.display = 'block';
            },
            error: function (err) {
                showError("CSV parsing error: " + err.message);
                showLoading(false);
            }
        });
    }

    // --- UI / Display Functions ---

    function resetState() {
        allRows = [];
        filteredRows = [];
        headers = [];
        currentPage = 1;
        profileSelect.innerHTML = '<option value="">All Profiles</option>';
        currentProfile = '';
        downloadBtn.disabled = true;
        dataContainer.style.display = 'none';
        errorMsg.style.display = 'none';
        successMsg.style.display = 'none';
        tableHead.innerHTML = '';
        tableBody.innerHTML = '';
    }

    function populateProfileSelect() {
        if (!headers.includes('Profile Name')) return;

        // Get unique profiles
        const profiles = [...new Set(allRows.map(row => row['Profile Name']).filter(p => p))].sort();

        profileSelect.innerHTML = '<option value="">All Profiles</option>';
        profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile;
            option.textContent = profile;
            profileSelect.appendChild(option);
        });
    }

    function showLoading(isLoading) {
        loadingSpinner.style.display = isLoading ? 'block' : 'none';
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
        successMsg.style.display = 'none';
    }

    function showSuccess(msg) {
        successMsg.textContent = msg;
        successMsg.style.display = 'block';
        errorMsg.style.display = 'none';
    }

    function updateSummary() {
        summaryCount.textContent = filteredRows.length;

        if (headers.includes('Start Time') && filteredRows.length > 0) {
            // Filter valid dates for summary
            const validDates = filteredRows
                .map(row => new Date(row['Start Time']))
                .filter(d => !isNaN(d));

            if (validDates.length > 0) {
                // Since mixed valid/invalid might be interspersed if we just blindly take first/last
                // let's rely on finding min/max from the valid list
                // However, if we sorted correctly, valid ones are at start?
                // Our sort puts INVALID at end. So valid dates are 0 to N.
                // But wait, sort is DESCENDING (newest first).
                // So dateB - dateA.

                // Newest is at index 0. Oldest valid is at index validDates.length - 1?
                // Let's re-calculate to be safe from sort issues.

                // Use reduce to avoid Maximum call stack size exceeded with spread operator on large arrays
                const maxTimestamp = validDates.reduce((max, d) => Math.max(max, d.getTime()), 0);
                const minTimestamp = validDates.reduce((min, d) => Math.min(min, d.getTime()), Infinity);

                const maxDate = new Date(maxTimestamp);
                const minDate = new Date(minTimestamp);

                const d1 = minDate.toISOString().split('T')[0];
                const d2 = maxDate.toISOString().split('T')[0];
                summaryDates.textContent = `${d1} - ${d2}`;
            } else {
                summaryDates.textContent = 'N/A';
            }
        } else {
            summaryDates.textContent = 'N/A';
        }
    }

    function renderTable() {
        // Headers
        if (tableHead.children.length === 0) {
            headers.forEach(h => {
                const th = document.createElement('th');
                th.textContent = h;
                tableHead.appendChild(th);
            });
        }

        // Body
        tableBody.innerHTML = '';
        const start = (currentPage - 1) * PAGE_SIZE;
        const end = start + PAGE_SIZE;
        const pageData = filteredRows.slice(start, end);

        pageData.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(h => {
                const td = document.createElement('td');
                td.textContent = row[h] || '';
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });

        // Pagination Controls
        pageInfo.textContent = `Page ${currentPage} of ${Math.ceil(filteredRows.length / PAGE_SIZE) || 1}`;
        prevPageBtn.disabled = currentPage <= 1;
        nextPageBtn.disabled = currentPage >= Math.ceil(filteredRows.length / PAGE_SIZE);
    }

    function changePage(delta) {
        const maxPage = Math.ceil(filteredRows.length / PAGE_SIZE);
        const newPage = currentPage + delta;
        if (newPage >= 1 && newPage <= maxPage) {
            currentPage = newPage;
            renderTable();
        }
    }

    function handleProfileChange(e) {
        currentProfile = e.target.value;
        updateFilters();
    }

    function handleSearch(e) {
        updateFilters();
    }

    function updateFilters() {
        const query = searchInput.value.toLowerCase();

        filteredRows = allRows.filter(row => {
            // Profile Filter
            if (currentProfile && row['Profile Name'] !== currentProfile) {
                return false;
            }

            // Search Filter
            if (query) {
                return headers.some(h => {
                    const val = row[h] ? row[h].toString().toLowerCase() : '';
                    return val.includes(query);
                });
            }

            return true;
        });

        currentPage = 1;
        updateDownloadButtonState();
        updateSummary();
        renderTable();
    }

    function updateDownloadButtonState() {
        if (!downloadBtnText) return;

        // Safe implementation: clear content, append icon, append escaped text
        downloadBtn.innerHTML = '';
        const icon = document.createElement('i');
        icon.className = 'fas fa-download';
        downloadBtn.appendChild(icon);

        let text = ' Download Full History';
        if (currentProfile) {
            text = ` Download ${currentProfile}'s History`;
        }

        downloadBtn.appendChild(document.createTextNode(text));
    }

    // --- Download Handling ---

    /**
     * Download the CURRENT data as ViewingActivity.csv.
     * Uses Blob + URL.createObjectURL.
     */
    function handleDownload() {
        if (!allRows || allRows.length === 0) return;

        // User requested to download history for the specific profile.
        // We filter based on the current profile selection, IGNORING the search query.
        // If "All Profiles" is selected, we download everything.

        let rowsToDownload = allRows;
        if (currentProfile) {
            rowsToDownload = allRows.filter(row => row['Profile Name'] === currentProfile);
        }

        const csvContent = Papa.unparse(rowsToDownload);

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.setAttribute('href', url);
        // Add profile name to filename if selected
        const filename = currentProfile ? `ViewingActivity_${currentProfile.replace(/[^a-z0-9]/gi, '_')}.csv` : 'ViewingActivity.csv';
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Revoke the Object URL to avoid memory leaks
        setTimeout(() => {
            URL.revokeObjectURL(url);
        }, 100);
    }
});

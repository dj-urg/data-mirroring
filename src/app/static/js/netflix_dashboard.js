/**
 * netflix_local_viewing.js
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
    const searchInput = document.getElementById('search-input');
    const downloadBtn = document.getElementById('download-btn');

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
    let currentPage = 1;
    const PAGE_SIZE = 50;

    // --- Event Listeners ---
    zipInput.addEventListener('change', handleZipUpload);
    folderInput.addEventListener('change', handleFolderUpload);
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
                if (results.errors.length > 0 && results.data.length === 0) {
                    showError("Failed to parse CSV file: " + results.errors[0].message);
                    showLoading(false);
                    return;
                }

                if (results.data.length === 0) {
                    showError("The CSV file appears to be empty.");
                    showLoading(false);
                    return;
                }

                allRows = results.data;
                headers = results.meta.fields;
                filteredRows = [...allRows];

                // Sort by Start Time descending if available
                if (headers.includes('Start Time')) {
                    filteredRows.sort((a, b) => new Date(b['Start Time']) - new Date(a['Start Time']));
                    allRows = [...filteredRows]; // Update master list order too
                }

                showSuccess(`Successfully loaded ${allRows.length} rows.`);
                downloadBtn.disabled = false;

                updateSummary();
                renderTable();
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
        downloadBtn.disabled = true;
        dataContainer.style.display = 'none';
        errorMsg.style.display = 'none';
        successMsg.style.display = 'none';
        tableHead.innerHTML = '';
        tableBody.innerHTML = '';
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
            // Find min/max dates. Assuming sorted descending already.
            // But let's scan to be safe or use the first/last if sorted.
            // Since we sorted by Start Time desc:
            const newest = filteredRows[0]['Start Time'];
            const oldest = filteredRows[filteredRows.length - 1]['Start Time'];

            // Basic formatting
            const d1 = new Date(oldest).toLocaleDateString();
            const d2 = new Date(newest).toLocaleDateString();
            summaryDates.textContent = `${d1} - ${d2}`;
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

    function handleSearch(e) {
        const query = e.target.value.toLowerCase();

        if (!query) {
            filteredRows = [...allRows];
        } else {
            // Simple search across all fields
            filteredRows = allRows.filter(row => {
                return headers.some(h => {
                    const val = row[h] ? row[h].toString().toLowerCase() : '';
                    return val.includes(query);
                });
            });
        }

        currentPage = 1;
        updateSummary();
        renderTable();
    }

    // --- Download Handling ---

    /**
     * Download the CURRENT data as ViewingActivity.csv.
     * Uses Blob + URL.createObjectURL.
     */
    function handleDownload() {
        if (!allRows || allRows.length === 0) return;

        // Convert back to CSV
        // We use the original allRows to let user download the valid dataset they uploaded
        // (Is it better to download filtered? User request says "download extracted... contents")
        // "Trigger a download of the exact ViewingActivity.csv content"
        const csvContent = Papa.unparse(allRows);

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'ViewingActivity.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

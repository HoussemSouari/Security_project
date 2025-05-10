/**
 * ReconScraper - Modern UI Interactions
 * Enhances the user experience with animations and dynamic behaviors
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded");
    
    // Initialize global arrays if they don't exist
    window.keywords = window.keywords || [];
    window.downloadFiles = window.downloadFiles || { json: '', csv: '' };

    // Card section toggles
    const toggleButtons = document.querySelectorAll('.section-toggle');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const target = document.getElementById(targetId);
            const icon = this.querySelector('i');
            
            if (target.classList.contains('show')) {
                target.classList.remove('show');
                icon.classList.remove('bi-chevron-up');
                icon.classList.add('bi-chevron-down');
            } else {
                target.classList.add('show');
                icon.classList.remove('bi-chevron-down');
                icon.classList.add('bi-chevron-up');
            }
    });
    
    // Keyword functionality
    const addKeywordBtn = document.getElementById('addKeywordBtn');
    const keywordInput = document.getElementById('keywordInput');
    
    // Add a keyword when the Add button is clicked
    if (addKeywordBtn) {
        console.log("Setting up Add button click handler");
        addKeywordBtn.onclick = function() {
            console.log("Add button clicked");
            const keyword = keywordInput.value.trim();
            if (keyword && !window.keywords.includes(keyword)) {
                window.keywords.push(keyword);
                renderKeywords();
                keywordInput.value = '';
            }
        };
    }
    
    // Add a keyword when Enter is pressed in the input field
    if (keywordInput) {
        keywordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addKeywordBtn.click();
            }
        });
    }
    
    // Function to render keywords
    function renderKeywords() {
        const keywordsList = document.getElementById('keywordsList');
        if (!keywordsList) return;
        
        keywordsList.innerHTML = '';
        window.keywords.forEach((keyword, index) => {
            const pill = document.createElement('span');
            pill.className = 'keyword-pill';
            pill.innerHTML = `${keyword} <span class="remove-keyword" data-index="${index}">×</span>`;
            keywordsList.appendChild(pill);
        });
        
        // Attach event listeners to all remove buttons
        document.querySelectorAll('.remove-keyword').forEach(button => {
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                window.keywords.splice(index, 1);
                renderKeywords();
            });
        });
    }
    
    // Enhanced logging with timestamp
    function addLog(message) {
        const log = document.getElementById('scrapingLog');
        if (!log) return;
        
        const line = document.createElement('div');
        const now = new Date();
        const timestamp = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;
        line.innerHTML = `<span class="log-timestamp">${timestamp}</span> ${message}`;
        log.appendChild(line);
        log.scrollTop = log.scrollHeight;
    }
    window.addLog = addLog;
    
    // Apply hover effects to the result table rows
    const resultRows = document.querySelectorAll('#resultsTable tr');
    resultRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.classList.add('highlight');
        });
        row.addEventListener('mouseleave', function() {
            this.classList.remove('highlight');
        });
    });
    
    // Form submission handler
    const scraperForm = document.getElementById('scraperForm');
    if (scraperForm) {
        scraperForm.addEventListener('submit', function(e) {
            // Prevent default form submission
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                submitBtn.disabled = true;
            }
            
            // Get form values
            const url = document.getElementById('urlInput').value;
            const depth = document.getElementById('depthInput').value;
            const maxUrls = document.getElementById('maxUrlsInput').value;
            const ignoreRobots = document.getElementById('ignoreRobotsInput').checked;
            
            const errorMessageElement = document.getElementById('errorMessage');
            
            // Validate URL
            if (!url) {
                if (errorMessageElement) {
                    errorMessageElement.textContent = 'Please enter a target URL';
                    errorMessageElement.style.display = 'block';
                }
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="bi bi-search"></i> Start Reconnaissance';
                    submitBtn.disabled = false;
                }
                return;
            }
            
            // Reset interface
            if (errorMessageElement) {
                errorMessageElement.style.display = 'none';
            }
            
            document.getElementById('loadingIndicator').style.display = 'block';
            document.getElementById('resultsContainer').style.display = 'none';
            document.getElementById('scrapingLog').innerHTML = '<div>$ Initializing scraper...</div>';
            
            // Smooth scroll to terminal
            const loadingIndicator = document.getElementById('loadingIndicator');
            if (loadingIndicator) {
                setTimeout(() => {
                    loadingIndicator.scrollIntoView({ behavior: 'smooth' });
                }, 300);
            }
            
            // Add logs
            addLog(`Initialization of reconnaissance for ${url}`);
            addLog(`Configured keywords: ${window.keywords.join(', ') || 'None'}`);
            addLog(`Depth: ${depth}, Maximum URLs: ${maxUrls}`);
            addLog(`Ignore robots.txt: ${ignoreRobots}`);
            
            // Make API request
            fetch('/api/scrape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    keywords: window.keywords.join(','),
                    depth: parseInt(depth),
                    max_urls: parseInt(maxUrls),
                    ignore_robots: ignoreRobots
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    // Update download files
                    window.downloadFiles = data.files;
                    
                    // Update counters
                    document.getElementById('visitedUrlsCount').textContent = data.visitedUrls;
                    document.getElementById('resultsCount').textContent = data.results.length;
                    
                    // Success logs
                    addLog(`Reconnaissance completed successfully`);
                    addLog(`${data.visitedUrls} URLs visited`);
                    addLog(`${data.results.length} results found`);
                    if (data.log) {
                        addLog(data.log);
                    }
                    
                    // Fill the results table
                    const resultsTable = document.getElementById('resultsTable');
                    resultsTable.innerHTML = '';
                    
                    data.results.forEach(result => {
                        result.findings.forEach(finding => {
                            const row = document.createElement('tr');
                            
                            const urlCell = document.createElement('td');
                            const urlBadge = document.createElement('span');
                            urlBadge.className = 'url-badge';
                            urlBadge.title = result.url;
                            urlBadge.textContent = result.url;
                            urlCell.appendChild(urlBadge);
                            row.appendChild(urlCell);
                            
                            const titleCell = document.createElement('td');
                            titleCell.textContent = result.title;
                            row.appendChild(titleCell);
                            
                            const keywordCell = document.createElement('td');
                            keywordCell.textContent = finding.keyword;
                            row.appendChild(keywordCell);
                            
                            const occurrencesCell = document.createElement('td');
                            occurrencesCell.textContent = finding.occurrences;
                            row.appendChild(occurrencesCell);
                            
                            resultsTable.appendChild(row);
                        });
                    });
                    
                    // Display results
                    document.getElementById('loadingIndicator').style.display = 'none';
                    document.getElementById('resultsContainer').style.display = 'block';
                } else {
                    throw new Error(data.error || 'Error during the request');
                }
                
                // Reset button state
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="bi bi-search"></i> Start Reconnaissance';
                    submitBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const errorMessageElement = document.getElementById('errorMessage');
                if (errorMessageElement) {
                    errorMessageElement.textContent = `Error: ${error.message}. Check scraper.log for more details.`;
                    errorMessageElement.style.display = 'block';
                }
                addLog(`Error: ${error.message}`);
                document.getElementById('loadingIndicator').style.display = 'none';
                
                // Reset button state
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="bi bi-search"></i> Start Reconnaissance';
                    submitBtn.disabled = false;
                }
            });
        });
    }
    
    // Download button functionality
    const jsonDownloadBtn = document.getElementById('jsonDownloadBtn');
    const csvDownloadBtn = document.getElementById('csvDownloadBtn');
    
    if (jsonDownloadBtn) {
        jsonDownloadBtn.addEventListener('click', function() {
            if (window.downloadFiles && window.downloadFiles.json) {
                window.location.href = `/downloads/${window.downloadFiles.json}`;
            }
        });
    }
    
    if (csvDownloadBtn) {
        csvDownloadBtn.addEventListener('click', function() {
            if (window.downloadFiles && window.downloadFiles.csv) {
                window.location.href = `/downloads/${window.downloadFiles.csv}`;
            }
        });
    }
    
    // Render keywords on page load
    renderKeywords();
});
    
    // Enhanced logging with timestamp
    function addLog(message) {
        const log = document.getElementById('scrapingLog');
        if (!log) return;
        
        const line = document.createElement('div');
        const now = new Date();
        const timestamp = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;
        line.innerHTML = `<span class="log-timestamp">${timestamp}</span> ${message}`;
        log.appendChild(line);
        log.scrollTop = log.scrollHeight;
    }
    
    // Override the existing addLog function
    window.addLog = addLog;
    
    // Apply nice hover effects to the result table rows
    const resultRows = document.querySelectorAll('#resultsTable tr');
    resultRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.classList.add('highlight');
        });
        row.addEventListener('mouseleave', function() {
            this.classList.remove('highlight');
        });
    });    // Enhance form submission UI feedback
    const scraperForm = document.getElementById('scraperForm');
    if (scraperForm) {
        // Remove any existing listener to prevent duplicate submissions
        const clonedForm = scraperForm.cloneNode(true);
        scraperForm.parentNode.replaceChild(clonedForm, scraperForm);
        
        // Get the new form reference
        const newScraperForm = document.getElementById('scraperForm');
        
        newScraperForm.addEventListener('submit', function(e) {
            // Prevent the default form submission
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            
            // Add loading state to button
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                submitBtn.disabled = true;
            }            // Get form values
            const url = document.getElementById('urlInput').value;
            const depth = document.getElementById('depthInput').value;
            const maxUrls = document.getElementById('maxUrlsInput').value;
            const ignoreRobots = document.getElementById('ignoreRobotsInput').checked;
            
            // Access the global keywords variable
            const keywordsToSend = window.keywords || [];
            
            // Get the error message element
            const errorMessageElement = document.getElementById('errorMessage');
            
            if (!url) {
                if (errorMessageElement) {
                    errorMessageElement.textContent = 'Please enter a target URL';
                    errorMessageElement.style.display = 'block';
                }
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="bi bi-search"></i> Start Reconnaissance';
                    submitBtn.disabled = false;
                }
                return;
            }
              // Reset interface
            if (errorMessageElement) {
                errorMessageElement.style.display = 'none';
            }
            document.getElementById('loadingIndicator').style.display = 'block';
            document.getElementById('resultsContainer').style.display = 'none';
            document.getElementById('scrapingLog').innerHTML = '<div>$ Initializing scraper...</div>';
            
            // Smooth scroll to terminal
            const loadingIndicator = document.getElementById('loadingIndicator');
            if (loadingIndicator) {
                setTimeout(() => {
                    loadingIndicator.scrollIntoView({ behavior: 'smooth' });
                }, 300);
            }
              // Logs
            addLog(`Initialization of reconnaissance for ${url}`);
            addLog(`Configured keywords: ${keywordsToSend.join(', ') || 'None'}`);
            addLog(`Depth: ${depth}, Maximum URLs: ${maxUrls}`);
            addLog(`Ignore robots.txt: ${ignoreRobots}`);
            
            // Make the API request
            fetch('/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    keywords: keywordsToSend.join(','),
                    depth: parseInt(depth),
                    max_urls: parseInt(maxUrls),
                    ignore_robots: ignoreRobots
                })
            })
            .then(response => response.json())
            .then(data => {                if (!data.error) {
                    // Update download files
                    if (window.downloadFiles) {
                        window.downloadFiles = data.files;
                    }
                    
                    // Update counters
                    document.getElementById('visitedUrlsCount').textContent = data.visitedUrls;
                    document.getElementById('resultsCount').textContent = data.results.length;
                    
                    // Success logs
                    addLog(`Reconnaissance completed successfully`);
                    addLog(`${data.visitedUrls} URLs visited`);
                    addLog(`${data.results.length} results found`);
                    if (data.log) {
                        addLog(data.log);
                    }
                    
                    // Fill the results table
                    const resultsTable = document.getElementById('resultsTable');
                    resultsTable.innerHTML = '';
                    
                    data.results.forEach(result => {
                        result.findings.forEach(finding => {
                            const row = document.createElement('tr');
                            
                            const urlCell = document.createElement('td');
                            const urlBadge = document.createElement('span');
                            urlBadge.className = 'url-badge';
                            urlBadge.title = result.url;
                            urlBadge.textContent = result.url;
                            urlCell.appendChild(urlBadge);
                            row.appendChild(urlCell);
                            
                            const titleCell = document.createElement('td');
                            titleCell.textContent = result.title;
                            row.appendChild(titleCell);
                            
                            const keywordCell = document.createElement('td');
                            keywordCell.textContent = finding.keyword;
                            row.appendChild(keywordCell);
                            
                            const occurrencesCell = document.createElement('td');
                            occurrencesCell.textContent = finding.occurrences;
                            row.appendChild(occurrencesCell);
                            
                            resultsTable.appendChild(row);
                        });
                    });
                    
                    // Display results
                    document.getElementById('loadingIndicator').style.display = 'none';
                    document.getElementById('resultsContainer').style.display = 'block';
                } else {
                    throw new Error(data.error || 'Error during the request');
                }
                
                // Reset button state
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="bi bi-search"></i> Start Reconnaissance';
                    submitBtn.disabled = false;
                }
            })            .catch(error => {
                console.error('Error:', error);
                const errorMessageElement = document.getElementById('errorMessage');
                if (errorMessageElement) {
                    errorMessageElement.textContent = `Error: ${error.message}. Check scraper.log for more details.`;
                    errorMessageElement.style.display = 'block';
                }
                addLog(`Error: ${error.message}`);
                document.getElementById('loadingIndicator').style.display = 'none';
                
                // Reset button state
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="bi bi-search"></i> Start Reconnaissance';
                    submitBtn.disabled = false;
                }
            });
        });
    }
    
    // Make the file cards interactive
    const fileCards = document.querySelectorAll('.file-card');
    fileCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('file-hover');
        });
        card.addEventListener('mouseleave', function() {
            this.classList.remove('file-hover');
        });
    });
});

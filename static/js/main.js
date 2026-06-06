document.addEventListener('DOMContentLoaded', function() {
    // 1. File Upload styling and input update
    const fileInput = document.getElementById('log_file');
    const uploadZone = document.getElementById('upload-zone');
    
    if (fileInput && uploadZone) {
        // Trigger file select on click
        uploadZone.addEventListener('click', () => fileInput.click());

        // Update display on file select
        fileInput.addEventListener('change', function(e) {
            if (this.files && this.files.length > 0) {
                const filename = this.files[0].name;
                const sizeKB = (this.files[0].size / 1024).toFixed(1);
                
                uploadZone.innerHTML = `
                    <i class="bi bi-file-earmark-text-fill upload-icon text-primary"></i>
                    <h4>${filename}</h4>
                    <p class="text-secondary small">${sizeKB} KB - Click to replace file</p>
                `;
            }
        });

        // Drag & drop handlers
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = '#3b82f6';
                uploadZone.style.background = 'rgba(59, 130, 246, 0.08)';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                uploadZone.style.background = 'rgba(255, 255, 255, 0.02)';
            }, false);
        });

        uploadZone.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                fileInput.files = files;
                // Dispatch change event to update text
                const event = new Event('change');
                fileInput.dispatchEvent(event);
            }
        });
    }

    // 2. Loading State Overlay for Analysis Action
    const analyzeBtn = document.getElementById('start-analysis-btn');
    const analyzeOverlay = document.getElementById('analysis-loading-overlay');
    
    if (analyzeBtn && analyzeOverlay) {
        analyzeBtn.addEventListener('click', function(e) {
            analyzeOverlay.classList.remove('d-none');
            
            // Cycle through agent loading messages to look realistic
            const statusText = document.getElementById('loading-status-text');
            const statuses = [
                "Agent 1: Fetching failed pipeline logs...",
                "Agent 1: Extracting error messages and stack traces...",
                "Agent 2: Contacting GitHub REST API...",
                "Agent 2: Analysing recent commits and diff changes...",
                "Agent 2: Correlating code changes with log errors...",
                "Agent 3: Loading historical successful logs...",
                "Agent 3: Generating final Root Cause report...",
                "Agent 3: Formulating retry & resolution steps..."
            ];
            
            let idx = 0;
            const interval = setInterval(() => {
                if (idx < statuses.length - 1) {
                    idx++;
                    if (statusText) {
                        statusText.textContent = statuses[idx];
                    }
                } else {
                    clearInterval(interval);
                }
            }, 3000);
        });
    }

    // 3. Highlight Diffs in page if present
    const diffBlocks = document.querySelectorAll('.raw-diff');
    diffBlocks.forEach(block => {
        const text = block.textContent;
        const lines = text.split('\n');
        let htmlLines = '';
        
        lines.forEach(line => {
            if (line.startsWith('+') && !line.startsWith('+++')) {
                htmlLines += `<span class="diff-line-added">${escapeHTML(line)}</span>`;
            } else if (line.startsWith('-') && !line.startsWith('---')) {
                htmlLines += `<span class="diff-line-removed">${escapeHTML(line)}</span>`;
            } else {
                htmlLines += `<span>${escapeHTML(line)}</span>\n`;
            }
        });
        block.innerHTML = htmlLines;
    });
});

function escapeHTML(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

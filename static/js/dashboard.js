// Global state
window.dashboardState = window.dashboardState || {
    uploadedReports: {
        sonarqube: false,
        sbom: false,
        trivy: false
    }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    setupFileUploads();
    
    // Detect project ID from upload cards
    const uploadCard = document.querySelector('.upload-card');
    const projectId = uploadCard ? uploadCard.dataset.projectId : null;
    
    loadSummaryData(projectId);
    
    // Set up periodic refresh of summary data
    if (projectId) {
        setInterval(() => loadSummaryData(projectId), 5000);
    }
});

// Setup file upload handlers
function setupFileUploads() {
    const uploadCards = document.querySelectorAll('.upload-card');
    
    uploadCards.forEach(card => {
        const fileInput = card.querySelector('.file-input');
        const uploadButton = card.querySelector('.upload-button');
        const reportType = card.dataset.reportType;
        const projectId = card.dataset.projectId;
        
        // Handle card click
        card.addEventListener('click', () => {
            if (!window.dashboardState.uploadedReports[reportType]) {
                fileInput.click();
            }
        });
        
        // Handle button click
        uploadButton.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });
        
        // Handle file selection
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                uploadFile(file, reportType, card, projectId);
            }
        });
    });
}

// Upload file function
async function uploadFile(file, reportType, card, projectId) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('report_type', reportType);
    
    // Show loading state
    showUploadLoading(card, true);
    
    try {
        const uploadUrl = projectId ? `/project/${projectId}/upload` : '/upload';
        const response = await fetch(uploadUrl, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Mark as uploaded
            window.dashboardState.uploadedReports[reportType] = true;
            updateUploadCard(card, true, file.name);
            
            // Show success message
            if (window.notificationManager) {
                window.notificationManager.success(result.message);
            }
            
            // Refresh summary data
            await loadSummaryData(projectId);
        } else {
            if (window.notificationManager) {
                window.notificationManager.error(result.error || 'Upload failed');
            }
        }
    } catch (error) {
        console.error('Upload error:', error);
        if (window.notificationManager) {
            window.notificationManager.error('Upload failed. Please try again.');
        }
    } finally {
        showUploadLoading(card, false);
    }
}

// Update upload card appearance
function updateUploadCard(card, uploaded, filename = '') {
    const icon = card.querySelector('.upload-icon');
    const title = card.querySelector('.upload-title');
    const description = card.querySelector('.upload-description');
    const button = card.querySelector('.upload-button');
    
    if (uploaded) {
        card.classList.add('uploaded');
        icon.innerHTML = '✓';
        icon.style.color = 'hsl(var(--low))';
        description.textContent = `Uploaded: ${filename}`;
        button.textContent = 'Uploaded';
        button.disabled = true;
        button.style.backgroundColor = 'hsl(var(--low))';
    }
}

// Show upload loading state
function showUploadLoading(card, loading) {
    const button = card.querySelector('.upload-button');
    const originalText = button.textContent;
    
    if (loading) {
        button.innerHTML = '<span class="loading-spinner"></span>Uploading...';
        button.disabled = true;
    } else {
        button.textContent = originalText;
        button.disabled = false;
    }
}

// Load summary data
async function loadSummaryData(projectId) {
    if (!projectId) {
        console.log('No project ID available for summary data loading');
        return;
    }
    
    try {
        const summaryUrl = `/project/${projectId}/api/summary`;
        const response = await fetch(summaryUrl);
        
        if (!response.ok) {
            console.log(`Summary API returned ${response.status}`);
            return;
        }
        
        const data = await response.json();
        
        updateSonarQubeSummary(data.sonarqube);
        updateSBOMSummary(data.sbom);
        updateTrivySummary(data.trivy);
        
    } catch (error) {
        console.error('Error loading summary data:', error);
    }
}

// Update SonarQube summary
function updateSonarQubeSummary(data) {
    const card = document.getElementById('sonarqube-summary');
    const detailButton = card.querySelector('.detail-button');
    
    if (!data) {
        card.classList.add('disabled');
        detailButton.style.display = 'none';
        showEmptyState(card, 'sonarqube');
        return;
    }
    
    card.classList.remove('disabled');
    detailButton.style.display = 'inline-block';
    
    // Update metrics
    updateMetric(card, 'bugs', data.bugs);
    updateMetric(card, 'vulnerabilities', data.vulnerabilities);
    updateMetric(card, 'code-smells', data.code_smells);
    updateMetric(card, 'coverage', data.coverage + '%');
    updateMetric(card, 'duplicated-lines', data.duplicated_lines_density + '%');
    
    // Update project info
    const projectName = card.querySelector('.project-name');
    if (projectName) {
        projectName.textContent = data.project_name;
    }
}

// Update SBOM summary
function updateSBOMSummary(data) {
    const card = document.getElementById('sbom-summary');
    const detailButton = card.querySelector('.detail-button');
    
    if (!data) {
        card.classList.add('disabled');
        detailButton.style.display = 'none';
        showEmptyState(card, 'sbom');
        return;
    }
    
    card.classList.remove('disabled');
    detailButton.style.display = 'inline-block';
    
    const vulnerabilities = data.vulnerabilities.by_severity;
    
    // Update vulnerability counts
    updateMetric(card, 'critical', vulnerabilities.critical, 'severity-critical');
    updateMetric(card, 'high', vulnerabilities.high, 'severity-high');
    updateMetric(card, 'medium', vulnerabilities.medium, 'severity-medium');
    updateMetric(card, 'low', vulnerabilities.low, 'severity-low');
    
    // Update total components
    updateMetric(card, 'total-components', data.components.total);
    
    // Create chart if canvas exists
    createSBOMChart(vulnerabilities);
}

// Update Trivy summary
function updateTrivySummary(data) {
    const card = document.getElementById('trivy-summary');
    const detailButton = card.querySelector('.detail-button');
    
    if (!data) {
        card.classList.add('disabled');
        detailButton.style.display = 'none';
        showEmptyState(card, 'trivy');
        return;
    }
    
    card.classList.remove('disabled');
    detailButton.style.display = 'inline-block';
    
    const vulnerabilities = data.vulnerabilities.by_severity;
    
    // Update vulnerability counts
    updateMetric(card, 'critical', vulnerabilities.CRITICAL, 'severity-critical');
    updateMetric(card, 'high', vulnerabilities.HIGH, 'severity-high');
    updateMetric(card, 'medium', vulnerabilities.MEDIUM, 'severity-medium');
    updateMetric(card, 'low', vulnerabilities.LOW, 'severity-low');
    updateMetric(card, 'unknown', vulnerabilities.UNKNOWN, 'severity-unknown');
    
    // Update artifact info
    const artifactName = card.querySelector('.artifact-name');
    if (artifactName) {
        artifactName.textContent = data.artifact_name;
    }
    
    // Create chart if canvas exists
    createTrivyChart(vulnerabilities);
}

// Update metric helper
function updateMetric(card, metricName, value, cssClass = '') {
    const metricElement = card.querySelector(`[data-metric="${metricName}"]`);
    if (metricElement) {
        metricElement.textContent = value;
        if (cssClass) {
            metricElement.className = `metric-value ${cssClass}`;
        }
    }
}

// Show empty state
function showEmptyState(card, type) {
    const metricsGrid = card.querySelector('.metrics-grid');
    const chartContainer = card.querySelector('.chart-container');
    
    if (metricsGrid) {
        metricsGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-text">No ${type.toUpperCase()} data</div>
                <div class="empty-state-subtext">Upload a ${type} report to see metrics</div>
            </div>
        `;
    }
    
    if (chartContainer) {
        chartContainer.innerHTML = '';
    }
}

// Create SBOM chart
function createSBOMChart(data) {
    const canvas = document.getElementById('sbom-chart');
    if (!canvas || !window.Chart) {
        console.log('SBOM chart canvas not found or Chart.js not loaded');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.log('Unable to get canvas context for SBOM chart');
        return;
    }
    
    // Destroy existing chart
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    // For SBOM, show component types or vulnerability severity if available
    let chartData, labels;
    if (data && typeof data === 'object') {
        if (data.critical !== undefined) {
            // Vulnerability data format
            labels = ['Critical', 'High', 'Medium', 'Low'];
            chartData = [data.critical || 0, data.high || 0, data.medium || 0, data.low || 0];
        } else {
            // Component types or other data
            labels = Object.keys(data);
            chartData = Object.values(data);
        }
    } else {
        // Default empty state
        labels = ['No Data'];
        chartData = [1];
    }
    
    const chartConfig = {
        labels: labels,
        datasets: [{
            data: chartData,
            backgroundColor: [
                '#dc3545',
                '#fd7e14',
                '#ffc107',
                '#20c997'
            ],
            borderWidth: 0
        }]
    };
    
    canvas.chart = new Chart(ctx, {
        type: 'doughnut',
        data: chartConfig,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Create Trivy chart
function createTrivyChart(vulnerabilities) {
    const canvas = document.getElementById('trivy-chart');
    if (!canvas || !window.Chart) {
        console.log('Trivy chart canvas not found or Chart.js not loaded');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.log('Unable to get canvas context for Trivy chart');
        return;
    }
    
    // Destroy existing chart
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    const data = {
        labels: ['Critical', 'High', 'Medium', 'Low', 'Unknown'],
        datasets: [{
            data: [
                vulnerabilities.CRITICAL || 0,
                vulnerabilities.HIGH || 0,
                vulnerabilities.MEDIUM || 0,
                vulnerabilities.LOW || 0,
                vulnerabilities.UNKNOWN || 0
            ],
            backgroundColor: [
                '#dc3545',
                '#fd7e14',
                '#ffc107',
                '#20c997',
                '#6c757d'
            ],
            borderWidth: 0
        }]
    };
    
    canvas.chart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Use notification manager if available
function showNotification(type, message) {
    if (window.notificationManager) {
        if (type === 'success') {
            window.notificationManager.success(message);
        } else if (type === 'warning') {
            window.notificationManager.warning(message);
        } else {
            window.notificationManager.error(message);
        }
    }
}

// Detail page functions
function filterTable(tableId, filterValue, columnIndex) {
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    for (let row of rows) {
        const cell = row.cells[columnIndex];
        if (cell) {
            const cellText = cell.textContent.toLowerCase();
            if (filterValue === '' || cellText.includes(filterValue.toLowerCase())) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    }
}

function sortTable(tableId, columnIndex, isNumeric = false) {
    const table = document.getElementById(tableId);
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        if (isNumeric) {
            return parseFloat(aText) - parseFloat(bText);
        } else {
            return aText.localeCompare(bText);
        }
    });
    
    // Clear tbody and re-append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Export functions
function exportToPDF() {
    window.print();
}

function exportToJSON() {
    // This would need to be implemented based on the specific data structure
    console.log('Export to JSON functionality would be implemented here');
}

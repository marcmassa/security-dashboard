/**
 * Security Risk Heatmap - Interactive Threat Visualization
 * Real-time security risk monitoring and visualization
 */

class SecurityHeatmap {
    constructor() {
        this.realTimeMode = false;
        this.updateInterval = null;
        this.currentData = null;
        this.riskScoreChart = null;
        this.selectedProject = null;
        
        this.init();
    }

    init() {
        this.loadInitialData();
        this.setupEventListeners();
        this.initializeCharts();
        
        // Auto-refresh every 30 seconds when real-time is enabled
        this.setupAutoRefresh();
    }

    setupEventListeners() {
        // Filter change listeners are already set in HTML onchange attributes
        
        // Click handlers for heatmap cells
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('heatmap-cell')) {
                this.showRiskDetails(e.target.dataset);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshHeatmap();
            }
        });
    }

    async loadInitialData() {
        try {
            const response = await fetch('/api/security-heatmap/data');
            const data = await response.json();
            
            if (data.success) {
                this.currentData = data.data;
                this.renderHeatmap();
                this.updateStatistics();
                this.updateProjectTable();
                this.generateInsights();
            } else {
                this.showError('Failed to load heatmap data');
            }
        } catch (error) {
            console.error('Error loading heatmap data:', error);
            this.showError('Network error loading data');
        }
    }

    renderHeatmap() {
        const container = document.getElementById('heatmap-grid');
        const viewMode = document.getElementById('viewMode').value;
        
        switch (viewMode) {
            case 'grid':
                this.renderGridView(container);
                break;
            case 'tree':
                this.renderTreeMap(container);
                break;
            case 'bubble':
                this.renderBubbleChart(container);
                break;
        }
    }

    renderGridView(container) {
        if (!this.currentData) return;
        
        const projects = this.currentData.projects || [];
        const categories = ['vulnerabilities', 'code_quality', 'dependencies', 'containers'];
        
        let html = '<div class="heatmap-grid">';
        
        // Header row
        html += '<div class="heatmap-row header">';
        html += '<div class="heatmap-cell header">Project</div>';
        categories.forEach(category => {
            html += `<div class="heatmap-cell header">${this.formatCategoryName(category)}</div>`;
        });
        html += '<div class="heatmap-cell header">Overall</div>';
        html += '</div>';
        
        // Data rows
        projects.forEach(project => {
            html += '<div class="heatmap-row">';
            html += `<div class="heatmap-cell project-name">${project.name}</div>`;
            
            categories.forEach(category => {
                const riskScore = project.risks[category] || 0;
                const riskLevel = this.getRiskLevel(riskScore);
                const riskClass = this.getRiskClass(riskLevel);
                
                html += `<div class="heatmap-cell risk-cell ${riskClass}" 
                              data-project="${project.name}" 
                              data-category="${category}"
                              data-score="${riskScore}"
                              data-level="${riskLevel}"
                              title="${project.name} - ${this.formatCategoryName(category)}: ${riskScore}/10">
                              <span class="risk-score">${riskScore}</span>
                         </div>`;
            });
            
            // Overall risk score
            const overallRisk = this.calculateOverallRisk(project.risks);
            const overallLevel = this.getRiskLevel(overallRisk);
            const overallClass = this.getRiskClass(overallLevel);
            
            html += `<div class="heatmap-cell overall-risk ${overallClass}">
                          <span class="risk-score">${overallRisk}</span>
                     </div>`;
            html += '</div>';
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    renderTreeMap(container) {
        // Create a D3.js treemap visualization
        container.innerHTML = '<div class="treemap-container"><canvas id="treemap-canvas"></canvas></div>';
        
        if (!this.currentData) return;
        
        const canvas = document.getElementById('treemap-canvas');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        canvas.width = container.offsetWidth;
        canvas.height = 400;
        
        // Simple treemap implementation
        const projects = this.currentData.projects || [];
        this.drawTreeMap(ctx, projects, canvas.width, canvas.height);
    }

    renderBubbleChart(container) {
        container.innerHTML = '<div class="bubble-container"><canvas id="bubble-canvas"></canvas></div>';
        
        if (!this.currentData) return;
        
        const canvas = document.getElementById('bubble-canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = container.offsetWidth;
        canvas.height = 400;
        
        const projects = this.currentData.projects || [];
        this.drawBubbleChart(ctx, projects, canvas.width, canvas.height);
    }

    drawTreeMap(ctx, projects, width, height) {
        const cellWidth = width / Math.ceil(Math.sqrt(projects.length));
        const cellHeight = height / Math.ceil(projects.length / Math.ceil(Math.sqrt(projects.length)));
        
        projects.forEach((project, index) => {
            const row = Math.floor(index / Math.ceil(Math.sqrt(projects.length)));
            const col = index % Math.ceil(Math.sqrt(projects.length));
            
            const x = col * cellWidth;
            const y = row * cellHeight;
            
            const overallRisk = this.calculateOverallRisk(project.risks);
            const color = this.getRiskColor(overallRisk);
            
            ctx.fillStyle = color;
            ctx.fillRect(x, y, cellWidth - 2, cellHeight - 2);
            
            // Add text
            ctx.fillStyle = '#ffffff';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(project.name, x + cellWidth/2, y + cellHeight/2 - 10);
            ctx.fillText(overallRisk.toString(), x + cellWidth/2, y + cellHeight/2 + 10);
        });
    }

    drawBubbleChart(ctx, projects, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const maxRadius = Math.min(width, height) / 8;
        
        projects.forEach((project, index) => {
            const overallRisk = this.calculateOverallRisk(project.risks);
            const radius = (overallRisk / 10) * maxRadius + 10;
            
            // Position bubbles in a circle
            const angle = (index / projects.length) * 2 * Math.PI;
            const distance = Math.min(width, height) / 4;
            const x = centerX + Math.cos(angle) * distance;
            const y = centerY + Math.sin(angle) * distance;
            
            const color = this.getRiskColor(overallRisk);
            
            // Draw bubble
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Add text
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(project.name, x, y - 5);
            ctx.fillText(overallRisk.toString(), x, y + 8);
        });
    }

    updateStatistics() {
        if (!this.currentData) return;
        
        const stats = this.currentData.statistics || {};
        
        document.getElementById('critical-count').textContent = stats.critical || 0;
        document.getElementById('high-count').textContent = stats.high || 0;
        document.getElementById('medium-count').textContent = stats.medium || 0;
        document.getElementById('trend-score').textContent = stats.trendScore || 0;
        
        // Update change indicators
        document.getElementById('critical-change').textContent = this.formatChange(stats.criticalChange);
        document.getElementById('high-change').textContent = this.formatChange(stats.highChange);
        document.getElementById('medium-change').textContent = this.formatChange(stats.mediumChange);
        document.getElementById('trend-change').textContent = stats.trendDirection || 'Stable';
    }

    updateProjectTable() {
        if (!this.currentData) return;
        
        const tbody = document.getElementById('project-risk-tbody');
        const projects = this.currentData.projects || [];
        
        let html = '';
        projects.forEach(project => {
            const overallRisk = this.calculateOverallRisk(project.risks);
            const trendIcon = this.getTrendIcon(project.trend);
            
            html += `
                <tr class="project-row" data-project="${project.name}">
                    <td>
                        <div class="project-info">
                            <i data-feather="folder" class="me-2"></i>
                            ${project.name}
                        </div>
                    </td>
                    <td>
                        <div class="risk-score-cell">
                            <span class="risk-badge ${this.getRiskClass(this.getRiskLevel(overallRisk))}">${overallRisk}</span>
                        </div>
                    </td>
                    <td><span class="severity-count critical">${project.counts.critical || 0}</span></td>
                    <td><span class="severity-count high">${project.counts.high || 0}</span></td>
                    <td><span class="severity-count medium">${project.counts.medium || 0}</span></td>
                    <td><i data-feather="${trendIcon}" class="trend-icon ${project.trend}"></i></td>
                    <td><span class="last-updated">${this.formatDate(project.lastUpdated)}</span></td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        feather.replace();
    }

    generateInsights() {
        const insights = document.getElementById('risk-insights-content');
        
        if (!this.currentData) {
            insights.innerHTML = '<p class="text-muted">No data available for insights</p>';
            return;
        }
        
        const projects = this.currentData.projects || [];
        const highRiskProjects = projects.filter(p => this.calculateOverallRisk(p.risks) >= 7);
        const criticalIssues = this.currentData.statistics?.critical || 0;
        
        let html = '<div class="insights-list">';
        
        if (highRiskProjects.length > 0) {
            html += `
                <div class="insight-item critical">
                    <i data-feather="alert-triangle" class="insight-icon"></i>
                    <div class="insight-content">
                        <strong>High Risk Alert</strong>
                        <p>${highRiskProjects.length} project(s) require immediate attention</p>
                    </div>
                </div>
            `;
        }
        
        if (criticalIssues > 10) {
            html += `
                <div class="insight-item warning">
                    <i data-feather="trending-up" class="insight-icon"></i>
                    <div class="insight-content">
                        <strong>Rising Critical Issues</strong>
                        <p>Critical vulnerabilities increased by ${criticalIssues} this week</p>
                    </div>
                </div>
            `;
        }
        
        // Add pattern analysis
        const topCategory = this.getMostVulnerableCategory();
        if (topCategory) {
            html += `
                <div class="insight-item info">
                    <i data-feather="pie-chart" class="insight-icon"></i>
                    <div class="insight-content">
                        <strong>Risk Pattern</strong>
                        <p>${this.formatCategoryName(topCategory)} shows highest risk concentration</p>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        insights.innerHTML = html;
        feather.replace();
    }

    initializeCharts() {
        const ctx = document.getElementById('risk-timeline-chart');
        if (!ctx) return;
        
        this.riskScoreChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Critical',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }, {
                    label: 'High',
                    data: [],
                    borderColor: '#f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Medium',
                    data: [],
                    borderColor: '#eab308',
                    backgroundColor: 'rgba(234, 179, 8, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Risk Count'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
        
        this.loadTimelineData();
    }

    async loadTimelineData() {
        try {
            const response = await fetch('/api/security-heatmap/timeline');
            const data = await response.json();
            
            if (data.success && this.riskScoreChart) {
                this.riskScoreChart.data.labels = data.data.labels;
                this.riskScoreChart.data.datasets[0].data = data.data.critical;
                this.riskScoreChart.data.datasets[1].data = data.data.high;
                this.riskScoreChart.data.datasets[2].data = data.data.medium;
                this.riskScoreChart.update();
            }
        } catch (error) {
            console.error('Error loading timeline data:', error);
        }
    }

    setupAutoRefresh() {
        // Will be enabled when real-time mode is activated
    }

    // Utility functions
    formatCategoryName(category) {
        return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    getRiskLevel(score) {
        if (score >= 9) return 'critical';
        if (score >= 7) return 'high';
        if (score >= 4) return 'medium';
        if (score >= 1) return 'low';
        return 'none';
    }

    getRiskClass(level) {
        return `risk-${level}`;
    }

    getRiskColor(score) {
        if (score >= 9) return '#ef4444';
        if (score >= 7) return '#f97316';
        if (score >= 4) return '#eab308';
        if (score >= 1) return '#22c55e';
        return '#94a3b8';
    }

    calculateOverallRisk(risks) {
        const values = Object.values(risks);
        return Math.round(values.reduce((sum, val) => sum + val, 0) / values.length * 10) / 10;
    }

    formatChange(change) {
        if (!change) return '+0 from yesterday';
        const sign = change >= 0 ? '+' : '';
        return `${sign}${change} from yesterday`;
    }

    getTrendIcon(trend) {
        switch (trend) {
            case 'up': return 'trending-up';
            case 'down': return 'trending-down';
            default: return 'minus';
        }
    }

    formatDate(date) {
        if (!date) return 'Never';
        return new Date(date).toLocaleDateString();
    }

    getMostVulnerableCategory() {
        if (!this.currentData?.projects) return null;
        
        const categoryTotals = {};
        this.currentData.projects.forEach(project => {
            Object.entries(project.risks).forEach(([category, score]) => {
                categoryTotals[category] = (categoryTotals[category] || 0) + score;
            });
        });
        
        return Object.entries(categoryTotals).reduce((max, [cat, score]) => 
            score > (categoryTotals[max] || 0) ? cat : max, null);
    }

    showError(message) {
        const container = document.getElementById('heatmap-grid');
        container.innerHTML = `
            <div class="error-state">
                <i data-feather="alert-circle" class="error-icon"></i>
                <h6>Error Loading Data</h6>
                <p>${message}</p>
                <button class="btn btn-primary btn-sm" onclick="heatmap.loadInitialData()">Retry</button>
            </div>
        `;
        feather.replace();
    }

    showRiskDetails(data) {
        const modal = new bootstrap.Modal(document.getElementById('riskDetailModal'));
        const content = document.getElementById('risk-detail-content');
        
        content.innerHTML = `
            <div class="risk-detail-header">
                <h6>${data.project} - ${this.formatCategoryName(data.category)}</h6>
                <span class="risk-badge ${this.getRiskClass(data.level)}">${data.score}/10</span>
            </div>
            <div class="risk-detail-body">
                <p>Risk level: <strong>${data.level.toUpperCase()}</strong></p>
                <p>Loading detailed information...</p>
            </div>
        `;
        
        modal.show();
        
        // Load detailed data asynchronously
        this.loadRiskDetails(data.project, data.category);
    }

    async loadRiskDetails(project, category) {
        try {
            const response = await fetch(`/api/security-heatmap/details/${project}/${category}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateRiskDetailModal(data.data);
            }
        } catch (error) {
            console.error('Error loading risk details:', error);
        }
    }

    updateRiskDetailModal(details) {
        const content = document.getElementById('risk-detail-content');
        // Update with detailed information
        // Implementation depends on the specific data structure
    }
}

// Global functions called from HTML
function updateHeatmap() {
    heatmap.renderHeatmap();
}

function refreshHeatmap() {
    heatmap.loadInitialData();
}

function toggleRealTimeMode() {
    heatmap.realTimeMode = !heatmap.realTimeMode;
    const button = document.getElementById('realtime-toggle-text');
    const status = document.getElementById('realtime-status');
    
    if (heatmap.realTimeMode) {
        button.textContent = 'Disable Real-time';
        status.style.display = 'block';
        heatmap.updateInterval = setInterval(() => {
            heatmap.loadInitialData();
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }, 30000);
    } else {
        button.textContent = 'Enable Real-time';
        status.style.display = 'none';
        if (heatmap.updateInterval) {
            clearInterval(heatmap.updateInterval);
        }
    }
}

function exportHeatmapData() {
    if (!heatmap.currentData) return;
    
    const dataStr = JSON.stringify(heatmap.currentData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `security-heatmap-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function zoomTimeline(period) {
    document.querySelectorAll('.timeline-controls .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update timeline data for the selected period
    heatmap.loadTimelineData();
}

function sortTable(column) {
    // Implement table sorting functionality
    console.log('Sorting by:', column);
}

function createRiskTicket() {
    // Integration with ticketing system
    console.log('Creating risk ticket...');
}

// Initialize heatmap when page loads
let heatmap;
document.addEventListener('DOMContentLoaded', function() {
    heatmap = new SecurityHeatmap();
});
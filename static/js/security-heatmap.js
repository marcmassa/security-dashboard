/**
 * Security Risk Heatmap - Fixed Version
 * Unified table styling with proper visibility and chart rendering
 */

class SecurityHeatmap {
    constructor() {
        this.data = {
            projects: [
                { name: 'test-project', risks: { vulnerabilities: 0, code_quality: 0, dependencies: 0, containers: 0 }, counts: { critical: 2, high: 5, medium: 8 } },
                { name: 'testo', risks: { vulnerabilities: 0, code_quality: 0, dependencies: 0, containers: 0 }, counts: { critical: 1, high: 3, medium: 4 } }
            ]
        };
        this.chart = null;
    }

    init() {
        this.safeRender();
        this.safeCreateChart('24h');
    }

    safeRender() {
        this.safeRenderGrid();
        this.safeRenderTable();
        this.safeUpdateStats();
    }

    // Unified badge styling function
    getBadgeStyle(score, isCount = false) {
        if (isCount && score === 0) {
            return 'bg-light text-dark fs-6 px-2 py-1';
        }
        
        if (score >= 9) return 'bg-danger text-white fs-6 px-3 py-2';
        if (score >= 7) return 'bg-warning text-dark fs-6 px-3 py-2';
        if (score >= 4) return 'bg-info text-white fs-6 px-3 py-2';
        if (score >= 1) return 'bg-success text-white fs-6 px-3 py-2';
        return 'bg-secondary text-white fs-6 px-3 py-2';
    }

    // Unified row styling
    getRowStyle(overallRisk) {
        if (overallRisk >= 7) return 'table-danger';
        if (overallRisk >= 4) return 'table-warning';
        if (overallRisk >= 1) return 'table-info';
        return '';
    }

    safeRenderGrid() {
        const container = document.getElementById('heatmap-grid');
        if (!container) return;
        
        const categories = ['vulnerabilities', 'code_quality', 'dependencies', 'containers'];
        let html = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th class="fw-bold py-3">Project</th>`;
        
        categories.forEach(cat => {
            html += `<th class="text-center fw-bold py-3">${this.formatCategory(cat)}</th>`;
        });
        html += `<th class="text-center fw-bold py-3">Overall Risk</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        this.data.projects.forEach(project => {
            const overall = this.calcOverall(project.risks);
            const rowClass = this.getRowStyle(overall);
            
            html += `<tr class="${rowClass}">
                        <td class="fw-medium py-3">
                            <div class="d-flex align-items-center">
                                <i data-feather="folder" class="me-2 text-muted" style="width: 16px; height: 16px;"></i>
                                ${project.name}
                            </div>
                        </td>`;
            
            categories.forEach(cat => {
                const score = project.risks[cat] || 0;
                const badgeStyle = this.getBadgeStyle(score);
                
                html += `<td class="text-center py-3">
                            <span class="badge ${badgeStyle}" title="${this.formatCategory(cat)}: ${score}/10">
                                ${score}
                            </span>
                         </td>`;
            });
            
            const overallBadgeStyle = this.getBadgeStyle(overall).replace('fs-6 px-3 py-2', 'fs-5 px-4 py-2 fw-bold');
            
            html += `<td class="text-center py-3">
                        <span class="badge ${overallBadgeStyle}" title="Riesgo general: ${overall}/10">
                            ${overall}
                        </span>
                     </td>
                   </tr>`;
        });
        
        html += `</tbody></table></div>`;
        container.innerHTML = html;
        this.replaceFeatherIcons();
    }

    safeRenderTable() {
        const tbody = document.getElementById('project-risk-tbody');
        if (!tbody) return;
        
        let html = '';
        this.data.projects.forEach(project => {
            const overall = this.calcOverall(project.risks);
            const rowClass = this.getRowStyle(overall);
            
            const overallBadgeStyle = this.getBadgeStyle(overall).replace('fs-6 px-3 py-2', 'fs-6 px-3 py-2 fw-bold');
            const criticalBadgeStyle = this.getBadgeStyle(project.counts.critical, true);
            const highBadgeStyle = this.getBadgeStyle(project.counts.high, true);
            const mediumBadgeStyle = this.getBadgeStyle(project.counts.medium, true);
            
            html += `
                <tr class="${rowClass}">
                    <td class="fw-medium py-3">
                        <div class="d-flex align-items-center">
                            <i data-feather="folder" class="me-2 text-muted" style="width: 16px; height: 16px;"></i>
                            ${project.name}
                        </div>
                    </td>
                    <td class="text-center py-3">
                        <span class="badge ${overallBadgeStyle}">${overall}</span>
                    </td>
                    <td class="text-center py-3">
                        <span class="badge ${criticalBadgeStyle}" title="Críticos: ${project.counts.critical}">${project.counts.critical}</span>
                    </td>
                    <td class="text-center py-3">
                        <span class="badge ${highBadgeStyle}" title="Altos: ${project.counts.high}">${project.counts.high}</span>
                    </td>
                    <td class="text-center py-3">
                        <span class="badge ${mediumBadgeStyle}" title="Medios: ${project.counts.medium}">${project.counts.medium}</span>
                    </td>
                    <td class="text-center py-3">
                        <i data-feather="minus" class="text-muted" style="width: 16px; height: 16px;"></i>
                    </td>
                    <td class="text-muted small py-3">Hoy</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
        this.replaceFeatherIcons();
    }

    safeUpdateStats() {
        // Calculate totals from project data
        let totalCritical = 0, totalHigh = 0, totalMedium = 0;
        
        this.data.projects.forEach(project => {
            totalCritical += project.counts.critical || 0;
            totalHigh += project.counts.high || 0;
            totalMedium += project.counts.medium || 0;
        });
        
        const elements = [
            { id: 'critical-count', value: totalCritical.toString() },
            { id: 'high-count', value: totalHigh.toString() },
            { id: 'medium-count', value: totalMedium.toString() },
            { id: 'trend-score', value: '1.4' }
        ];
        
        elements.forEach(item => {
            const el = document.getElementById(item.id);
            if (el) el.textContent = item.value;
        });
    }

    safeCreateChart(period) {
        // Try multiple ways to find the canvas
        let ctx = document.getElementById('risk-timeline-chart');
        if (!ctx) {
            ctx = document.querySelector('#risk-timeline-chart');
        }
        if (!ctx) {
            ctx = document.querySelector('canvas');
        }
        
        if (!ctx) {
            console.warn('Chart canvas not found, attempting to create one');
            const chartContainer = document.querySelector('.summary-card [style*="height: 300px"]');
            if (chartContainer) {
                chartContainer.innerHTML = '<canvas id="risk-timeline-chart" width="400" height="300"></canvas>';
                ctx = document.getElementById('risk-timeline-chart');
            }
        }

        if (!ctx) {
            console.error('Unable to find or create chart canvas');
            return;
        }

        console.log('Chart canvas found:', ctx.id || 'unnamed canvas');

        if (this.chart) {
            try {
                this.chart.destroy();
            } catch (e) {}
            this.chart = null;
        }

        const data = {
            '6h': { labels: ['0h', '1h', '2h', '3h', '4h', '5h'], values: [1, 1.2, 0.8, 1.1, 0.9, 1.3] },
            '7d': { labels: ['L', 'M', 'X', 'J', 'V', 'S', 'D'], values: [1.5, 1.2, 1.8, 1.1, 1.6, 1.0, 1.3] },
            '24h': { labels: ['0h', '6h', '12h', '18h', '24h'], values: [1.2, 1.5, 1.8, 1.3, 1.1] }
        };

        const chartData = data[period] || data['24h'];

        // Wait for Chart.js to load if not available yet
        const createChart = () => {
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js not loaded yet, waiting...');
                setTimeout(createChart, 200);
                return;
            }

            try {
                this.chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: 'Riesgo',
                            data: chartData.values,
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.3,
                            fill: true,
                            pointBackgroundColor: '#ef4444',
                            pointBorderColor: '#ef4444',
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { 
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: 'rgba(0,0,0,0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff'
                            }
                        },
                        scales: { 
                            y: { 
                                beginAtZero: true, 
                                max: 3,
                                grid: { color: 'rgba(255,255,255,0.1)' },
                                ticks: { color: '#6b7280' }
                            },
                            x: { 
                                grid: { color: 'rgba(255,255,255,0.1)' },
                                ticks: { color: '#6b7280' }
                            }
                        }
                    }
                });
                console.log('Chart created successfully for period:', period);
            } catch (error) {
                console.error('Chart creation failed:', error);
                const container = ctx.parentElement;
                if (container) {
                    container.innerHTML = '<div class="alert alert-warning">Error al crear el gráfico</div>';
                }
            }
        };

        createChart();
    }

    replaceFeatherIcons() {
        if (typeof feather !== 'undefined' && feather.replace) {
            setTimeout(() => {
                try {
                    feather.replace();
                } catch (e) {}
            }, 50);
        }
    }

    calcOverall(risks) {
        const values = Object.values(risks || {});
        return values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : 0;
    }

    formatCategory(cat) {
        const categoryNames = {
            'vulnerabilities': 'Vulnerabilidades',
            'code_quality': 'Calidad de Código',
            'dependencies': 'Dependencias',
            'containers': 'Contenedores'
        };
        return categoryNames[cat] || cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
}

// Enhanced global functions
function updateHeatmap() {
    try {
        if (window.heatmap && window.heatmap.safeRender) {
            window.heatmap.safeRender();
        }
    } catch (error) {
        console.warn('Update heatmap failed:', error);
    }
}

function zoomTimeline(period, eventTarget = null) {
    try {
        console.log('zoomTimeline called with period:', period);
        
        // Update button states
        const buttons = document.querySelectorAll('.btn-group .btn');
        buttons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toLowerCase().includes(period.toLowerCase())) {
                btn.classList.add('active');
            }
        });
        
        // Update title dynamically - be more specific with selector
        const titleElements = document.querySelectorAll('.card-title');
        titleElements.forEach(titleElement => {
            if (titleElement && titleElement.textContent.includes('Risk Timeline')) {
                const periodNames = {
                    '6h': '6 Horas',
                    '24h': '24 Horas', 
                    '7d': '7 Días'
                };
                const periodName = periodNames[period] || '24 Horas';
                titleElement.innerHTML = `<i class="card-icon" data-feather="activity"></i> Risk Timeline (${periodName})`;
                console.log('Title updated to:', `Risk Timeline (${periodName})`);
            }
        });
        
        // Replace feather icons
        if (typeof feather !== 'undefined' && feather.replace) {
            setTimeout(() => {
                try {
                    feather.replace();
                } catch (e) {}
            }, 50);
        }
        
        // Create/update chart
        if (window.heatmap && window.heatmap.safeCreateChart) {
            window.heatmap.safeCreateChart(period);
        } else {
            console.warn('Heatmap instance not available');
        }
    } catch (error) {
        console.error('Timeline zoom failed:', error);
    }
}

function sortHeatmapTable(column) {
    try {
        if (!window.heatmap || !window.heatmap.data) return;
        
        const projects = [...window.heatmap.data.projects];
        projects.sort((a, b) => {
            switch(column) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'risk-score':
                    return window.heatmap.calcOverall(b.risks) - window.heatmap.calcOverall(a.risks);
                default:
                    return 0;
            }
        });
        
        window.heatmap.data.projects = projects;
        window.heatmap.safeRenderTable();
    } catch (error) {
        console.warn('Sort heatmap table failed:', error);
    }
}

// Other global functions
function refreshHeatmap() { updateHeatmap(); }
function toggleRealTimeMode() { console.log('Real-time mode toggled'); }
function exportHeatmapData() { console.log('Export requested'); }
function clearFilters() { console.log('Filters cleared'); }
function createRiskTicket() { console.log('Risk ticket creation requested'); }
function sortTable(column) {
    if (window.location.pathname.includes('security-heatmap')) {
        return sortHeatmapTable(column);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    try {
        window.heatmap = new SecurityHeatmap();
        window.heatmap.init();
    } catch (error) {
        console.error('Heatmap initialization failed:', error);
    }
});
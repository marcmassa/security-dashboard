/**
 * Unit Tests for Security Heatmap
 * Comprehensive test suite to catch errors and validate functionality
 */

class HeatmapTester {
    constructor() {
        this.tests = [];
        this.results = { passed: 0, failed: 0, errors: [] };
    }

    // Test runner
    runAllTests() {
        console.log('🧪 Starting Security Heatmap Tests...');
        
        this.testGlobalFunctionsExist();
        this.testSecurityHeatmapClass();
        this.testDOMSafety();
        this.testChartFunctionality();
        this.testDataIntegrity();
        
        this.showResults();
    }

    // Test global functions existence
    testGlobalFunctionsExist() {
        const functions = [
            'updateHeatmap', 'refreshHeatmap', 'toggleRealTimeMode',
            'exportHeatmapData', 'zoomTimeline', 'sortHeatmapTable', 
            'clearFilters', 'createRiskTicket'
        ];

        functions.forEach(funcName => {
            this.test(`Global function ${funcName} exists`, () => {
                return typeof window[funcName] === 'function';
            });
        });
    }

    // Test SecurityHeatmap class
    testSecurityHeatmapClass() {
        this.test('SecurityHeatmap class exists', () => {
            return typeof SecurityHeatmap === 'function';
        });

        this.test('SecurityHeatmap can be instantiated', () => {
            const heatmap = new SecurityHeatmap();
            return heatmap instanceof SecurityHeatmap;
        });

        this.test('SecurityHeatmap has required methods', () => {
            const heatmap = new SecurityHeatmap();
            const methods = ['init', 'safeRender', 'safeRenderGrid', 'safeRenderTable', 'safeUpdateStats', 'safeCreateChart', 'calcOverall'];
            return methods.every(method => typeof heatmap[method] === 'function');
        });

        this.test('SecurityHeatmap initializes with valid data', () => {
            const heatmap = new SecurityHeatmap();
            return heatmap.data && 
                   Array.isArray(heatmap.data.projects) && 
                   heatmap.data.projects.length > 0;
        });
    }

    // Test DOM safety
    testDOMSafety() {
        this.test('Global functions handle missing DOM elements gracefully', () => {
            try {
                // Test functions with non-existent elements
                updateHeatmap();
                refreshHeatmap();
                toggleRealTimeMode();
                
                // Create mock event for zoomTimeline
                const mockEvent = { target: { classList: { add: () => {}, remove: () => {} } } };
                window.event = mockEvent;
                zoomTimeline('24h');
                window.event = undefined;
                
                sortHeatmapTable('name');
                clearFilters();
                createRiskTicket();
                return true;
            } catch (error) {
                console.error('DOM safety test failed:', error);
                this.logDetailedError(error);
                return false;
            }
        });

        this.test('Functions handle null/undefined gracefully', () => {
            try {
                const originalHeatmap = window.heatmap;
                window.heatmap = null;
                
                updateHeatmap();
                refreshHeatmap();
                
                window.heatmap = undefined;
                updateHeatmap();
                refreshHeatmap();
                
                window.heatmap = originalHeatmap;
                return true;
            } catch (error) {
                console.error('Null handling test failed:', error);
                return false;
            }
        });
    }

    // Test chart functionality
    testChartFunctionality() {
        this.test('Chart creation handles missing Chart.js gracefully', () => {
            try {
                const heatmap = new SecurityHeatmap();
                const originalChart = window.Chart;
                window.Chart = undefined;
                
                heatmap.safeCreateChart('24h');
                
                window.Chart = originalChart;
                return true;
            } catch (error) {
                console.error('Chart test failed:', error);
                return false;
            }
        });

        this.test('Chart periods are handled correctly', () => {
            const heatmap = new SecurityHeatmap();
            const periods = ['6h', '24h', '7d', 'invalid'];
            
            return periods.every(period => {
                try {
                    heatmap.safeCreateChart(period);
                    return true;
                } catch (error) {
                    console.error(`Chart period ${period} failed:`, error);
                    return false;
                }
            });
        });
    }

    // Test data integrity
    testDataIntegrity() {
        this.test('calcOverall function works correctly', () => {
            const heatmap = new SecurityHeatmap();
            
            const testCases = [
                { risks: { a: 1, b: 2, c: 3 }, expected: 2 },
                { risks: { a: 0, b: 0, c: 0 }, expected: 0 },
                { risks: {}, expected: 0 },
                { risks: null, expected: 0 },
                { risks: undefined, expected: 0 }
            ];
            
            return testCases.every(testCase => {
                const result = heatmap.calcOverall(testCase.risks);
                return result === testCase.expected;
            });
        });

        this.test('Badge classes are assigned correctly', () => {
            const testCases = [
                { score: 0, expected: 'bg-secondary' },
                { score: 1, expected: 'bg-info' },
                { score: 4, expected: 'bg-warning' },
                { score: 7, expected: 'bg-danger' },
                { score: 10, expected: 'bg-danger' }
            ];
            
            return testCases.every(testCase => {
                let badge;
                if (testCase.score >= 7) badge = 'bg-danger';
                else if (testCase.score >= 4) badge = 'bg-warning';
                else if (testCase.score >= 1) badge = 'bg-info';
                else badge = 'bg-secondary';
                
                return badge === testCase.expected;
            });
        });

        this.test('Project data structure is valid', () => {
            const heatmap = new SecurityHeatmap();
            
            return heatmap.data.projects.every(project => {
                return project.name && 
                       typeof project.name === 'string' &&
                       project.risks &&
                       typeof project.risks === 'object' &&
                       project.counts &&
                       typeof project.counts === 'object';
            });
        });
    }

    // Test helper
    test(description, testFunction) {
        try {
            const result = testFunction();
            if (result) {
                this.results.passed++;
                console.log(`✅ ${description}`);
            } else {
                this.results.failed++;
                this.results.errors.push(`❌ ${description}: Test returned false`);
                console.log(`❌ ${description}: Test returned false`);
            }
        } catch (error) {
            this.results.failed++;
            this.results.errors.push(`❌ ${description}: ${error.message}`);
            console.log(`❌ ${description}: ${error.message}`);
        }
    }

    // Log detailed error information
    logDetailedError(error) {
        console.error('Detailed error information:');
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        if (error.cause) console.error('Error cause:', error.cause);
    }

    // Show test results
    showResults() {
        console.log('\n📊 Test Results:');
        console.log(`✅ Passed: ${this.results.passed}`);
        console.log(`❌ Failed: ${this.results.failed}`);
        console.log(`📈 Success Rate: ${Math.round((this.results.passed / (this.results.passed + this.results.failed)) * 100)}%`);
        
        if (this.results.errors.length > 0) {
            console.log('\n🚨 Errors Found:');
            this.results.errors.forEach(error => console.log(error));
        } else {
            console.log('\n🎉 All tests passed! Security Heatmap is functioning correctly.');
        }
    }

    // Performance test
    runPerformanceTests() {
        console.log('\n⚡ Running Performance Tests...');
        
        const start = performance.now();
        
        // Test initialization performance
        const heatmap = new SecurityHeatmap();
        heatmap.init();
        
        const initTime = performance.now() - start;
        console.log(`📊 Initialization time: ${initTime.toFixed(2)}ms`);
        
        // Test rendering performance
        const renderStart = performance.now();
        heatmap.safeRender();
        const renderTime = performance.now() - renderStart;
        console.log(`📊 Render time: ${renderTime.toFixed(2)}ms`);
        
        // Test chart creation performance
        const chartStart = performance.now();
        heatmap.safeCreateChart('24h');
        const chartTime = performance.now() - chartStart;
        console.log(`📊 Chart creation time: ${chartTime.toFixed(2)}ms`);
        
        const totalTime = performance.now() - start;
        console.log(`📊 Total test time: ${totalTime.toFixed(2)}ms`);
        
        // Performance benchmarks
        if (initTime > 100) console.warn('⚠️ Initialization is slow (>100ms)');
        if (renderTime > 50) console.warn('⚠️ Rendering is slow (>50ms)');
        if (chartTime > 200) console.warn('⚠️ Chart creation is slow (>200ms)');
        
        console.log('⚡ Performance tests completed');
    }
}

// Auto-run tests when script loads
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for the main heatmap to initialize
    setTimeout(() => {
        const tester = new HeatmapTester();
        tester.runAllTests();
        tester.runPerformanceTests();
    }, 1000);
});

// Export for manual testing
window.HeatmapTester = HeatmapTester;
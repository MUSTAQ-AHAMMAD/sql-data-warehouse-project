// API Testing Dashboard - JavaScript

// Configuration
const API_BASE_URL = window.location.origin;
let currentData = null;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing API Testing Dashboard...');
    
    // Load initial data
    loadStats();
    loadSources();
    loadErrorSummary();
    loadDLQFiles();
    
    // Set up event listeners
    setupEventListeners();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadStats();
        loadErrorSummary();
        loadDLQFiles();
    }, 30000);
});

// Set up event listeners
function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', refreshAll);
    document.getElementById('fetchBtn').addEventListener('click', fetchData);
    document.getElementById('validateBtn').addEventListener('click', validateData);
    document.getElementById('sourceSelect').addEventListener('change', updateEntityOptions);
}

// Refresh all data
function refreshAll() {
    showToast('Refreshing data...', 'info');
    loadStats();
    loadSources();
    loadErrorSummary();
    loadDLQFiles();
}

// Load dashboard statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalSources').textContent = data.stats.total_sources;
            document.getElementById('totalErrors').textContent = data.stats.total_errors;
            document.getElementById('dlqCount').textContent = data.stats.dlq_count;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load data sources
async function loadSources() {
    const sourcesList = document.getElementById('sourcesList');
    const sourceSelect = document.getElementById('sourceSelect');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/sources`);
        const data = await response.json();
        
        if (data.success && data.sources) {
            // Update sources list
            sourcesList.innerHTML = '';
            data.sources.forEach(source => {
                const sourceItem = createSourceItem(source);
                sourcesList.appendChild(sourceItem);
            });
            
            // Update source select dropdown
            sourceSelect.innerHTML = '<option value="">Select a source...</option>';
            data.sources.forEach(source => {
                if (source.enabled) {
                    const option = document.createElement('option');
                    option.value = source.name;
                    option.textContent = source.name.charAt(0).toUpperCase() + source.name.slice(1);
                    option.dataset.entities = JSON.stringify(source.supported_entities);
                    sourceSelect.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('Failed to load sources:', error);
        sourcesList.innerHTML = '<div class="error">Failed to load data sources</div>';
    }
}

// Create source item element
function createSourceItem(source) {
    const div = document.createElement('div');
    div.className = `source-item ${source.enabled ? 'enabled' : 'disabled'}`;
    div.innerHTML = `
        <div class="source-name">${source.name}</div>
        <div class="source-description">${source.description || 'No description'}</div>
        <span class="source-status ${source.enabled ? 'enabled' : 'disabled'}">
            ${source.enabled ? 'Enabled' : 'Disabled'}
        </span>
    `;
    
    // Add click event for testing connection
    if (source.enabled) {
        div.addEventListener('click', () => testConnection(source.name));
    }
    
    return div;
}

// Test connection to a data source
async function testConnection(sourceName) {
    showToast(`Testing connection to ${sourceName}...`, 'info');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/sources/${sourceName}/test`);
        const data = await response.json();
        
        if (data.success && data.result.success) {
            showToast(`Connection to ${sourceName} successful!`, 'success');
        } else {
            showToast(`Connection to ${sourceName} failed: ${data.result.message}`, 'error');
        }
    } catch (error) {
        console.error('Connection test failed:', error);
        showToast(`Connection test failed: ${error.message}`, 'error');
    }
}

// Update entity options based on selected source
function updateEntityOptions() {
    const sourceSelect = document.getElementById('sourceSelect');
    const entitySelect = document.getElementById('entitySelect');
    
    const selectedOption = sourceSelect.options[sourceSelect.selectedIndex];
    
    if (selectedOption && selectedOption.dataset.entities) {
        const entities = JSON.parse(selectedOption.dataset.entities);
        
        entitySelect.innerHTML = '<option value="">Select an entity...</option>';
        entities.forEach(entity => {
            const option = document.createElement('option');
            option.value = entity;
            option.textContent = entity.charAt(0).toUpperCase() + entity.slice(1);
            entitySelect.appendChild(option);
        });
        
        entitySelect.disabled = false;
    } else {
        entitySelect.innerHTML = '<option value="">Select an entity...</option>';
        entitySelect.disabled = true;
    }
}

// Fetch data from API
async function fetchData() {
    const sourceName = document.getElementById('sourceSelect').value;
    const entityType = document.getElementById('entitySelect').value;
    const page = document.getElementById('pageInput').value;
    const perPage = document.getElementById('perPageInput').value;
    
    if (!sourceName || !entityType) {
        showToast('Please select a source and entity type', 'warning');
        return;
    }
    
    const apiResponse = document.getElementById('apiResponse');
    apiResponse.innerHTML = '<div class="loading">Fetching data...</div>';
    
    try {
        const url = `${API_BASE_URL}/api/sources/${sourceName}/entities/${entityType}/fetch?page=${page}&per_page=${perPage}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            currentData = data.data;
            displayAPIResponse(data.data);
            showToast('Data fetched successfully!', 'success');
        } else {
            apiResponse.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            showToast(`Failed to fetch data: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Fetch failed:', error);
        apiResponse.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        showToast(`Fetch failed: ${error.message}`, 'error');
    }
}

// Display API response
function displayAPIResponse(data) {
    const apiResponse = document.getElementById('apiResponse');
    
    const jsonString = JSON.stringify(data, null, 2);
    apiResponse.innerHTML = `
        <div class="response-header">
            <strong>API Response:</strong>
            <button class="btn btn-primary" onclick="copyToClipboard('${escapeHtml(jsonString)}')">
                <i class="fas fa-copy"></i> Copy
            </button>
        </div>
        <pre class="response-json">${escapeHtml(jsonString)}</pre>
    `;
}

// Validate data
async function validateData() {
    if (!currentData || !currentData.data) {
        showToast('Please fetch data first', 'warning');
        return;
    }
    
    const entityType = document.getElementById('entitySelect').value;
    const validationResults = document.getElementById('validationResults');
    const validationContent = document.getElementById('validationContent');
    
    validationContent.innerHTML = '<div class="loading">Validating data...</div>';
    validationResults.style.display = 'block';
    
    try {
        // Schema validation
        const schemaResponse = await fetch(`${API_BASE_URL}/api/validate/schema`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                records: currentData.data,
                entity_type: entityType
            })
        });
        
        const schemaData = await schemaResponse.json();
        
        // Quality validation
        const qualityResponse = await fetch(`${API_BASE_URL}/api/validate/quality`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                records: currentData.data
            })
        });
        
        const qualityData = await qualityResponse.json();
        
        // Display validation results
        displayValidationResults(schemaData, qualityData);
        
        // Update quality metrics
        if (qualityData.success) {
            displayQualityMetrics(qualityData.profile, qualityData.quality);
        }
        
        showToast('Validation completed!', 'success');
        
    } catch (error) {
        console.error('Validation failed:', error);
        validationContent.innerHTML = `<div class="error">Validation failed: ${error.message}</div>`;
        showToast(`Validation failed: ${error.message}`, 'error');
    }
}

// Display validation results
function displayValidationResults(schemaData, qualityData) {
    const validationContent = document.getElementById('validationContent');
    
    let html = '<div>';
    
    // Schema validation
    html += '<h4>Schema Validation</h4>';
    if (schemaData.success && schemaData.validation) {
        const validation = schemaData.validation;
        
        if (validation.success) {
            html += '<div class="validation-item success"><i class="fas fa-check-circle"></i> Schema validation passed</div>';
        } else {
            html += '<div class="validation-item error"><i class="fas fa-times-circle"></i> Schema validation failed</div>';
        }
        
        if (validation.errors && validation.errors.length > 0) {
            validation.errors.forEach(error => {
                html += `<div class="validation-item error"><i class="fas fa-exclamation-circle"></i> ${error}</div>`;
            });
        }
        
        if (validation.warnings && validation.warnings.length > 0) {
            validation.warnings.forEach(warning => {
                html += `<div class="validation-item warning"><i class="fas fa-exclamation-triangle"></i> ${warning}</div>`;
            });
        }
    }
    
    // Quality validation
    html += '<h4>Quality Validation</h4>';
    if (qualityData.success && qualityData.quality) {
        const quality = qualityData.quality;
        
        html += `<div class="validation-item ${quality.success ? 'success' : 'error'}">
            <i class="fas ${quality.success ? 'fa-check-circle' : 'fa-times-circle'}"></i>
            Checks Passed: ${quality.checks_passed} / ${quality.checks_passed + quality.checks_failed}
        </div>`;
        
        if (quality.details) {
            quality.details.forEach(detail => {
                html += `<div class="validation-item ${detail.passed ? 'success' : 'warning'}">
                    <i class="fas ${detail.passed ? 'fa-check' : 'fa-exclamation-triangle'}"></i>
                    ${detail.description}: ${detail.message}
                </div>`;
            });
        }
    }
    
    html += '</div>';
    validationContent.innerHTML = html;
}

// Display quality metrics
function displayQualityMetrics(profile, quality) {
    const qualityMetrics = document.getElementById('qualityMetrics');
    
    let html = '';
    
    // Row count
    html += `
        <div class="metric-card">
            <div class="metric-title">Total Records</div>
            <div class="metric-value">${profile.row_count}</div>
        </div>
    `;
    
    // Column count
    html += `
        <div class="metric-card">
            <div class="metric-title">Total Columns</div>
            <div class="metric-value">${profile.column_count}</div>
        </div>
    `;
    
    // Null percentage
    let totalNulls = 0;
    let totalCells = profile.row_count * profile.column_count;
    
    for (const column in profile.columns) {
        totalNulls += profile.columns[column].null_count;
    }
    
    const nullPercentage = totalCells > 0 ? ((totalNulls / totalCells) * 100).toFixed(2) : 0;
    
    html += `
        <div class="metric-card">
            <div class="metric-title">Null Values</div>
            <div class="metric-value">${nullPercentage}%</div>
        </div>
    `;
    
    // Quality checks
    html += `
        <div class="metric-card">
            <div class="metric-title">Quality Score</div>
            <div class="metric-value">${quality.checks_passed}/${quality.checks_passed + quality.checks_failed}</div>
        </div>
    `;
    
    qualityMetrics.innerHTML = html;
}

// Load error summary
async function loadErrorSummary() {
    const errorSummary = document.getElementById('errorSummary');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/errors/summary`);
        const data = await response.json();
        
        if (data.success && data.summary) {
            const summary = data.summary;
            
            let html = '<div>';
            html += `<div class="error-stat">
                <span class="error-stat-label">Total Errors:</span>
                <span class="error-stat-value">${summary.total_errors}</span>
            </div>`;
            
            // By severity
            if (summary.by_severity) {
                for (const [severity, count] of Object.entries(summary.by_severity)) {
                    if (count > 0) {
                        html += `<div class="error-stat">
                            <span class="error-stat-label">${severity.charAt(0).toUpperCase() + severity.slice(1)}:</span>
                            <span class="error-stat-value">${count}</span>
                        </div>`;
                    }
                }
            }
            
            html += '</div>';
            errorSummary.innerHTML = html;
        }
    } catch (error) {
        console.error('Failed to load error summary:', error);
        errorSummary.innerHTML = '<div class="error">Failed to load error summary</div>';
    }
}

// Load DLQ files
async function loadDLQFiles() {
    const dlqList = document.getElementById('dlqList');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/dlq/files`);
        const data = await response.json();
        
        if (data.success && data.files) {
            if (data.files.length === 0) {
                dlqList.innerHTML = '<div class="info">No files in DLQ</div>';
            } else {
                dlqList.innerHTML = '';
                data.files.forEach(file => {
                    const fileItem = createDLQItem(file);
                    dlqList.appendChild(fileItem);
                });
            }
        }
    } catch (error) {
        console.error('Failed to load DLQ files:', error);
        dlqList.innerHTML = '<div class="error">Failed to load DLQ files</div>';
    }
}

// Create DLQ item element
function createDLQItem(file) {
    const div = document.createElement('div');
    div.className = 'dlq-item';
    div.innerHTML = `
        <div class="dlq-filename">${file.filename}</div>
        <div class="dlq-meta">
            ${file.source} - ${file.entity_type} - ${file.error_type}
            <br>
            ${new Date(file.timestamp).toLocaleString()}
        </div>
    `;
    return div;
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' :
                type === 'error' ? 'fa-times-circle' :
                type === 'warning' ? 'fa-exclamation-triangle' :
                'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Remove toast after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Utility: Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy to clipboard', 'error');
    });
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

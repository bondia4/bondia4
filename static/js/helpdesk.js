// Custom JavaScript for BRTS Helpdesk System

// Global variables
let notificationCount = 0;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
});

function initializeComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize file upload drag and drop
    initializeFileUpload();
    
    // Initialize auto-refresh for real-time updates
    initializeAutoRefresh();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize form validation
    initializeFormValidation();
}

// Notification Management
function updateNotifications(notifications, count) {
    const notificationList = document.getElementById('notification-list');
    const notificationCount = document.getElementById('notification-count');
    
    if (!notificationList || !notificationCount) return;
    
    // Update count badge
    if (count > 0) {
        notificationCount.textContent = count;
        notificationCount.style.display = 'inline';
    } else {
        notificationCount.style.display = 'none';
    }
    
    // Update notification list
    notificationList.innerHTML = '';
    
    if (notifications.length === 0) {
        notificationList.innerHTML = '<li><span class="dropdown-item-text text-muted">No new notifications</span></li>';
        return;
    }
    
    notifications.forEach(function(notification) {
        const notificationItem = document.createElement('li');
        notificationItem.innerHTML = `
            <div class="dropdown-item-text notification-item unread">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong class="small">${escapeHtml(notification.title)}</strong><br>
                        <span class="small text-muted">${escapeHtml(notification.message)}</span>
                    </div>
                    <small class="text-muted">${formatDate(notification.created_at)}</small>
                </div>
                ${notification.ticket_id ? `<a href="/helpdesk/tickets/${notification.ticket_id}/" class="btn btn-sm btn-outline-primary mt-2">View Ticket</a>` : ''}
            </div>
        `;
        notificationList.appendChild(notificationItem);
    });
}

// File Upload with Drag and Drop
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(function(input) {
        const container = input.closest('.file-upload-area') || input.parentNode;
        
        // Drag and drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            container.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            container.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            container.addEventListener(eventName, unhighlight, false);
        });
        
        container.addEventListener('drop', handleDrop, false);
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        function highlight(e) {
            container.classList.add('dragover');
        }
        
        function unhighlight(e) {
            container.classList.remove('dragover');
        }
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                input.files = files;
                displayFileInfo(files[0], container);
            }
        }
    });
}

function displayFileInfo(file, container) {
    const info = container.querySelector('.file-info') || document.createElement('div');
    info.className = 'file-info mt-2';
    info.innerHTML = `
        <div class="alert alert-info">
            <i class="bi bi-file-earmark"></i>
            <strong>${escapeHtml(file.name)}</strong>
            <br><small>${formatFileSize(file.size)}</small>
        </div>
    `;
    
    if (!container.querySelector('.file-info')) {
        container.appendChild(info);
    }
}

// Auto-refresh functionality
function initializeAutoRefresh() {
    // Only on dashboard pages
    if (window.location.pathname.includes('dashboard') || window.location.pathname.includes('tickets/')) {
        // Auto-refresh every 60 seconds
        setInterval(function() {
            if (document.visibilityState === 'visible') {
                refreshPageData();
            }
        }, 60000);
    }
}

function refreshPageData() {
    // Check for new notifications
    if (typeof updateNotifications === 'function') {
        fetch('/helpdesk/api/notifications/')
            .then(response => response.json())
            .then(data => {
                updateNotifications(data.notifications, data.count);
            })
            .catch(error => console.log('Error refreshing notifications:', error));
    }
}

// Search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[name="search"]');
    
    searchInputs.forEach(function(input) {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                if (input.value.length >= 3 || input.value.length === 0) {
                    // Auto-submit search form
                    const form = input.closest('form');
                    if (form) {
                        form.submit();
                    }
                }
            }, 500);
        });
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Utility Functions
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMins < 1) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins}m ago`;
    } else if (diffHours < 24) {
        return `${diffHours}h ago`;
    } else if (diffDays < 7) {
        return `${diffDays}d ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

// Loading state management
function showLoading(element) {
    element.classList.add('loading');
    element.disabled = true;
}

function hideLoading(element) {
    element.classList.remove('loading');
    element.disabled = false;
}

// AJAX form submission
function submitFormAjax(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    const button = form.querySelector('button[type="submit"]');
    
    showLoading(button);
    
    fetch(form.action, {
        method: form.method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(button);
        if (data.success) {
            if (successCallback) successCallback(data);
        } else {
            if (errorCallback) errorCallback(data);
        }
    })
    .catch(error => {
        hideLoading(button);
        console.error('Error:', error);
        if (errorCallback) errorCallback({error: 'Network error'});
    });
}

// Chart helpers for analytics
function createChart(canvasId, type, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...options
        }
    });
}

// Export functions for global use
window.HelpdeskJS = {
    updateNotifications: updateNotifications,
    showLoading: showLoading,
    hideLoading: hideLoading,
    submitFormAjax: submitFormAjax,
    createChart: createChart,
    formatDate: formatDate,
    formatFileSize: formatFileSize
};
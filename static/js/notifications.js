/**
 * Notification system for Security Dashboard
 * Handles flash messages and popup notifications with proper dark theme styling
 */

class NotificationManager {
    constructor() {
        this.init();
    }

    init() {
        // Initialize notification container if it doesn't exist
        this.createNotificationContainer();
        
        // Process existing flash messages
        this.processFlashMessages();
        
        // Auto-hide notifications after delay
        this.autoHideNotifications();
    }

    createNotificationContainer() {
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
    }

    processFlashMessages() {
        // Find all existing alert elements and enhance them
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            this.enhanceAlert(alert);
        });
    }

    enhanceAlert(alertElement) {
        // Ensure proper visibility and styling
        alertElement.style.backgroundColor = 'var(--bs-card-bg)';
        alertElement.style.color = 'var(--bs-body-color)';
        alertElement.style.border = '1px solid var(--bs-border-color)';
        alertElement.style.borderRadius = '8px';
        alertElement.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        
        // Add close button if not present
        if (!alertElement.querySelector('.btn-close')) {
            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.className = 'btn-close';
            closeBtn.setAttribute('data-bs-dismiss', 'alert');
            closeBtn.setAttribute('aria-label', 'Close');
            closeBtn.style.filter = 'invert(1)'; // Make close button visible on dark theme
            alertElement.appendChild(closeBtn);
        }
    }

    showNotification(type, message, title = null, duration = 5000) {
        const container = document.getElementById('notification-container');
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `toast align-items-center border-0 show notification-${type}`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');
        
        // Apply proper styling based on type
        this.applyNotificationStyling(notification, type);
        
        const content = `
            <div class="d-flex">
                <div class="toast-body">
                    ${title ? `<strong>${title}</strong><br>` : ''}
                    ${message}
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        notification.innerHTML = content;
        container.appendChild(notification);
        
        // Initialize Bootstrap toast
        const toast = new bootstrap.Toast(notification, {
            delay: duration
        });
        toast.show();
        
        // Remove element after hiding
        notification.addEventListener('hidden.bs.toast', () => {
            notification.remove();
        });
        
        return notification;
    }

    applyNotificationStyling(element, type) {
        // Base styling for dark theme compatibility
        element.style.backgroundColor = 'hsl(var(--card))';
        element.style.color = 'hsl(var(--foreground))';
        element.style.border = '1px solid hsl(var(--border))';
        element.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.25)';
        
        // Type-specific styling
        switch (type) {
            case 'success':
                element.style.borderLeftColor = 'hsl(var(--low))';
                element.style.borderLeftWidth = '4px';
                break;
            case 'error':
            case 'danger':
                element.style.borderLeftColor = 'hsl(var(--critical))';
                element.style.borderLeftWidth = '4px';
                break;
            case 'warning':
                element.style.borderLeftColor = 'hsl(var(--medium))';
                element.style.borderLeftWidth = '4px';
                break;
            case 'info':
                element.style.borderLeftColor = 'hsl(var(--info))';
                element.style.borderLeftWidth = '4px';
                break;
        }
    }

    autoHideNotifications() {
        // Auto-hide flash messages after 8 seconds
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
            alerts.forEach(alert => {
                if (alert.classList.contains('show') || !alert.classList.contains('fade')) {
                    const closeBtn = alert.querySelector('.btn-close');
                    if (closeBtn) {
                        closeBtn.click();
                    } else {
                        alert.style.transition = 'opacity 0.5s ease';
                        alert.style.opacity = '0';
                        setTimeout(() => alert.remove(), 500);
                    }
                }
            });
        }, 8000);
    }

    // Utility methods for common notifications
    success(message, title = 'Success') {
        return this.showNotification('success', message, title);
    }

    error(message, title = 'Error') {
        return this.showNotification('error', message, title);
    }

    warning(message, title = 'Warning') {
        return this.showNotification('warning', message, title);
    }

    info(message, title = 'Information') {
        return this.showNotification('info', message, title);
    }
}

// Initialize notification manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.notifications = new NotificationManager();
    
    // Global function for easy access
    window.showNotification = function(type, message, title, duration) {
        return window.notifications.showNotification(type, message, title, duration);
    };
});

// Enhancement for SonarQube configuration testing
document.addEventListener('DOMContentLoaded', function() {
    const testButtons = document.querySelectorAll('[data-test-connection]');
    testButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<i data-feather="loader" class="me-1"></i> Testing...';
            this.disabled = true;
            
            // Re-render feather icons
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
            
            // Reset button after timeout (will be overridden by actual response)
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
            }, 10000);
        });
    });
});
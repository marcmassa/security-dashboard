/**
 * Configuration page styling fixes
 * Forces proper contrast and styling for dark theme
 */

document.addEventListener('DOMContentLoaded', function() {
    // Force styling on configuration page elements
    forceConfigurationStyling();
    
    // Re-apply styling when the page changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                forceConfigurationStyling();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

function forceConfigurationStyling() {
    // Force card headers to be blue with white text
    const cardHeaders = document.querySelectorAll('.card-header');
    cardHeaders.forEach(header => {
        header.style.backgroundColor = '#3b82f6';
        header.style.color = '#ffffff';
        header.style.borderBottom = '1px solid #334155';
        header.style.borderRadius = '12px 12px 0 0';
        
        // Force all children to be white
        const children = header.querySelectorAll('*');
        children.forEach(child => {
            child.style.color = '#ffffff';
        });
    });
    
    // Force list group items to have white text
    const listItems = document.querySelectorAll('.list-group-item');
    listItems.forEach(item => {
        item.style.backgroundColor = '#1e293b';
        item.style.color = '#ffffff';
        item.style.border = '1px solid #334155';
        item.style.borderRadius = '8px';
        item.style.marginBottom = '4px';
        
        // Handle active state
        if (item.classList.contains('active')) {
            item.style.backgroundColor = '#3b82f6';
            item.style.borderColor = '#3b82f6';
        }
        
        // Add hover effect
        item.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active')) {
                this.style.backgroundColor = '#2563eb';
            }
        });
        
        item.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.backgroundColor = '#1e293b';
            }
        });
    });
    
    // Force all cards to have rounded corners
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.borderRadius = '12px';
        card.style.border = '1px solid #334155';
        card.style.overflow = 'hidden';
    });
    
    // Force all text in configuration to be white
    const configElements = document.querySelectorAll('.container-fluid *');
    configElements.forEach(element => {
        if (element.tagName === 'H1' || 
            element.tagName === 'H2' || 
            element.tagName === 'H3' || 
            element.tagName === 'H4' || 
            element.tagName === 'H5' || 
            element.tagName === 'H6' ||
            element.classList.contains('card-title') ||
            element.classList.contains('form-label')) {
            element.style.color = '#ffffff';
            element.style.fontWeight = '600';
        }
        
        if (element.classList.contains('text-muted') || 
            element.classList.contains('form-text')) {
            element.style.color = '#cbd5e1';
        }
    });
    
    // Force form controls to have proper styling
    const formControls = document.querySelectorAll('.form-control, .form-select');
    formControls.forEach(control => {
        control.style.backgroundColor = '#1e293b';
        control.style.color = '#ffffff';
        control.style.border = '1px solid #334155';
        control.style.borderRadius = '8px';
    });
    
    // Force buttons to have proper styling
    const buttons = document.querySelectorAll('.btn-outline-primary, .btn-outline-secondary');
    buttons.forEach(button => {
        button.style.color = '#ffffff';
        button.style.borderColor = '#334155';
    });
    
    console.log('Configuration styling applied');
}

// Export for global access
window.forceConfigurationStyling = forceConfigurationStyling;
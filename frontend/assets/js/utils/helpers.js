/**
 * API Utility Functions
 * Common helper functions for formatting and styling
 */

window.ApiUtils = {
    // Get CSS class for HTTP method badge
    getMethodBadgeClass(method) {
        const classes = {
            'GET': 'bg-green-100 text-green-800',
            'POST': 'bg-blue-100 text-blue-800',
            'PUT': 'bg-yellow-100 text-yellow-800',
            'DELETE': 'bg-red-100 text-red-800',
            'PATCH': 'bg-purple-100 text-purple-800'
        };
        return classes[method?.toUpperCase()] || 'bg-gray-100 text-gray-800';
    },

    // Get CSS class for status badge
    getStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'approved': 'bg-green-100 text-green-800',
            'rejected': 'bg-red-100 text-red-800',
            'completed': 'bg-blue-100 text-blue-800',
            'running': 'bg-indigo-100 text-indigo-800',
            'failed': 'bg-red-100 text-red-800',
            'success': 'bg-green-100 text-green-800',
            'active': 'bg-green-100 text-green-800',
            'inactive': 'bg-gray-100 text-gray-800'
        };
        return classes[status?.toLowerCase()] || 'bg-gray-100 text-gray-800';
    },

    // Get CSS class for role badge
    getRoleBadgeClass(role) {
        const classes = {
            'admin': 'bg-red-100 text-red-800',
            'leader': 'bg-blue-100 text-blue-800',
            'member': 'bg-green-100 text-green-800'
        };
        return classes[role?.toLowerCase()] || 'bg-gray-100 text-gray-800';
    },

    // Format date string for display
    formatDate(dateString) {
        if (!dateString) return '-';
        
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now - date);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays <= 1) {
                return date.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } else if (diffDays <= 7) {
                return date.toLocaleDateString('en-US', {
                    weekday: 'short',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } else {
                return date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric'
                });
            }
        } catch (error) {
            return dateString;
        }
    },

    // Format duration in milliseconds
    formatDuration(milliseconds) {
        if (!milliseconds || milliseconds < 0) return '-';
        
        if (milliseconds < 1000) {
            return `${milliseconds}ms`;
        } else if (milliseconds < 60000) {
            return `${(milliseconds / 1000).toFixed(2)}s`;
        } else {
            const minutes = Math.floor(milliseconds / 60000);
            const seconds = ((milliseconds % 60000) / 1000).toFixed(0);
            return `${minutes}m ${seconds}s`;
        }
    },

    // Format numbers with appropriate units
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textArea);
            return success;
        }
    }
};

/**
 * Global Alert System
 * Provides alert functionality accessible from any component
 */
window.GlobalAlert = {
    // Show alert message
    show(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container') || this.createAlertContainer();
        
        const alert = document.createElement('div');
        
        const bgColor = {
            'success': 'bg-green-100 border-green-500 text-green-700',
            'error': 'bg-red-100 border-red-500 text-red-700',
            'warning': 'bg-yellow-100 border-yellow-500 text-yellow-700',
            'info': 'bg-blue-100 border-blue-500 text-blue-700'
        }[type] || 'bg-gray-100 border-gray-500 text-gray-700';
        
        alert.className = `${bgColor} border-l-4 p-4 mb-4 rounded-md shadow-lg transition-all duration-300`;
        alert.innerHTML = `
            <div class="flex justify-between items-center">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-lg font-bold">&times;</button>
            </div>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    },

    // Create alert container if it doesn't exist
    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm';
        document.body.appendChild(container);
        return container;
    }
};

/**
 * Global Navigation System
 */
window.GlobalNav = {
    loadPage(page) {
        // Dispatch custom event to the main app
        window.dispatchEvent(new CustomEvent('navigate', { detail: { page } }));
    }
};

/**
 * Global User System with Reactivity
 */
window.GlobalUser = {
    _currentUser: null,
    _listeners: [],
    
    setUser(user) {
        this._currentUser = user;
        // Notify all listeners of user change
        this._listeners.forEach(callback => {
            try {
                callback(user);
            } catch (error) {
                console.warn('GlobalUser listener error:', error);
            }
        });
        
        // Trigger Alpine.js reactivity by dispatching custom event
        if (typeof window !== 'undefined') {
            // Use setTimeout to ensure Alpine.js has fully initialized
            setTimeout(() => {
                window.dispatchEvent(new CustomEvent('user-changed', { 
                    detail: { user } 
                }));
            }, 100);
        }
    },
    
    getUser() {
        return this._currentUser;
    },
    
    getUserRole() {
        return this._currentUser?.role || 'member';
    },
    
    getUserId() {
        return this._currentUser?.id;
    },
    
    // Add listener for user changes
    addListener(callback) {
        this._listeners.push(callback);
        // Immediately call with current user if available
        if (this._currentUser) {
            callback(this._currentUser);
        }
    },
    
    // Remove listener
    removeListener(callback) {
        const index = this._listeners.indexOf(callback);
        if (index > -1) {
            this._listeners.splice(index, 1);
        }
    }
};
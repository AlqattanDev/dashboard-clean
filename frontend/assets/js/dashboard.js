window.DashboardApp = {
    modals: {
        executeModal: null,
        detailsModal: null,
        editModal: null,
        createModal: null,
        roleModal: null
    },
    
    currentUser: null,
    
    init() {
        if (window.location.pathname === '/login') {
            return;
        }
        this.setupEventListeners();
        this.loadUserInfo();
        this.setupHTMXConfig();
    },
    
    setupEventListeners() {
        document.addEventListener('htmx:responseError', (e) => {
            this.showAlert('An error occurred. Please try again.', 'error');
        });
        
        document.addEventListener('htmx:sendError', (e) => {
            this.showAlert('Network error. Please check your connection.', 'error');
        });
        
        document.addEventListener('htmx:beforeRequest', (e) => {
            const token = localStorage.getItem('token');
            if (token) {
                e.detail.xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    },
    
    setupHTMXConfig() {
        htmx.config.globalViewTransitions = true;
        htmx.config.defaultSwapStyle = 'outerHTML';
        htmx.config.defaultSwapDelay = 100;
        htmx.config.defaultSettleDelay = 100;
    },
    
    loadUserInfo() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        fetch('/api/v1/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(user => {
            this.currentUser = user;
        })
        .catch(() => {
            localStorage.removeItem('token');
            window.location.href = '/login';
        });
    },
    
    showAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.getElementById('alert-container') || this.createAlertContainer();
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} p-4 mb-4 rounded-md shadow-lg transition-all duration-300 transform translate-x-full`;
        
        const bgColor = {
            'success': 'bg-green-100 border-green-500 text-green-700',
            'error': 'bg-red-100 border-red-500 text-red-700',
            'warning': 'bg-yellow-100 border-yellow-500 text-yellow-700',
            'info': 'bg-blue-100 border-blue-500 text-blue-700'
        }[type] || 'bg-gray-100 border-gray-500 text-gray-700';
        
        alert.className += ` ${bgColor} border-l-4`;
        alert.innerHTML = `
            <div class="flex justify-between items-center">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-lg font-bold">&times;</button>
            </div>
        `;
        
        alertContainer.appendChild(alert);
        
        setTimeout(() => {
            alert.classList.remove('translate-x-full');
        }, 10);
        
        if (duration > 0) {
            setTimeout(() => {
                alert.classList.add('translate-x-full');
                setTimeout(() => alert.remove(), 300);
            }, duration);
        }
    },
    
    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm';
        document.body.appendChild(container);
        return container;
    },
    
    openModal(modalId, content = '') {
        const modal = document.getElementById(modalId);
        if (!modal) {
            this.createModal(modalId, content);
        } else {
            if (content) {
                modal.querySelector('.modal-content').innerHTML = content;
            }
            modal.classList.remove('hidden');
        }
    },
    
    createModal(modalId, content) {
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center';
        modal.innerHTML = `
            <div class="modal-backdrop fixed inset-0" onclick="DashboardApp.closeModal('${modalId}')"></div>
            <div class="modal-content bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                ${content}
            </div>
        `;
        document.body.appendChild(modal);
    },
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    },
    
    closeAllModals() {
        Object.keys(this.modals).forEach(modalKey => {
            const modalId = this.modals[modalKey];
            if (modalId) {
                this.closeModal(modalId);
            }
        });
        
        document.querySelectorAll('[id$="Modal"]').forEach(modal => {
            modal.classList.add('hidden');
        });
    },
    
    confirmAction(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    formatDuration(milliseconds) {
        if (milliseconds < 1000) {
            return `${milliseconds}ms`;
        }
        return `${(milliseconds / 1000).toFixed(2)}s`;
    },
    
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showAlert('Copied to clipboard!', 'success', 2000);
        }).catch(() => {
            this.showAlert('Failed to copy to clipboard', 'error');
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.DashboardApp.init();
});

function executeFunction(functionId, parameters = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    fetch(`/api/v1/functions/${functionId}/execute`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ parameters })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            DashboardApp.showAlert('Function executed successfully!', 'success');
        } else if (data.status === 'pending_approval') {
            DashboardApp.showAlert('Request submitted for approval', 'info');
        } else {
            DashboardApp.showAlert(data.error || 'Execution failed', 'error');
        }
        htmx.trigger(document.body, 'refreshData');
    })
    .catch(error => {
        DashboardApp.showAlert('Network error occurred', 'error');
    });
}

function logout() {
    const token = localStorage.getItem('token');
    if (token) {
        fetch('/api/v1/auth/logout', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        }).finally(() => {
            localStorage.removeItem('token');
            window.location.href = '/login';
        });
    } else {
        window.location.href = '/login';
    }
}

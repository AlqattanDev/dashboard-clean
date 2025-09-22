/**
 * Main Alpine.js Application
 * Pure SPA implementation without HTMX
 */

// Global app state and functionality
function app() {
    return {
        // Authentication state
        isAuthenticated: false,
        isLogging: false,
        user: null,
        isCheckingAuth: true, // Add loading state for auth check
        
        // Navigation state
        currentPage: null, // Don't set initial page until auth is checked
        appInitialized: false, // Track if app is fully initialized
        
        // Login form
        loginForm: {
            username: '',
            password: ''
        },

        // Initialize the application
        async init() {
            await this.checkAuth();
            
            // Set up navigation event listener
            window.addEventListener('navigate', (e) => {
                this.loadPage(e.detail.page);
            });
        },

        // Check authentication status
        async checkAuth() {
            const token = localStorage.getItem('token');
            if (!token) {
                this.isAuthenticated = false;
                this.currentPage = 'login'; // Set to login page if no token
                this.isCheckingAuth = false;
                return;
            }

            try {
                this.user = await window.apiClient.getCurrentUser();
                this.isAuthenticated = true;
                this.currentPage = 'dashboard'; // Set to dashboard if authenticated
                
                // Set user in global system
                window.GlobalUser.setUser(this.user);
            } catch (error) {
                localStorage.removeItem('token');
                this.isAuthenticated = false;
                this.currentPage = 'login'; // Set to login page if auth fails
                window.GlobalUser.setUser(null);
            } finally {
                this.isCheckingAuth = false;
                this.appInitialized = true;
            }
        },

        // Handle login
        async login() {
            this.isLogging = true;
            
            try {
                const data = await window.apiClient.login(
                    this.loginForm.username, 
                    this.loginForm.password
                );
                
                this.user = data.user;
                this.isAuthenticated = true;
                
                // Set user in global system
                window.GlobalUser.setUser(this.user);
                
                this.showAlert('Login successful!', 'success');
                this.loadPage('dashboard');
                
                // Reset form
                this.loginForm = { username: '', password: '' };
                
            } catch (error) {
                this.showAlert(error.message || 'Login failed', 'error');
            } finally {
                this.isLogging = false;
            }
        },

        // Handle logout
        async logout() {
            try {
                await window.apiClient.logout();
            } catch (error) {
                // Ignore logout errors
            }
            
            this.isAuthenticated = false;
            this.user = null;
            this.currentPage = 'dashboard';
            
            // Clear user from global system
            window.GlobalUser.setUser(null);
            
            this.showAlert('Logged out successfully', 'info');
        },

        // Load page component
        loadPage(page) {
            this.currentPage = page;
            
            // Initialize page-specific component if it exists
            const componentName = page + 'Page';
            if (window[componentName]) {
                // Page component will be initialized via x-data
                console.log(`Loading ${componentName} component`);
            }
        },

        // Check if current page matches
        isCurrentPage(page) {
            return this.currentPage === page;
        },

        // Show alert message
        showAlert(message, type = 'info') {
            const alertContainer = document.getElementById('alert-container');
            if (!alertContainer) return;
            
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

        // Get user initials for avatar
        getUserInitials() {
            if (!this.user || !this.user.username) return 'U';
            return this.user.username.charAt(0).toUpperCase();
        },

        // Check if user has permission for action
        canPerformAction(requiredRole) {
            if (!this.user) return false;
            
            const roleHierarchy = {
                'member': 1,
                'leader': 2,
                'admin': 3
            };
            
            const userLevel = roleHierarchy[this.user.role] || 0;
            const requiredLevel = roleHierarchy[requiredRole] || 0;
            
            return userLevel >= requiredLevel;
        },

        // Check if user is admin
        isAdmin() {
            return this.user && this.user.role === 'admin';
        },

        // Check if user is leader or admin
        isLeaderOrAdmin() {
            return this.user && ['admin', 'leader'].includes(this.user.role);
        }
    }
}

// Make app function globally available
window.app = app;
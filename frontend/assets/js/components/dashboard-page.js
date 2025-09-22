/**
 * Dashboard Page Component
 * Displays overview statistics and recent activity
 */

function dashboardPage() {
    return {
        // Component state
        loading: true,
        error: null,
        stats: {
            total_functions: 0,
            total_users: 0,
            pending_requests: 0,
            completed_requests_today: 0,
            my_pending_requests: 0
        },
        recentFunctions: [],
        recentRequests: [],

        // Initialize component
        async init() {
            // Wait for authentication to be ready
            if (!window.GlobalUser.getUser()) {
                // If no user yet, set up a watcher
                const checkAuth = () => {
                    if (window.GlobalUser.getUser()) {
                        this.loadDashboardData();
                    } else {
                        setTimeout(checkAuth, 100);
                    }
                };
                checkAuth();
            } else {
                await this.loadDashboardData();
            }
        },

        // Load all dashboard data
        async loadDashboardData() {
            this.loading = true;
            this.error = null;

            try {
                // Load stats and recent data in parallel
                const [stats, functions, requests] = await Promise.all([
                    this.loadStats(),
                    this.loadRecentFunctions(),
                    this.loadRecentRequests()
                ]);

                this.stats = stats;
                this.recentFunctions = functions.slice(0, 5); // Show top 5
                this.recentRequests = requests.slice(0, 5); // Show latest 5

            } catch (error) {
                this.error = error.message;
                console.error('Dashboard loading error:', error);
            } finally {
                this.loading = false;
            }
        },

        // Load dashboard statistics
        async loadStats() {
            try {
                return await window.apiClient.getDashboardStats();
            } catch (error) {
                // If stats endpoint doesn't exist, calculate manually
                const [functions, users, requests] = await Promise.all([
                    window.apiClient.getFunctions(),
                    window.apiClient.getUsers(),
                    window.apiClient.getRequests()
                ]);

                const today = new Date().toDateString();
                const completedToday = requests.filter(r => 
                    r.status === 'completed' && 
                    new Date(r.updated_at).toDateString() === today
                ).length;

                const pendingRequests = requests.filter(r => r.status === 'pending').length;
                
                // Get current user from global user system
                const currentUser = window.GlobalUser.getUser();
                const myPendingRequests = requests.filter(r => 
                    r.status === 'pending' && 
                    r.user_id === currentUser?.id
                ).length;

                return {
                    total_functions: functions.length,
                    total_users: users.length,
                    pending_requests: pendingRequests,
                    completed_requests_today: completedToday,
                    my_pending_requests: myPendingRequests
                };
            }
        },

        // Load recent functions
        async loadRecentFunctions() {
            const functions = await window.apiClient.getFunctions();
            // Sort by creation date, newest first
            return functions.sort((a, b) => 
                new Date(b.created_at) - new Date(a.created_at)
            );
        },

        // Load recent requests
        async loadRecentRequests() {
            const requests = await window.apiClient.getRequests();
            // Sort by creation date, newest first
            return requests.sort((a, b) => 
                new Date(b.created_at) - new Date(a.created_at)
            );
        },

        // Refresh dashboard data
        async refresh() {
            await this.loadDashboardData();
        },

        // Navigate to functions page
        goToFunctions() {
            window.GlobalNav.loadPage('functions');
        },

        // Navigate to users page
        goToUsers() {
            window.GlobalNav.loadPage('users');
        },

        // Navigate to requests page
        goToRequests() {
            window.GlobalNav.loadPage('requests');
        },

        // Execute a function quickly
        async executeFunction(functionItem) {
            try {
                const result = await window.apiClient.executeFunction(functionItem.id, {});
                
                if (result.status === 'pending') {
                    window.GlobalAlert.show('Request submitted for approval', 'info');
                } else {
                    window.GlobalAlert.show('Function executed successfully!', 'success');
                }
                
                // Refresh stats
                await this.loadStats();
                
            } catch (error) {
                window.GlobalAlert.show(error.message || 'Execution failed', 'error');
            }
        },

        // Format numbers for display
        formatNumber(num) {
            if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'k';
            }
            return num.toString();
        },

        // Get stat card icon
        getStatIcon(type) {
            const icons = {
                functions: '⚙️',
                users: '👥',
                pending: '⏳',
                completed: '✅',
                my_pending: '📋'
            };
            return icons[type] || '📊';
        },

        // Get stat card color
        getStatColor(type) {
            const colors = {
                functions: 'bg-blue-500',
                users: 'bg-green-500',
                pending: 'bg-yellow-500',
                completed: 'bg-purple-500',
                my_pending: 'bg-indigo-500'
            };
            return colors[type] || 'bg-gray-500';
        },

        // Get method badge class (delegate to utility)
        getMethodBadgeClass(method) {
            return window.ApiUtils.getMethodBadgeClass(method);
        },

        // Get status badge class (delegate to utility)  
        getStatusBadgeClass(status) {
            return window.ApiUtils.getStatusBadgeClass(status);
        },

        // Check if user can execute function
        canExecuteFunction(func) {
            return func.can_execute !== false;
        },

        // Format date (delegate to utility)
        formatDate(dateString) {
            return window.ApiUtils.formatDate(dateString);
        }
    }
}

// Make component globally available
window.dashboardPage = dashboardPage;
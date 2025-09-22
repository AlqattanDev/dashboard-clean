/**
 * Shared API utilities for the Operations Dashboard
 * Handles authentication, error handling, and common API patterns
 */

class ApiClient {
    constructor() {
        this.baseURL = '/api/v1';
        this.token = localStorage.getItem('token');
    }

    // Get auth headers
    getHeaders(contentType = 'application/json') {
        // Always get fresh token from localStorage
        this.token = localStorage.getItem('token');
        
        const headers = {
            'Content-Type': contentType
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    // Update token
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('token', token);
        } else {
            localStorage.removeItem('token');
        }
    }

    // Handle API response
    async handleResponse(response) {
        if (response.status === 401) {
            this.setToken(null);
            throw new Error('Not authenticated');
        }

        if (response.status === 403) {
            throw new Error('Access forbidden');
        }

        let data;
        try {
            data = await response.json();
        } catch (e) {
            // Handle non-JSON responses
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return {};
        }
        
        if (!response.ok) {
            throw new Error(data.detail || data.message || `HTTP ${response.status}`);
        }
        
        return data;
    }

    // Generic API request
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);
            return await this.handleResponse(response);
        } catch (error) {
            console.error(`API Error [${options.method || 'GET'}] ${endpoint}:`, error);
            throw error;
        }
    }

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Authentication endpoints
    async login(username, password) {
        const data = await this.post('/auth/login', { username, password });
        this.setToken(data.access_token);
        return data;
    }

    async logout() {
        try {
            await this.post('/auth/logout', {});
        } catch (error) {
            // Ignore logout errors
        } finally {
            this.setToken(null);
        }
    }

    async getCurrentUser() {
        return this.get('/auth/me');
    }

    // Users endpoints
    async getUsers() {
        return this.get('/users/');
    }

    async getUser(userId) {
        return this.get(`/users/${userId}`);
    }

    async createUser(userData) {
        return this.post('/users/', userData);
    }

    async updateUser(userId, userData) {
        return this.put(`/users/${userId}`, userData);
    }

    async deleteUser(userId) {
        return this.delete(`/users/${userId}`);
    }

    // Functions endpoints
    async getFunctions() {
        return this.get('/functions/');
    }

    async getFunction(functionId) {
        return this.get(`/functions/${functionId}`);
    }

    async createFunction(functionData) {
        return this.post('/functions/', functionData);
    }

    async updateFunction(functionId, functionData) {
        return this.put(`/functions/${functionId}`, functionData);
    }

    async deleteFunction(functionId) {
        return this.delete(`/functions/${functionId}`);
    }

    async executeFunction(functionId, parameters = {}) {
        return this.post(`/functions/${functionId}/execute`, { parameters });
    }

    // Requests endpoints
    async getRequests() {
        return this.get('/requests/');
    }

    async getRequest(requestId) {
        return this.get(`/requests/${requestId}`);
    }

    async approveRequest(requestId) {
        return this.post(`/requests/${requestId}/approve`, {});
    }

    async rejectRequest(requestId, reason) {
        return this.post(`/requests/${requestId}/reject`, { 
            request_id: requestId, 
            reason 
        });
    }

    async cancelRequest(requestId) {
        return this.delete(`/requests/${requestId}`);
    }

    // Dashboard stats
    async getDashboardStats() {
        try {
            return await this.get('/dashboard/stats');
        } catch (error) {
            // Fallback stats if endpoint doesn't exist
            return {
                total_functions: 0,
                total_users: 0,
                pending_requests: 0,
                completed_requests_today: 0,
                my_pending_requests: 0
            };
        }
    }
}

// Create global API client instance
window.apiClient = new ApiClient();

// Utility functions for common patterns
window.ApiUtils = {
    // Show loading state
    setLoading(element, loading = true) {
        if (loading) {
            element.classList.add('opacity-50', 'pointer-events-none');
        } else {
            element.classList.remove('opacity-50', 'pointer-events-none');
        }
    },

    // Debounce function for search
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Format date for display
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Format duration
    formatDuration(ms) {
        if (!ms) return 'N/A';
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(2)}s`;
    },

    // Get role badge class
    getRoleBadgeClass(role) {
        const classes = {
            admin: 'bg-red-100 text-red-800',
            leader: 'bg-blue-100 text-blue-800',
            member: 'bg-green-100 text-green-800'
        };
        return classes[role] || 'bg-gray-100 text-gray-800';
    },

    // Get status badge class
    getStatusBadgeClass(status) {
        const classes = {
            pending: 'bg-yellow-100 text-yellow-800',
            approved: 'bg-blue-100 text-blue-800',
            rejected: 'bg-red-100 text-red-800',
            completed: 'bg-green-100 text-green-800',
            failed: 'bg-red-100 text-red-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    },

    // Get method badge class
    getMethodBadgeClass(method) {
        const classes = {
            GET: 'bg-green-100 text-green-800',
            POST: 'bg-blue-100 text-blue-800',
            PUT: 'bg-yellow-100 text-yellow-800',
            DELETE: 'bg-red-100 text-red-800',
            PATCH: 'bg-purple-100 text-purple-800'
        };
        return classes[method] || 'bg-gray-100 text-gray-800';
    }
};
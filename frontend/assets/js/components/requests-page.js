/**
 * Requests Page Component
 * Manages request viewing, approval, and rejection
 */

function requestsPage() {
    return {
        // Component state
        loading: true,
        requests: [],
        filteredRequests: [],
        error: null,

        // Search and filters
        searchTerm: '',
        statusFilter: '',
        dateFrom: '',
        dateTo: '',
        searchTimeout: null,

        // Pagination
        currentPage: 1,
        pageSize: 10,
        totalRequests: 0,

        // Modals (initialized to false to prevent flash)
        showDetailsModal: false,
        showRejectModal: false,
        
        // Component initialization state
        componentReady: false,

        // Selected items
        selectedRequest: null,

        // Forms
        rejectForm: {
            reason: ''
        },

        // Loading states
        approving: false,
        rejecting: false,

        // Get user role from global app (with reactivity)
        get userRole() {
            return window.GlobalUser.getUserRole();
        },
        
        // Reactive user object to trigger re-evaluation
        get currentUser() {
            return window.GlobalUser.getUser();
        },

        // Get total pages for pagination
        get totalPages() {
            return Math.ceil(this.totalRequests / this.pageSize);
        },

        // Get page numbers for pagination
        get pageNumbers() {
            const pages = [];
            const start = Math.max(1, this.currentPage - 2);
            const end = Math.min(this.totalPages, this.currentPage + 2);
            
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            return pages;
        },

        // Initialize component
        async init() {
            // Wait for authentication to be ready
            if (!window.GlobalUser.getUser()) {
                // If no user yet, set up a watcher
                const checkAuth = () => {
                    if (window.GlobalUser.getUser()) {
                        this.loadRequests();
                    } else {
                        setTimeout(checkAuth, 100);
                    }
                };
                checkAuth();
            } else {
                await this.loadRequests();
            }
        },

        // Load all requests
        async loadRequests() {
            this.loading = true;
            this.error = null;

            try {
                const response = await window.apiClient.getRequests();
                // Ensure response is always an array
                this.requests = Array.isArray(response) ? response : [];
                console.log('Loaded requests:', this.requests); // Debug log
                this.applyFilters();
            } catch (error) {
                console.error('Failed to load requests:', error);
                this.error = error.message || 'Failed to load requests';
                this.requests = []; // Ensure requests is still an array
                window.GlobalAlert.show(this.error, 'error');
            } finally {
                this.loading = false;
            }
        },

        // Apply search and filters
        applyFilters() {
            // Ensure requests is always an array
            let filtered = Array.isArray(this.requests) ? [...this.requests] : [];

            // Apply search filter
            if (this.searchTerm) {
                const term = this.searchTerm.toLowerCase();
                filtered = filtered.filter(request => {
                    // Defensive access to properties that might be undefined/null
                    const functionName = (request.function_name || '').toLowerCase();
                    const userName = (request.user_username || '').toLowerCase();
                    const rejectionReason = (request.rejection_reason || '').toLowerCase();
                    
                    return functionName.includes(term) ||
                           userName.includes(term) ||
                           rejectionReason.includes(term);
                });
            }

            // Apply status filter
            if (this.statusFilter) {
                filtered = filtered.filter(request => request.status === this.statusFilter);
            }

            // Apply date filters
            if (this.dateFrom) {
                const fromDate = new Date(this.dateFrom);
                filtered = filtered.filter(request => {
                    try {
                        return new Date(request.created_at) >= fromDate;
                    } catch (e) {
                        console.warn('Invalid date in request:', request.created_at);
                        return false;
                    }
                });
            }

            if (this.dateTo) {
                const toDate = new Date(this.dateTo);
                toDate.setHours(23, 59, 59, 999); // End of day
                filtered = filtered.filter(request => {
                    try {
                        return new Date(request.created_at) <= toDate;
                    } catch (e) {
                        console.warn('Invalid date in request:', request.created_at);
                        return false;
                    }
                });
            }

            // Sort by creation date, newest first
            filtered.sort((a, b) => {
                try {
                    return new Date(b.created_at) - new Date(a.created_at);
                } catch (e) {
                    console.warn('Error sorting requests by date:', e);
                    return 0;
                }
            });

            this.filteredRequests = filtered;
            this.totalRequests = filtered.length;
            
            // Reset to first page if current page is out of bounds
            if (this.currentPage > this.totalPages && this.totalPages > 0) {
                this.currentPage = 1;
            }
        },

        // Get requests for current page
        get paginatedRequests() {
            const start = (this.currentPage - 1) * this.pageSize;
            const end = start + this.pageSize;
            return this.filteredRequests.slice(start, end);
        },

        // Debounced search
        debounceSearch() {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.applyFilters();
            }, 300);
        },

        // Navigate to specific page
        goToPage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
            }
        },

        // Go to previous page
        previousPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
            }
        },

        // Go to next page
        nextPage() {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
            }
        },

        // Open request details modal
        openDetailsModal(request) {
            this.selectedRequest = request;
            this.showDetailsModal = true;
        },

        // Approve request
        async approveRequest(request) {
            if (this.approving) return;
            this.approving = true;

            try {
                await window.apiClient.approveRequest(request.id);
                window.GlobalAlert.show('Request approved successfully!', 'success');
                await this.loadRequests();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.approving = false;
            }
        },

        // Open reject modal
        openRejectModal(request) {
            this.selectedRequest = request;
            this.rejectForm.reason = '';
            this.showRejectModal = true;
        },

        // Reject request
        async rejectRequest() {
            if (this.rejecting || !this.selectedRequest) return;
            this.rejecting = true;

            try {
                await window.apiClient.rejectRequest(
                    this.selectedRequest.id, 
                    this.rejectForm.reason
                );
                window.GlobalAlert.show('Request rejected successfully!', 'success');
                this.showRejectModal = false;
                await this.loadRequests();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.rejecting = false;
            }
        },

        // Cancel request (user can cancel their own pending requests)
        async cancelRequest(request) {
            if (!confirm('Are you sure you want to cancel this request?')) {
                return;
            }

            try {
                await window.apiClient.cancelRequest(request.id);
                window.GlobalAlert.show('Request cancelled successfully!', 'success');
                await this.loadRequests();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            }
        },

        // Close all modals
        closeModals() {
            this.showDetailsModal = false;
            this.showRejectModal = false;
            this.selectedRequest = null;
        },

        // Check if user can approve/reject requests
        canReviewRequests() {
            const user = this.currentUser;
            return user && ['admin', 'leader'].includes(user.role);
        },

        // Check if user can cancel specific request
        canCancelRequest(request) {
            if (!request || request.status !== 'pending') return false;
            const currentUser = this.currentUser;
            if (!currentUser) return false;
            return request.user_id === currentUser.id || currentUser.role === 'admin';
        },

        // Check if user can approve specific request
        canApproveRequest(request) {
            if (!request || request.status !== 'pending') return false;
            return this.canReviewRequests();
        },

        // Check if user can reject specific request
        canRejectRequest(request) {
            if (!request || request.status !== 'pending') return false;
            return this.canReviewRequests();
        },

        // Get status badge class
        getStatusBadgeClass(status) {
            return window.ApiUtils.getStatusBadgeClass(status);
        },

        // Format date
        formatDate(dateString) {
            return window.ApiUtils.formatDate(dateString);
        },

        // Format duration
        formatDuration(ms) {
            return window.ApiUtils.formatDuration(ms);
        },

        // Get status icon
        getStatusIcon(status) {
            const icons = {
                pending: '⏳',
                approved: '✅',
                rejected: '❌',
                completed: '🎉',
                failed: '💥'
            };
            return icons[status] || '❓';
        },

        // Get request summary for display
        getRequestSummary(request) {
            const params = request.parameters;
            const paramCount = Object.keys(params).length;
            
            if (paramCount === 0) {
                return 'No parameters';
            } else if (paramCount === 1) {
                const [key, value] = Object.entries(params)[0];
                return `${key}: ${value}`;
            } else {
                return `${paramCount} parameters`;
            }
        },

        // Export requests to CSV
        exportToCSV() {
            const headers = ['Date', 'User', 'Function', 'Status', 'Reviewer', 'Reviewed At'];
            const rows = this.filteredRequests.map(request => [
                this.formatDate(request.created_at),
                request.user_username,
                request.function_name,
                request.status,
                request.reviewer_username || '',
                request.reviewed_at ? this.formatDate(request.reviewed_at) : ''
            ]);

            const csvContent = [headers, ...rows]
                .map(row => row.map(field => `"${field}"`).join(','))
                .join('\n');

            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `requests-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        },

        // Clear all filters
        clearFilters() {
            this.searchTerm = '';
            this.statusFilter = '';
            this.dateFrom = '';
            this.dateTo = '';
            this.currentPage = 1;
            this.applyFilters();
        },

        // Get filter count
        get activeFilterCount() {
            let count = 0;
            if (this.searchTerm) count++;
            if (this.statusFilter) count++;
            if (this.dateFrom) count++;
            if (this.dateTo) count++;
            return count;
        },

        // Refresh requests
        async refresh() {
            await this.loadRequests();
        }
    }
}

// Make component globally available
window.requestsPage = requestsPage;
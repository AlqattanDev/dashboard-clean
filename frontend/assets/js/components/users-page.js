/**
 * Users Page Component
 * Manages user CRUD operations and role management
 */

function usersPage() {
    return {
        // Component state
        loading: true,
        users: [],
        filteredUsers: [],
        error: null,

        // Search and filters
        searchTerm: '',
        roleFilter: '',
        statusFilter: '',
        searchTimeout: null,

        // Modals (initialized to false to prevent flash)
        showCreateModal: false,
        showEditModal: false,
        
        // Component initialization state
        componentReady: false,

        // Forms
        createForm: {
            username: '',
            email: '',
            password: '',
            full_name: '',
            role: 'member'
        },
        editForm: {},

        // Selected items
        selectedUser: null,

        // Loading states
        creating: false,
        updating: false,

        // Get user role from global app (with reactivity)
        get userRole() {
            return window.GlobalUser.getUserRole();
        },
        
        // Reactive user object to trigger re-evaluation
        get currentUser() {
            return window.GlobalUser.getUser();
        },

        // Initialize component
        async init() {
            // Wait for authentication to be ready
            if (!window.GlobalUser.getUser()) {
                // If no user yet, set up a watcher
                const checkAuth = () => {
                    if (window.GlobalUser.getUser()) {
                        this.loadUsers();
                    } else {
                        setTimeout(checkAuth, 100);
                    }
                };
                checkAuth();
            } else {
                await this.loadUsers();
            }
        },

        // Load all users
        async loadUsers() {
            this.loading = true;
            this.error = null;

            try {
                this.users = await window.apiClient.getUsers();
                this.applyFilters();
            } catch (error) {
                this.error = error.message;
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.loading = false;
            }
        },

        // Apply search and filters
        applyFilters() {
            let filtered = [...this.users];

            // Apply search filter
            if (this.searchTerm) {
                const term = this.searchTerm.toLowerCase();
                filtered = filtered.filter(user => 
                    user.username.toLowerCase().includes(term) ||
                    user.email.toLowerCase().includes(term) ||
                    (user.full_name && user.full_name.toLowerCase().includes(term))
                );
            }

            // Apply role filter
            if (this.roleFilter) {
                filtered = filtered.filter(user => user.role === this.roleFilter);
            }

            // Apply status filter
            if (this.statusFilter) {
                const isActive = this.statusFilter === 'active';
                filtered = filtered.filter(user => user.is_active === isActive);
            }

            this.filteredUsers = filtered;
        },

        // Debounced search
        debounceSearch() {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.applyFilters();
            }, 300);
        },

        // Open create modal
        openCreateModal() {
            this.createForm = {
                username: '',
                email: '',
                password: '',
                full_name: '',
                role: 'member'
            };
            this.showCreateModal = true;
        },

        // Create user
        async createUser() {
            if (this.creating) return;
            this.creating = true;

            try {
                await window.apiClient.createUser(this.createForm);
                window.GlobalAlert.show('User created successfully!', 'success');
                this.showCreateModal = false;
                await this.loadUsers();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.creating = false;
            }
        },

        // Open edit modal
        openEditModal(user) {
            this.editForm = { 
                ...user,
                password: '' // Don't pre-fill password
            };
            this.selectedUser = user;
            this.showEditModal = true;
        },

        // Update user
        async updateUser() {
            if (this.updating) return;
            this.updating = true;

            try {
                // Don't send empty password
                const updateData = { ...this.editForm };
                if (!updateData.password) {
                    delete updateData.password;
                }

                await window.apiClient.updateUser(this.editForm.id, updateData);
                window.GlobalAlert.show('User updated successfully!', 'success');
                this.showEditModal = false;
                await this.loadUsers();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.updating = false;
            }
        },

        // Delete user
        async deleteUser(user) {
            if (!confirm(`Are you sure you want to delete user "${user.username}"?`)) {
                return;
            }

            try {
                await window.apiClient.deleteUser(user.id);
                window.GlobalAlert.show('User deleted successfully!', 'success');
                await this.loadUsers();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            }
        },

        // Toggle user status
        async toggleUserStatus(user) {
            try {
                const updatedUser = {
                    ...user,
                    is_active: !user.is_active
                };

                await window.apiClient.updateUser(user.id, updatedUser);
                
                const action = updatedUser.is_active ? 'activated' : 'deactivated';
                window.GlobalAlert.show(`User ${action} successfully!`, 'success');
                
                await this.loadUsers();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            }
        },

        // Close all modals
        closeModals() {
            this.showCreateModal = false;
            this.showEditModal = false;
            this.selectedUser = null;
        },

        // Check if user can manage users
        canManageUsers() {
            // Force re-evaluation by accessing currentUser
            const user = this.currentUser;
            return user && user.role === 'admin';
        },

        // Check if user can edit specific user
        canEditUser(user) {
            const currentUser = this.currentUser;
            if (!currentUser) return false;
            
            if (currentUser.role === 'admin') return true;
            if (currentUser.role === 'leader' && user.role === 'member') return true;
            return user.id === currentUser.id; // Users can edit themselves
        },

        // Check if user can delete specific user
        canDeleteUser(user) {
            const currentUser = this.currentUser;
            if (!currentUser || currentUser.role !== 'admin') return false;
            return user.id !== currentUser.id; // Can't delete yourself
        },

        // Get available roles for current user
        getAvailableRoles() {
            const currentUser = this.currentUser;
            if (!currentUser) return [];
            
            if (currentUser.role === 'admin') {
                return ['admin', 'leader', 'member'];
            } else if (currentUser.role === 'leader') {
                return ['member'];
            }
            return [];
        },

        // Check if role option should be disabled
        isRoleDisabled(role) {
            const availableRoles = this.getAvailableRoles();
            return !availableRoles.includes(role);
        },

        // Get role badge class
        getRoleBadgeClass(role) {
            return window.ApiUtils.getRoleBadgeClass(role);
        },

        // Get status badge class
        getStatusBadgeClass(isActive) {
            return isActive 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800';
        },

        // Format date
        formatDate(dateString) {
            return window.ApiUtils.formatDate(dateString);
        },

        // Get user avatar initials
        getUserInitials(user) {
            if (user.full_name) {
                return user.full_name.split(' ')
                    .map(name => name.charAt(0))
                    .join('')
                    .toUpperCase()
                    .slice(0, 2);
            }
            return user.username.charAt(0).toUpperCase();
        },

        // Validate create form
        isCreateFormValid() {
            return this.createForm.username && 
                   this.createForm.email && 
                   this.createForm.password &&
                   this.createForm.role;
        },

        // Validate edit form
        isEditFormValid() {
            return this.editForm.username && 
                   this.editForm.email && 
                   this.editForm.role;
        },

        // Get role description
        getRoleDescription(role) {
            const descriptions = {
                admin: 'Full system access and user management',
                leader: 'Can manage members and approve requests',
                member: 'Basic user with limited permissions'
            };
            return descriptions[role] || '';
        },

        // Sort users by different criteria
        sortUsers(criteria) {
            let sorted = [...this.filteredUsers];
            
            switch (criteria) {
                case 'username':
                    sorted.sort((a, b) => a.username.localeCompare(b.username));
                    break;
                case 'role':
                    const roleOrder = { admin: 0, leader: 1, member: 2 };
                    sorted.sort((a, b) => roleOrder[a.role] - roleOrder[b.role]);
                    break;
                case 'created':
                    sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                    break;
                case 'status':
                    sorted.sort((a, b) => b.is_active - a.is_active);
                    break;
                default:
                    break;
            }
            
            this.filteredUsers = sorted;
        }
    }
}

// Make component globally available
window.usersPage = usersPage;
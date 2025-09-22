/**
 * Functions Page Component
 * Manages function CRUD operations and execution
 */

function functionsPage() {
    return {
        // Component state
        loading: true,
        functions: [],
        filteredFunctions: [],
        error: null,

        // Search and filters
        searchTerm: '',
        roleFilter: '',
        methodFilter: '',
        searchTimeout: null,

        // Modals (initialized to false to prevent flash)
        showCreateModal: false,
        showEditModal: false,
        showExecuteModal: false,
        
        // Component initialization state
        componentReady: false,

        // Forms
        createForm: {
            name: '',
            description: '',
            api_endpoint: '',
            http_method: 'POST',
            min_role: 'member',
            timeout: 30,
            required_fields: [],
            url_parameters: [],
            request_headers: {}
        },
        editForm: {},
        executeForm: {
            parameters: {}
        },

        // Selected items
        selectedFunction: null,

        // Loading states
        creating: false,
        updating: false,
        executing: false,

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
            // Set component as ready to prevent modal flashes
            this.componentReady = true;
            
            // Wait for authentication to be ready
            if (!window.GlobalUser.getUser()) {
                // If no user yet, set up a watcher
                const checkAuth = () => {
                    if (window.GlobalUser.getUser()) {
                        this.loadFunctions();
                    } else {
                        setTimeout(checkAuth, 100);
                    }
                };
                checkAuth();
            } else {
                await this.loadFunctions();
            }
        },

        // Load all functions
        async loadFunctions() {
            this.loading = true;
            this.error = null;

            try {
                this.functions = await window.apiClient.getFunctions();
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
            let filtered = [...this.functions];

            // Apply search filter
            if (this.searchTerm) {
                const term = this.searchTerm.toLowerCase();
                filtered = filtered.filter(fn => 
                    fn.name.toLowerCase().includes(term) ||
                    fn.description.toLowerCase().includes(term) ||
                    fn.api_endpoint.toLowerCase().includes(term)
                );
            }

            // Apply role filter
            if (this.roleFilter) {
                filtered = filtered.filter(fn => fn.min_role === this.roleFilter);
            }

            // Apply method filter
            if (this.methodFilter) {
                filtered = filtered.filter(fn => fn.http_method === this.methodFilter);
            }

            this.filteredFunctions = filtered;
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
                name: '',
                description: '',
                api_endpoint: '',
                http_method: 'POST',
                min_role: 'member',
                timeout: 30,
                required_fields: [],
                url_parameters: [],
                request_headers: {}
            };
            this.showCreateModal = true;
        },

        // Create function
        async createFunction() {
            if (this.creating) return;
            this.creating = true;

            try {
                await window.apiClient.createFunction(this.createForm);
                window.GlobalAlert.show('Function created successfully!', 'success');
                this.showCreateModal = false;
                await this.loadFunctions();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.creating = false;
            }
        },

        // Open edit modal
        openEditModal(functionItem) {
            this.editForm = { 
                ...functionItem,
                // Ensure required_fields is properly initialized as an array
                required_fields: Array.isArray(functionItem.required_fields) 
                    ? [...functionItem.required_fields] 
                    : []
            };
            this.selectedFunction = functionItem;
            this.showEditModal = true;
        },

        // Update function
        async updateFunction() {
            if (this.updating) return;
            this.updating = true;

            try {
                await window.apiClient.updateFunction(this.editForm.id, this.editForm);
                window.GlobalAlert.show('Function updated successfully!', 'success');
                this.showEditModal = false;
                await this.loadFunctions();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.updating = false;
            }
        },

        // Delete function
        async deleteFunction(functionItem) {
            if (!confirm(`Are you sure you want to delete "${functionItem.name}"?`)) {
                return;
            }

            try {
                await window.apiClient.deleteFunction(functionItem.id);
                window.GlobalAlert.show('Function deleted successfully!', 'success');
                await this.loadFunctions();
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            }
        },

        // Open execute modal
        openExecuteModal(functionItem) {
            this.selectedFunction = functionItem;
            this.executeForm = { parameters: {} };
            
            // Initialize parameters based on required fields
            if (functionItem.required_fields) {
                functionItem.required_fields.forEach(field => {
                    this.executeForm.parameters[field.name] = '';
                });
            }
            
            this.showExecuteModal = true;
        },

        // Execute function
        async executeFunction() {
            if (this.executing || !this.selectedFunction) return;
            this.executing = true;

            try {
                const result = await window.apiClient.executeFunction(
                    this.selectedFunction.id, 
                    this.executeForm.parameters
                );

                if (result.status === 'pending') {
                    window.GlobalAlert.show('Request submitted for approval', 'info');
                } else {
                    window.GlobalAlert.show('Function executed successfully!', 'success');
                }

                this.showExecuteModal = false;
            } catch (error) {
                window.GlobalAlert.show(error.message, 'error');
            } finally {
                this.executing = false;
            }
        },

        // Close all modals
        closeModals() {
            this.showCreateModal = false;
            this.showEditModal = false;
            this.showExecuteModal = false;
            this.selectedFunction = null;
        },

        // Check if user can execute function
        canExecuteFunction(functionItem) {
            return functionItem.can_execute !== false;
        },

        // Check if user can edit functions (admin only)
        canEditFunctions() {
            // Force re-evaluation by accessing currentUser
            const user = this.currentUser;
            return user && user.role === 'admin';
        },

        // Get role badge class
        getRoleBadgeClass(role) {
            return window.ApiUtils.getRoleBadgeClass(role);
        },

        // Get method badge class
        getMethodBadgeClass(method) {
            return window.ApiUtils.getMethodBadgeClass(method);
        },

        // Format date
        formatDate(dateString) {
            return window.ApiUtils.formatDate(dateString);
        },

        // Get parameter input type
        getParameterType(fieldType) {
            const typeMap = {
                'string': 'text',
                'number': 'number',
                'boolean': 'checkbox',
                'email': 'email',
                'url': 'url',
                'password': 'password'
            };
            return typeMap[fieldType] || 'text';
        },

        // Validate form
        isFormValid(form) {
            return form.name && form.description && form.api_endpoint;
        },

        // Add required field (for create/edit forms)
        addRequiredField() {
            if (!Array.isArray(this.createForm.required_fields)) {
                this.createForm.required_fields = [];
            }
            this.createForm.required_fields.push({
                name: '',
                type: 'string',
                required: true,
                description: ''
            });
        },

        // Remove required field
        removeRequiredField(index) {
            this.createForm.required_fields.splice(index, 1);
        },

        // Add URL parameter
        addUrlParameter() {
            if (!Array.isArray(this.createForm.url_parameters)) {
                this.createForm.url_parameters = [];
            }
            this.createForm.url_parameters.push('');
        },

        // Remove URL parameter
        removeUrlParameter(index) {
            this.createForm.url_parameters.splice(index, 1);
        },

        // Add required field for edit form
        addRequiredFieldToEdit() {
            if (!Array.isArray(this.editForm.required_fields)) {
                this.editForm.required_fields = [];
            }
            this.editForm.required_fields.push({
                name: '',
                type: 'string',
                required: true,
                description: ''
            });
        },

        // Remove required field from edit form
        removeRequiredFieldFromEdit(index) {
            if (Array.isArray(this.editForm.required_fields)) {
                this.editForm.required_fields.splice(index, 1);
            }
        }
    }
}

// Make component globally available
window.functionsPage = functionsPage;
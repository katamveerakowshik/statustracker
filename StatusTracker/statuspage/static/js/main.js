document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather Icons
    feather.replace();
    
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarClose = document.getElementById('sidebar-close');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    if (sidebarClose && sidebar) {
        sidebarClose.addEventListener('click', function() {
            sidebar.classList.remove('show');
        });
    }
    
    // Organization switcher
    const orgSwitcherButton = document.getElementById('org-switcher-button');
    const orgMenu = document.getElementById('org-menu');
    
    if (orgSwitcherButton && orgMenu) {
        orgSwitcherButton.addEventListener('click', function() {
            orgMenu.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!orgSwitcherButton.contains(event.target) && !orgMenu.contains(event.target)) {
                orgMenu.classList.remove('show');
            }
        });
        
        // Handle organization selection
        const orgItems = document.querySelectorAll('.organization-menu-item[data-org-id]');
        orgItems.forEach(function(item) {
            item.addEventListener('click', function() {
                const orgId = this.getAttribute('data-org-id');
                
                fetch(`/organizations/set-current/${orgId}/`, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        window.location.reload();
                    }
                });
            });
        });
    }
    
    // Form field enhancements
    // Auto-slugify organization name when creating a new organization
    const nameField = document.getElementById('id_name');
    const slugField = document.getElementById('id_slug');
    
    if (nameField && slugField && !slugField.value) {
        nameField.addEventListener('input', function() {
            slugField.value = generateSlug(nameField.value);
        });
    }
    
    // Toggle maintenance fields based on incident type
    const typeField = document.getElementById('id_type');
    const maintenanceFields = document.querySelector('.maintenance-fields');
    
    if (typeField && maintenanceFields) {
        function toggleMaintenanceFields() {
            if (typeField.value === 'maintenance') {
                maintenanceFields.style.display = 'block';
            } else {
                maintenanceFields.style.display = 'none';
            }
        }
        
        // Initialize
        toggleMaintenanceFields();
        
        // Add change event listener
        typeField.addEventListener('change', toggleMaintenanceFields);
    }
});

// Helper function to generate a slug from text
function generateSlug(text) {
    return text.toLowerCase()
        .replace(/[^\w ]+/g, '')
        .replace(/ +/g, '-');
}

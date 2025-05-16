/**
 * Sets up WebSocket connection for real-time status updates
 * @param {string} organizationId - The ID of the current organization
 */
function setupStatusUpdates(organizationId) {
    if (!organizationId) {
        console.error('No organization ID provided for WebSocket connection');
        return;
    }
    
    // Determine WebSocket protocol based on page protocol (secure or not)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/status-updates/?organization_id=${organizationId}`;
    
    console.log(`Connecting to WebSocket at ${wsUrl}`);
    
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = function(e) {
        console.log('WebSocket connection established');
    };
    
    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('WebSocket message received:', data);
        
        // Update service statuses
        if (data.services) {
            updateServiceStatuses(data.services);
        }
        
        // Update incident list
        if (data.incidents) {
            updateIncidents(data.incidents);
        }
        
        // Update last updated timestamp
        const lastUpdated = document.querySelector('#last-updated');
        if (lastUpdated) {
            lastUpdated.textContent = new Date().toLocaleString();
        }
    };
    
    socket.onclose = function(e) {
        console.log('WebSocket connection closed');
        
        // Try to reconnect after a delay
        setTimeout(function() {
            console.log('Attempting to reconnect WebSocket...');
            setupStatusUpdates(organizationId);
        }, 5000);
    };
    
    socket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };
}

/**
 * Updates service status indicators in the UI
 * @param {Array} services - Array of service objects with updated status
 */
function updateServiceStatuses(services) {
    if (!services || !services.length) return;
    
    services.forEach(service => {
        // Find service elements in the DOM
        const serviceElements = document.querySelectorAll(`[data-service-id="${service.id}"]`);
        
        serviceElements.forEach(element => {
            // Update status badge
            const statusBadge = element.querySelector('.status-badge');
            if (statusBadge) {
                // Remove old status classes
                statusBadge.classList.remove('status-operational', 'status-degraded', 'status-partial_outage', 'status-major_outage');
                
                // Add new status class
                statusBadge.classList.add(`status-${service.status}`);
                
                // Update text
                statusBadge.textContent = service.status_display;
            }
        });
    });
    
    // Update system status indicator
    updateSystemStatus(services);
}

/**
 * Updates the incidents list in the UI
 * @param {Array} incidents - Array of incident objects 
 */
function updateIncidents(incidents) {
    if (!incidents) return;
    
    const activeIncidentsContainer = document.querySelector('#active-incidents');
    if (!activeIncidentsContainer) return;
    
    // Get current incident IDs
    const currentIncidentIds = Array.from(
        activeIncidentsContainer.querySelectorAll('[data-incident-id]')
    ).map(el => parseInt(el.dataset.incidentId));
    
    const newIncidentIds = incidents.map(incident => incident.id);
    
    // Update existing incidents
    incidents.forEach(incident => {
        const incidentElement = document.querySelector(`[data-incident-id="${incident.id}"]`);
        if (incidentElement) {
            // Update status badge
            const statusBadge = incidentElement.querySelector('.status-badge');
            if (statusBadge) {
                // Remove old status classes
                statusBadge.classList.remove(
                    'status-investigating', 'status-identified', 'status-monitoring',
                    'status-resolved', 'status-scheduled', 'status-in_progress',
                    'status-completed'
                );
                
                // Add new status class
                statusBadge.classList.add(`status-${incident.status}`);
                
                // Update text
                statusBadge.textContent = incident.status_display;
            }
            
            // Update affected services
            const servicesContainer = incidentElement.querySelector('.affected-services');
            if (servicesContainer) {
                servicesContainer.innerHTML = incident.services.map(service => 
                    `<span class="badge bg-light text-dark me-1" data-service-id="${service.id}">${service.name}</span>`
                ).join('');
            }
        }
    });
    
    // If there are new incidents or removed incidents, update the container
    if (!arraysEqual(currentIncidentIds, newIncidentIds)) {
        // Create new incident elements
        const newIncidents = incidents.filter(incident => !currentIncidentIds.includes(incident.id));
        const removedIncidents = currentIncidentIds.filter(id => !newIncidentIds.includes(id));
        
        // Remove resolved incidents
        removedIncidents.forEach(id => {
            const element = document.querySelector(`[data-incident-id="${id}"]`);
            if (element) {
                element.remove();
            }
        });
        
        // Add new incidents
        if (newIncidents.length > 0) {
            const listGroup = activeIncidentsContainer.querySelector('.list-group') || 
                            document.createElement('div');
            if (!listGroup.classList.contains('list-group')) {
                listGroup.classList.add('list-group');
            }
            
            newIncidents.forEach(incident => {
                const incidentHtml = `
                    <div class="list-group-item" data-incident-id="${incident.id}">
                        <div class="d-flex w-100 justify-content-between align-items-center">
                            <h6 class="mb-1">${incident.title}</h6>
                            <span class="status-badge status-${incident.status}">${incident.status_display}</span>
                        </div>
                        <p class="mb-1">${incident.description || ''}</p>
                        <div class="d-flex justify-content-between">
                            <small class="text-muted affected-services">
                                ${incident.services.map(service => 
                                    `<span class="badge bg-light text-dark me-1" data-service-id="${service.id}">${service.name}</span>`
                                ).join('')}
                            </small>
                            <small class="text-muted">${new Date(incident.created_at).toLocaleString()}</small>
                        </div>
                    </div>
                `;
                listGroup.insertAdjacentHTML('beforeend', incidentHtml);
            });
            
            if (!activeIncidentsContainer.contains(listGroup)) {
                activeIncidentsContainer.appendChild(listGroup);
            }
        }
        
        // Update empty state message
        const emptyState = activeIncidentsContainer.querySelector('.text-center');
        if (emptyState) {
            emptyState.style.display = incidents.length === 0 ? 'block' : 'none';
        }
    }
}

/**
 * Updates the system status indicator based on service statuses
 * @param {Array} services - Array of service objects
 */
function updateSystemStatus(services) {
    const systemStatusElement = document.querySelector('.system-status');
    if (!systemStatusElement) return;
    
    // Find the most severe status
    const statusOrder = {
        'operational': 0,
        'degraded': 1,
        'partial_outage': 2,
        'major_outage': 3
    };
    
    let maxSeverity = 0;
    let worstStatus = 'operational';
    
    services.forEach(service => {
        const severity = statusOrder[service.status] || 0;
        if (severity > maxSeverity) {
            maxSeverity = severity;
            worstStatus = service.status;
        }
    });
    
    // Update the system status
    systemStatusElement.className = `system-status ${worstStatus}`;
    const statusIcon = systemStatusElement.querySelector('.status-icon');
    if (statusIcon) {
        statusIcon.className = 'status-icon';
    }
    
    // Update the status text
    const statusText = {
        'operational': 'All Systems Operational',
        'degraded': 'Degraded System Performance',
        'partial_outage': 'Partial System Outage',
        'major_outage': 'Major System Outage'
    }[worstStatus] || 'All Systems Operational';
    
    systemStatusElement.innerHTML = `
        <div class="status-icon"></div>
        ${statusText}
    `;
}

/**
 * Helper function to compare arrays
 */
function arraysEqual(a, b) {
    if (a.length !== b.length) return false;
    const sortedA = [...a].sort();
    const sortedB = [...b].sort();
    return sortedA.every((val, idx) => val === sortedB[idx]);
}

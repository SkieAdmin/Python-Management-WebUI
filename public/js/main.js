// main.js - ES6 Module for Python Project Manager
'use strict';

// Project management functionality
class ProjectManager {
  constructor() {
    this.initEventListeners();
  }

  initEventListeners() {
    // Handle run command modal
    const runCommandModal = document.getElementById('runCommandModal');
    if (runCommandModal) {
      runCommandModal.addEventListener('show.bs.modal', event => {
        const button = event.relatedTarget;
        const projectName = button.getAttribute('data-project-name');
        const form = runCommandModal.querySelector('#runCommandForm');
        
        if (projectName && form) {
          form.action = `/projects/run-command/${projectName}`;
        }
      });
    }

    // Handle command form submission with AJAX
    const commandForm = document.getElementById('runCommandForm');
    if (commandForm) {
      commandForm.addEventListener('submit', this.handleCommandSubmit.bind(this));
    }

    // Handle project status toggle
    const statusToggles = document.querySelectorAll('.status-toggle');
    statusToggles.forEach(toggle => {
      toggle.addEventListener('change', this.handleStatusToggle.bind(this));
    });
  }

  handleCommandSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const commandOutput = document.getElementById('commandOutput');
    const outputPre = commandOutput.querySelector('pre');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Running...';
    
    fetch(form.action, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command: formData.get('command')
      })
    })
    .then(response => response.json())
    .then(data => {
      commandOutput.classList.remove('d-none');
      outputPre.textContent = data.output;
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fas fa-play me-1"></i>Run Command';
    })
    .catch(error => {
      commandOutput.classList.remove('d-none');
      outputPre.textContent = 'Error: ' + error.message;
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fas fa-play me-1"></i>Run Command';
    });
  }

  handleStatusToggle(event) {
    const toggle = event.target;
    const projectName = toggle.getAttribute('data-project-name');
    const status = toggle.checked ? 'Active' : 'Inactive';
    
    fetch(`/projects/toggle-status/${projectName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status })
    })
    .then(response => {
      if (response.ok) {
        // Update UI to reflect new status
        const statusBadge = document.querySelector(`#project-${projectName} .status-badge`);
        if (statusBadge) {
          statusBadge.className = `status-badge badge ${status === 'Active' ? 'bg-success' : 'bg-secondary'}`;
          statusBadge.textContent = status;
        }
      } else {
        // Revert toggle if there was an error
        toggle.checked = !toggle.checked;
        alert('Failed to update project status');
      }
    })
    .catch(error => {
      console.error('Error updating status:', error);
      toggle.checked = !toggle.checked;
      alert('Failed to update project status');
    });
  }
}

// Socket.io functionality for real-time logs
class LogManager {
  constructor() {
    this.socket = null;
    this.logOutput = document.getElementById('logOutput');
    
    if (this.logOutput) {
      this.initSocket();
    }
  }

  initSocket() {
    // Get project name from the URL
    const pathParts = window.location.pathname.split('/');
    const projectName = pathParts[pathParts.length - 1];
    
    if (!projectName) return;
    
    // Connect to socket.io
    this.socket = io();
    
    // Join project-specific room
    this.socket.emit('join', projectName);
    
    // Listen for log updates
    this.socket.on('log', (logEntry) => {
      this.appendLogEntry(logEntry);
    });
  }

  appendLogEntry(logEntry) {
    if (!this.logOutput) return;
    
    const logEntryDiv = document.createElement('div');
    logEntryDiv.className = `log-entry mb-2 ${logEntry.type === 'stderr' ? 'text-danger' : (logEntry.type === 'system' ? 'text-warning' : '')}`;
    
    const timestamp = document.createElement('small');
    timestamp.className = 'text-muted';
    timestamp.textContent = `[${new Date(logEntry.timestamp).toLocaleString()}]`;
    
    const pre = document.createElement('pre');
    pre.className = 'mb-0';
    pre.style.whiteSpace = 'pre-wrap';
    pre.textContent = logEntry.message;
    
    logEntryDiv.appendChild(timestamp);
    logEntryDiv.appendChild(pre);
    
    this.logOutput.appendChild(logEntryDiv);
    
    // Auto-scroll to bottom
    this.logOutput.scrollTop = this.logOutput.scrollHeight;
  }
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize project manager
  const projectManager = new ProjectManager();
  
  // Initialize log manager for real-time logs
  const logManager = new LogManager();
  
  // Auto-scroll to bottom of logs
  const logOutput = document.getElementById('logOutput');
  if (logOutput) {
    logOutput.scrollTop = logOutput.scrollHeight;
  }
});

// Export classes for potential reuse
export { ProjectManager, LogManager };

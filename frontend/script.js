// ===============================
// Judicial File Backup System JS
// ===============================

const BACKEND_URL = 'http://localhost:5000'; // <-- Your Flask backend

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadBackups(); // Load backups on page load
});

// ===============================
// INITIALIZATION
// ===============================
function initializeApp() {
    initializeFileUpload();
    initializeSearch();
    initializeModals();
    initializeSidebar();
    initializePendingRegistrations();
}

// ===============================
// CASE ACTIONS
// ===============================
function viewCase(id) {
    showNotification(`Viewing case ${id}`, 'info');
}

function editCase(id) {
    showNotification(`Editing case ${id}`, 'info');
}

function deleteCase(id) {
    if (confirm('Are you sure you want to delete this case?')) {
        showNotification(`Case ${id} deleted successfully`, 'success');
    }
}

// ===============================
// FILE UPLOAD SYSTEM
// ===============================
function initializeFileUpload() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('file-input');

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
    }
}

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (validateFile(file)) addFileToList(file);
    });
}

function validateFile(file) {
    const validTypes = [
        'application/pdf', 'image/jpeg', 'image/png',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    const maxSize = 50 * 1024 * 1024; // 50MB

    if (!validTypes.includes(file.type)) {
        showNotification('Invalid file type. Only PDF, JPG, PNG, or DOCX allowed.', 'error');
        return false;
    }

    if (file.size > maxSize) {
        showNotification('File exceeds 50MB limit.', 'error');
        return false;
    }
    return true;
}

function addFileToList(file) {
    const fileList = document.querySelector('.file-list');
    const fileId = 'file-' + Date.now();

    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.id = fileId;
    fileItem.innerHTML = `
        <div class="file-info">
            <div class="file-icon"><i>📄</i></div>
            <div>
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
        </div>
        <div class="file-progress">
            <div class="file-progress-bar" style="width: 0%"></div>
        </div>
        <button class="btn btn-sm btn-danger" onclick="removeFile('${fileId}')">Remove</button>
    `;
    fileList.appendChild(fileItem);
    simulateUpload(fileId);
}

function simulateUpload(fileId) {
    const bar = document.querySelector(`#${fileId} .file-progress-bar`);
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            markAsUploaded(fileId);
        }
        bar.style.width = progress + '%';
    }, 200);
}

function markAsUploaded(fileId) {
    const container = document.querySelector(`#${fileId} .file-progress`);
    container.innerHTML = '<span class="badge badge-success">Uploaded</span>';
}

function removeFile(fileId) {
    document.getElementById(fileId)?.remove();
}

function formatFileSize(bytes) {
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ===============================
// SEARCH SYSTEM
// ===============================
function initializeSearch() {
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
    }
}

function performSearch() {
    const query = document.querySelector('input[type="search"]')?.value || '';
    showLoading('search-results');
    setTimeout(() => displaySearchResults(generateMockResults(query)), 1000);
}

function generateMockResults(query) {
    const allCases = [
        { id: 1, caseNumber: 'CR-2024-001', title: 'State vs. John Doe', judge: 'Justice Katanu', status: 'Active', lastUpdated: '2024-10-15', files: 5 },
        { id: 2, caseNumber: 'CM-2024-002', title: 'Commercial Dispute - ABC Corp', judge: 'Justice Mwangi', status: 'Pending', lastUpdated: '2024-10-14', files: 3 }
    ];
    return allCases.filter(c => c.title.toLowerCase().includes(query.toLowerCase()));
}

function displaySearchResults(results) {
    const container = document.getElementById('search-results');
    if (!results.length) {
        container.innerHTML = `<div class="empty-state"><i>🔍</i><h3>No results</h3><p>Try a different search</p></div>`;
        return;
    }
    container.innerHTML = results.map(r => `
        <div class="card mb-2">
            <div class="card-body d-flex justify-between align-center">
                <div>
                    <h4>${r.caseNumber} - ${r.title}</h4>
                    <p class="text-light">Judge: ${r.judge} • Files: ${r.files} • Updated: ${r.lastUpdated}</p>
                </div>
                <div class="d-flex gap-1">
                    <span class="badge ${getStatusClass(r.status)}">${r.status}</span>
                    <button class="btn btn-sm btn-outline" onclick="viewCase(${r.id})">View</button>
                </div>
            </div>
        </div>
    `).join('');
}

function getStatusClass(status) {
    const map = { Active: 'badge-success', Pending: 'badge-warning', Closed: 'badge-secondary', Archived: 'badge-info' };
    return map[status] || 'badge-secondary';
}

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) container.innerHTML = `<div class="loading">Loading...</div>`;
}

// ===============================
// MODAL SYSTEM
// ===============================
function initializeModals() {
    document.addEventListener('click', e => {
        if (e.target.classList.contains('modal')) closeModal(e.target.id);
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') document.querySelector('.modal.show')?.classList.remove('show');
    });
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
}

// ===============================
// SIDEBAR TOGGLE
// ===============================
function initializeSidebar() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => sidebar.classList.toggle('show'));
    }
}

// ===============================
// NOTIFICATION SYSTEM
// ===============================
function showNotification(message, type = 'info') {
    const note = document.createElement('div');
    note.className = `notification notification-${type}`;
    note.innerHTML = `
        <div class="notification-content">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification { position: fixed; top: 20px; right: 20px; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 1000; animation: slideIn .3s ease; }
            .notification-success { border-left: 4px solid green; }
            .notification-warning { border-left: 4px solid orange; }
            .notification-error { border-left: 4px solid red; }
            .notification-info { border-left: 4px solid #3498db; }
            .notification-content { padding: 1rem; display: flex; justify-content: space-between; align-items: center; min-width: 280px; }
            @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
        `;
        document.head.appendChild(style);
    }
    document.body.appendChild(note);
    setTimeout(() => note.remove(), 4000);
}

// ===============================
// BACKUP SYSTEM
// ===============================
async function loadBackups() {
    try {
        const response = await fetch(`${BACKEND_URL}/backup`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });
        if (!response.ok) throw new Error('Failed to fetch backups');
        const backups = await response.json();
        const tbody = document.getElementById('backupTableBody');
        tbody.innerHTML = '';
        backups.forEach(b => {
            tbody.innerHTML += `
                <tr>
                    <td>${b.created_at}</td>
                    <td>${b.backup_type}</td>
                    <td>${b.size || '-'}</td>
                    <td><span class="badge ${b.status === 'completed' ? 'badge-success' : 'badge-warning'}">${b.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline restore-btn" data-backup-id="${b.id}">Restore</button>
                    </td>
                </tr>
            `;
        });
        attachRestoreEvents();
    } catch (err) {
        console.error(err);
        showNotification('Failed to load backups', 'error');
    }
}

document.getElementById('startBackupBtn')?.addEventListener('click', async () => {
    const backupType = document.querySelector('select[name="backup_type"]').value;
    const storageLocation = document.querySelector('select[name="storage_location"]').value;

    try {
        const response = await fetch(`${BACKEND_URL}/backup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({ type: backupType, storage_location: storageLocation })
        });
        const data = await response.json();
        if (response.ok) {
            showNotification(`Backup started! ID: ${data.backup_id}`, 'success');
            loadBackups();
        } else {
            showNotification(data.error || 'Error starting backup', 'error');
        }
    } catch (err) {
        console.error(err);
        showNotification('Server error while starting backup', 'error');
    }
});

function attachRestoreEvents() {
    document.querySelectorAll('.restore-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const backupId = btn.dataset.backupId;
            try {
                const response = await fetch(`${BACKEND_URL}/backup/${backupId}/restore`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
                });
                const data = await response.json();
                if (response.ok) showNotification('Restore started!', 'success');
                else showNotification(data.error || 'Error restoring backup', 'error');
            } catch (err) {
                console.error(err);
                showNotification('Server error while restoring backup', 'error');
            }
        });
    });
}

// ===============================
// PENDING REGISTRATION SYSTEM
// ===============================
function initializePendingRegistrations() {
    if (!localStorage.getItem('pendingRegistrations')) {
        const sample = [
            { id: 1, name: 'David Kimani', email: 'd.kimani@judiciary.go.ke', role: 'Court Clerk', court: 'Nairobi High Court', applied: 'Today, 09:30 AM', status: 'Pending' },
            { id: 2, name: 'Grace Wambui', email: 'g.wambui@judiciary.go.ke', role: 'Judge', court: 'Mombasa Law Courts', applied: 'Yesterday, 02:15 PM', status: 'Pending' }
        ];
        localStorage.setItem('pendingRegistrations', JSON.stringify(sample));
    }
    refreshRegistrationUI();
}

function getRegistrations() { return JSON.parse(localStorage.getItem('pendingRegistrations')) || []; }
function updateRegistrations(data) { localStorage.setItem('pendingRegistrations', JSON.stringify(data)); }

function approveRegistration(id) {
    if (confirm('Approve this registration request?')) {
        const data = getRegistrations();
        const reg = data.find(r => r.id === id);
        if (reg) reg.status = 'Approved';
        updateRegistrations(data);
        showNotification(`${reg.name} approved successfully`, 'success');
        refreshRegistrationUI();
    }
}

function rejectRegistration(id) {
    const reason = prompt('Enter rejection reason:');
    if (reason) {
        const data = getRegistrations();
        const reg = data.find(r => r.id === id);
        if (reg) reg.status = 'Rejected';
        updateRegistrations(data);
        showNotification(`${reg.name} rejected. Reason: ${reason}`, 'warning');
        refreshRegistrationUI();
    }
}

function viewApplication(id) {
    const reg = getRegistrations().find(r => r.id === id);
    if (reg) {
        alert(`📋 Application Details
-------------------------
Name: ${reg.name}
Email: ${reg.email}
Role: ${reg.role}
Court: ${reg.court}
Applied: ${reg.applied}
Status: ${reg.status}`);
    }
}

function refreshRegistrationUI() {
    const table = document.querySelector('.card table tbody');
    if (!table) return;
    const data = getRegistrations();
    table.innerHTML = data
        .filter(r => r.status === 'Pending')
        .map(r => `
        <tr>
            <td>${r.name}</td>
            <td>${r.email}</td>
            <td>${r.role}</td>
            <td>${r.court}</td>
            <td>${r.applied}</td>
            <td>
                <div class="d-flex gap-1">
                    <button class="btn btn-sm btn-success" onclick="approveRegistration(${r.id})">Approve</button>
                    <button class="btn btn-sm btn-danger" onclick="rejectRegistration(${r.id})">Reject</button>
                    <button class="btn btn-sm btn-outline" onclick="viewApplication(${r.id})">View</button>
                </div>
            </td>
        </tr>
    `).join('');
}

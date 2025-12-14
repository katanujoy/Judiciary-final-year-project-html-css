/* =====================================================
   CONFIGURATION
===================================================== */
const BACKEND_URL = 'http://127.0.0.1:5000/api';
const FRONTEND_URL = 'http://127.0.0.1:5500';
const TOKEN_KEY = 'judiciary_auth_token';
const USER_KEY = 'judiciary_user';

/* =====================================================
   API ENDPOINTS
===================================================== */
const API = {
    login: `${BACKEND_URL}/auth/login`,
    register: `${BACKEND_URL}/auth/register`,
    logout: `${BACKEND_URL}/auth/logout`,
    me: `${BACKEND_URL}/auth/me`,
    changePassword: `${BACKEND_URL}/auth/change-password`,

    uploadFile: `${BACKEND_URL}/files/upload`,

    backup: `${BACKEND_URL}/backup`,
    restoreBackup: id => `${BACKEND_URL}/backup/${id}/restore`,

    search: `${BACKEND_URL}/search`,

    pendingUsers: `${BACKEND_URL}/users/pending`,
    approveUser: id => `${BACKEND_URL}/users/${id}/approve`,
    resetPassword: id => `${BACKEND_URL}/users/${id}/reset-password`
};

/* =====================================================
   AUTH UTILITIES
===================================================== */
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getUser() {
    const u = localStorage.getItem(USER_KEY);
    return u ? JSON.parse(u) : null;
}

function isAuthenticated() {
    return !!getToken();
}

function requireAuth() {
    if (!isAuthenticated()) {
        forceLogout();
        return false;
    }
    return true;
}

function authHeaders(contentType = 'application/json') {
    const headers = { Authorization: `Bearer ${getToken()}` };
    if (contentType) headers['Content-Type'] = contentType;
    return headers;
}

function forceLogout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.href = 'index.html';
}

/* =====================================================
   LOGOUT
===================================================== */
async function logout() {
    try {
        if (getToken()) {
            await fetch(API.logout, { method: 'POST', headers: authHeaders() });
        }
    } catch (_) {}
    finally {
        forceLogout();
        showNotification('Logged out successfully', 'success');
    }
}
window.logout = logout;

/* =====================================================
   LOGIN
===================================================== */
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email')?.value.trim();
    const password = document.getElementById('password')?.value;
    const btn = document.getElementById('loginBtn');
    const spinner = document.getElementById('loginSpinner');

    if (!email || !password) {
        showNotification('Email and password required', 'error');
        return;
    }

    btn && (btn.disabled = true);
    spinner && (spinner.style.display = 'inline-block');

    try {
        const res = await fetch(API.login, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok || !data.access_token) {
            showNotification(data.msg || data.error || 'Login failed', 'error');
            return;
        }

        localStorage.setItem(TOKEN_KEY, data.access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user || {}));

        showNotification('Login successful', 'success');
        setTimeout(() => window.location.href = 'dashboard.html', 800);

    } catch (err) {
        showNotification('Backend not running', 'error');
        console.error(err);
    } finally {
        btn && (btn.disabled = false);
        spinner && (spinner.style.display = 'none');
    }
}

/* =====================================================
   DASHBOARD
===================================================== */
async function loadDashboard() {
    if (!requireAuth()) return;

    try {
        const res = await fetch(API.me, { headers: authHeaders() });
        if (!res.ok) return forceLogout();

        const user = await res.json();
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        document.getElementById('user-name')?.textContent = user.full_name || 'User';
        document.getElementById('user-role')?.textContent = user.role || 'user';
        document.getElementById('welcome-text')?.textContent = `Welcome back, ${user.full_name || 'Your Honor'}`;

        loadRecentCases();
        loadBackupInfo();
        loadSystemStats();

    } catch {
        showNotification('Failed to load dashboard', 'error');
    }
}

/* =====================================================
   RECENT CASES
===================================================== */
async function loadRecentCases() {
    const tbody = document.getElementById('casesTableBody');
    if (!tbody) return;

    // Note: Cases endpoint not in your flask routes - you'll need to add it
    // For now, using mock data
    const mockCases = [
        { case_number: 'CR-2024-001', title: 'State vs. John Doe', status: 'Active', court_station: 'Nairobi High Court', filed_on: '2024-10-15' },
        { case_number: 'CV-2024-045', title: 'Land Dispute - Nakuru', status: 'Pending', court_station: 'Nakuru High Court', filed_on: '2024-10-14' },
        { case_number: 'MC-2024-123', title: 'Commercial Arbitration', status: 'Active', court_station: 'Mombasa Law Courts', filed_on: '2024-10-13' }
    ];
    
    tbody.innerHTML = mockCases.map(caseItem => `
        <tr>
            <td><strong>${escapeHtml(caseItem.case_number)}</strong></td>
            <td>${escapeHtml(caseItem.title)}</td>
            <td><span class="badge badge-${caseItem.status === 'Active' ? 'success' : 'warning'}">${escapeHtml(caseItem.status)}</span></td>
            <td>${escapeHtml(caseItem.court_station)}</td>
            <td>${escapeHtml(caseItem.filed_on)}</td>
        </tr>
    `).join('');
}

/* =====================================================
   BACKUPS
===================================================== */
async function loadBackupInfo() {
    try {
        const res = await fetch(API.backup, { headers: authHeaders() });
        if (!res.ok) return;

        const backups = await res.json();
        updateBackupInfo(backups);

    } catch (err) {
        console.error(err);
    }
}

function updateBackupInfo(backups) {
    const lastBackup = document.getElementById('last-backup');
    const storageBar = document.getElementById('storage-bar');
    const storageText = document.getElementById('storage-text');
    
    if (lastBackup && backups && backups.length > 0) {
        const latest = backups[0];
        lastBackup.textContent = new Date(latest.created_at).toLocaleString();
    }
    
    if (storageBar && storageText) {
        storageBar.style.width = '75%';
        storageText.textContent = '24.5GB / 32GB (75% used)';
    }
}

async function startBackup() {
    try {
        const res = await fetch(API.backup, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ backup_type: 'manual' })
        });

        if (res.ok) {
            showNotification('Backup started', 'success');
            loadBackupInfo();
        }
    } catch {
        showNotification('Backup failed', 'error');
    }
}

async function restoreBackup(backupId) {
    if (!requireAuth()) return;
    
    if (!confirm('Are you sure you want to restore this backup? This may overwrite current data.')) {
        return;
    }
    
    try {
        const response = await fetch(API.restoreBackup(backupId), {
            method: 'POST',
            headers: authHeaders()
        });
        
        if (response.ok) {
            showNotification('Backup restoration started', 'success');
        }
    } catch (error) {
        console.error('Restore error:', error);
        showNotification('Failed to restore backup', 'error');
    }
}

/* =====================================================
   FILE UPLOAD
===================================================== */
async function uploadFile(e) {
    e.preventDefault();
    if (!requireAuth()) return;

    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('uploadBtn');
    const spinner = document.getElementById('uploadSpinner');
    
    if (!fileInput?.files.length) {
        showNotification('Select a file', 'error');
        return;
    }

    const fd = new FormData();
    fd.append('file', fileInput.files[0]);
    
    // Add additional metadata
    const caseSelect = document.querySelector('select[name="case"]');
    const docType = document.querySelector('select[name="documentType"]');
    const description = document.querySelector('textarea[name="description"]');
    
    if (caseSelect) fd.append('case_id', caseSelect.value);
    if (docType) fd.append('document_type', docType.value);
    if (description) fd.append('description', description.value);

    // Show loading state
    uploadBtn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';

    try {
        const res = await fetch(API.uploadFile, {
            method: 'POST',
            headers: authHeaders(null), // Do NOT set JSON content type for FormData
            body: fd
        });

        if (!res.ok) {
            const err = await res.json();
            showNotification(err.msg || err.error || 'Upload failed', 'error');
            return;
        }

        showNotification('Upload successful', 'success');
        fileInput.value = '';
        loadRecentUploads();

    } catch {
        showNotification('Upload error', 'error');
    } finally {
        uploadBtn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
}

/* =====================================================
   SEARCH
===================================================== */
async function searchFiles() {
    const q = document.getElementById('searchQuery')?.value;
    const searchBtn = document.getElementById('searchBtn');
    const spinner = document.getElementById('searchSpinner');
    
    if (!q) {
        showNotification('Enter search terms', 'error');
        return;
    }

    // Show loading state
    searchBtn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';

    try {
        const res = await fetch(`${API.search}?q=${encodeURIComponent(q)}`, {
            headers: authHeaders()
        });

        if (!res.ok) {
            showNotification('Search failed', 'error');
            return;
        }

        const results = await res.json();
        displaySearchResults(results);

    } catch {
        showNotification('Search failed', 'error');
    } finally {
        searchBtn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
}

/* =====================================================
   USER MANAGEMENT
===================================================== */
async function loadPendingRegistrations() {
    if (!requireAuth()) return;
    
    try {
        const response = await fetch(API.pendingUsers, {
            headers: authHeaders()
        });
        
        if (response.ok) {
            const pending = await response.json();
            displayPendingRegistrations(pending);
        }
    } catch (error) {
        console.error('Error loading pending registrations:', error);
    }
}

async function approveUser(userId) {
    if (!requireAuth()) return;
    
    try {
        const response = await fetch(API.approveUser(userId), {
            method: 'POST',
            headers: authHeaders()
        });
        
        if (response.ok) {
            showNotification('User approved successfully', 'success');
            loadPendingRegistrations();
        }
    } catch (error) {
        console.error('Error approving user:', error);
        showNotification('Failed to approve user', 'error');
    }
}

/* =====================================================
   NOTIFICATIONS
===================================================== */
function showNotification(msg, type = 'info') {
    document.querySelectorAll('.notification').forEach(n => n.remove());

    const div = document.createElement('div');
    div.className = `notification notification-${type}`;
    div.innerHTML = `
        <div style="padding:1rem; display:flex; justify-content:space-between; align-items:center;">
            <span>${escapeHtml(msg)}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background:none; border:none; font-size:1.5rem; cursor:pointer; color:var(--slate);">&times;</button>
        </div>
    `;

    // Add notification styles if not already present
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification { position: fixed; top: 20px; right: 20px; background: white; border-radius: var(--border-radius); box-shadow: var(--shadow-lg); z-index: 9999; border-left: 4px solid; animation: slideIn 0.3s ease; }
            .notification-success { border-left-color: var(--forest); }
            .notification-error { border-left-color: var(--burgundy); }
            .notification-warning { border-left-color: var(--gold); }
            .notification-info { border-left-color: var(--slate); }
            @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(div);
    setTimeout(() => div.remove(), 5000);
}

/* =====================================================
   UTILITY FUNCTIONS
===================================================== */
function escapeHtml(text) {
    if (!text) return '';
    return text.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/* =====================================================
   INIT
===================================================== */
document.addEventListener('DOMContentLoaded', () => {
    // Redirect if auth required
    if (document.body.dataset.requiresAuth === 'true' && !isAuthenticated()) {
        forceLogout();
        return;
    }

    // Redirect to dashboard if already logged in on login page
    if (location.pathname.includes('index.html') && isAuthenticated()) {
        window.location.href = 'dashboard.html';
        return;
    }

    // Attach event listeners
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.querySelector('.upload-form')?.addEventListener('submit', uploadFile);
    
    // Set up search form
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            searchFiles();
        });
    }

    // Load dashboard data
    if (location.pathname.includes('dashboard.html')) {
        loadDashboard();
    }
    
    // Load pending registrations if on users page
    if (window.location.pathname.includes('users.html')) {
        loadPendingRegistrations();
    }
    
    // Setup file input preview
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileList = document.getElementById('fileList');
            if (fileList) {
                fileList.innerHTML = '';
                Array.from(this.files).forEach(file => {
                    const item = document.createElement('div');
                    item.className = 'file-item';
                    item.innerHTML = `
                        <div class="file-info">
                            <div class="file-icon">📄</div>
                            <div>
                                <strong>${escapeHtml(file.name)}</strong>
                                <div style="font-size: 0.8rem; color: var(--slate);">
                                    ${(file.size / 1024 / 1024).toFixed(2)} MB
                                </div>
                            </div>
                        </div>
                    `;
                    fileList.appendChild(item);
                });
            }
        });
    }
    
    // Setup drag and drop for upload area
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            uploadArea.style.borderColor = 'var(--gold)';
            uploadArea.style.backgroundColor = 'var(--light-gold)';
        }
        
        function unhighlight() {
            uploadArea.style.borderColor = '';
            uploadArea.style.backgroundColor = '';
        }
        
        uploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            const fileInput = document.getElementById('file-input');
            
            if (fileInput) {
                fileInput.files = files;
                fileInput.dispatchEvent(new Event('change'));
            }
        }
        
        // Click to browse
        uploadArea.addEventListener('click', function() {
            const fileInput = document.getElementById('file-input');
            if (fileInput) {
                fileInput.click();
            }
        });
    }
});

// Global functions for modals
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Helper functions that need to be defined
function loadRecentUploads() {
    // TODO: Implement recent uploads loading
    console.log('Recent uploads should be loaded here');
}

function displaySearchResults(results) {
    // TODO: Implement search results display
    console.log('Search results:', results);
}

function displayPendingRegistrations(pending) {
    // TODO: Implement pending registrations display
    console.log('Pending registrations:', pending);
}

function loadSystemStats() {
    // TODO: Implement system stats loading
    console.log('System stats should be loaded here');
}
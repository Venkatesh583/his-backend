const API_BASE_URL = window.API_BASE_URL || window.location.origin;

async function apiFetch(path, options = {}) {
    const url = `${API_BASE_URL}${path}`;
    const headers = options.headers ? { ...options.headers } : {};
    if (!headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, {
        ...options,
        headers,
        credentials: options.credentials || 'same-origin'
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const errorMessage = data.message || 'Request failed. Please try again.';
        throw new Error(errorMessage);
    }
    return data;
}

function showMessage(elementId, message, isError = false) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.style.color = isError ? '#d32f2f' : '#1b5e20';
}

function normalizeReason(reason) {
    return reason && reason.toString().trim().length > 0
        ? reason
        : 'No AI explanation available';
}

async function login(event) {
    if (event) event.preventDefault();
    showMessage('login-error', '');

    const username = document.getElementById('username')?.value.trim();
    const password = document.getElementById('password')?.value;

    if (!username || !password) {
        showMessage('login-error', 'Username and password are required.', true);
        return;
    }

    try {
        const data = await apiFetch('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        localStorage.setItem('his_user_id', data.user_id);
        localStorage.setItem('his_username', data.username);

        window.location.href = '/caseworker/dashboard';
    } catch (err) {
        showMessage('login-error', err.message, true);
    }
}

async function submitApplication(event) {
    if (event) event.preventDefault();
    showMessage('form-error', '');
    showMessage('apply-result', '');

    const name = document.getElementById('name')?.value.trim();
    const age = parseInt(document.getElementById('age')?.value, 10);
    const income = parseFloat(document.getElementById('income')?.value);
    const family_size = parseInt(document.getElementById('family_size')?.value, 10);

    if (!name || isNaN(age) || isNaN(income) || isNaN(family_size)) {
        showMessage('form-error', 'Please fill all required fields with valid values.', true);
        return;
    }

    try {
        const data = await apiFetch('/apply', {
            method: 'POST',
            body: JSON.stringify({ name, age, income, family_size })
        });

        document.getElementById('public-register')?.reset();
        const message = `Application submitted successfully. AI Decision: ${data.ai_decision}. Explanation: ${normalizeReason(data.ai_reason)}`;
        showMessage('apply-result', message, false);
    } catch (err) {
        showMessage('form-error', err.message, true);
    }
}

function buildPendingTable(applications) {
    if (!applications || applications.length === 0) {
        return '<p>No pending applications at the moment.</p>';
    }

    const rows = applications.map(app => `
        <tr>
            <td>${app.id}</td>
            <td>${app.name}</td>
            <td>${app.age}</td>
            <td>${app.income}</td>
            <td>${app.family_size}</td>
            <td>${app.status}</td>
            <td>${app.ai_decision}</td>
            <td>${normalizeReason(app.ai_reason)}</td>
            <td>${app.created_at || 'N/A'}</td>
            <td>
                <button type="button" onclick="updateApplicationStatus(${app.id}, 'Approved')">Approve</button>
                <button type="button" onclick="updateApplicationStatus(${app.id}, 'Rejected')">Reject</button>
            </td>
        </tr>
    `).join('');

    return `
        <table class="app-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Age</th>
                    <th>Income</th>
                    <th>Family Size</th>
                    <th>Status</th>
                    <th>AI Decision</th>
                    <th>AI Reason</th>
                    <th>Created At</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

function buildApplicationsTable(applications) {
    if (!applications || applications.length === 0) {
        return '<p>No applications available.</p>';
    }

    const rows = applications.map(app => `
        <tr>
            <td>${app.id}</td>
            <td>${app.name}</td>
            <td>${app.age}</td>
            <td>${app.income}</td>
            <td>${app.family_size}</td>
            <td>${app.status}</td>
            <td>${app.ai_decision}</td>
            <td>${normalizeReason(app.ai_reason)}</td>
            <td>${app.created_at || 'N/A'}</td>
        </tr>
    `).join('');

    return `
        <table class="app-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Age</th>
                    <th>Income</th>
                    <th>Family Size</th>
                    <th>Status</th>
                    <th>AI Decision</th>
                    <th>AI Reason</th>
                    <th>Created At</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

async function loadPendingApplications() {
    const list = document.getElementById('pending-applications-list');
    const errorId = 'pending-error';
    if (!list) return;
    list.innerHTML = '<p>Loading pending applications...</p>';
    showMessage(errorId, '');

    try {
        const applications = await apiFetch('/pending-applications', { method: 'GET' });
        list.innerHTML = buildPendingTable(applications);
    } catch (err) {
        list.innerHTML = '';
        showMessage(errorId, err.message, true);
    }
}

async function loadApplications() {
    const list = document.getElementById('applications-list');
    const errorId = 'applications-error';
    if (!list) return;
    list.innerHTML = '<p>Loading applications...</p>';
    showMessage(errorId, '');

    try {
        const applications = await apiFetch('/applications', { method: 'GET' });
        list.innerHTML = buildApplicationsTable(applications);
    } catch (err) {
        list.innerHTML = '';
        showMessage(errorId, err.message, true);
    }
}

function buildDocumentsTable(documents) {
    if (!documents || documents.length === 0) {
        return '<p>No documents available.</p>';
    }

    const rows = documents.map(doc => {
        const preview = doc.extracted_text
            ? doc.extracted_text.length > 200
                ? `${doc.extracted_text.slice(0, 200)}...`
                : doc.extracted_text
            : 'No text extracted';
        return `
        <tr>
            <td>${doc.id}</td>
            <td>${doc.name || 'Unnamed Document'}</td>
            <td>${doc.status}</td>
            <td>${normalizeReason(doc.ai_summary) || 'No analysis available'}</td>
            <td>${preview}</td>
            <td>${doc.created_at || 'N/A'}</td>
        </tr>
    `;
    }).join('');

    return `
        <table class="app-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>AI Summary</th>
                    <th>Extracted Text</th>
                    <th>Created At</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

async function loadDocuments() {
    const list = document.getElementById('documents-list');
    const errorId = 'document-error';
    if (!list) return;
    list.innerHTML = '<p>Loading documents...</p>';
    showMessage(errorId, '');

    try {
        const documents = await apiFetch('/documents', { method: 'GET' });
        list.innerHTML = buildDocumentsTable(documents);
    } catch (err) {
        list.innerHTML = '';
        showMessage(errorId, err.message, true);
    }
}

async function uploadDocument(event) {
    if (event) event.preventDefault();
    showMessage('document-error', '');
    showMessage('upload-success', '');

    const form = document.getElementById('document-upload-form');
    const name = document.getElementById('document-name')?.value.trim();
    const fileInput = document.getElementById('document-file');
    const file = fileInput?.files?.[0];

    if (!name || !file) {
        showMessage('document-error', 'Document name and file are required.', true);
        return;
    }

    const formData = new FormData();
    formData.append('name', name);
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload-document`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });
        const data = await response.json();
        if (!response.ok) {
            const message = data.error || 'Upload failed';
            throw new Error(message);
        }

        form.reset();
        let message = data.message || 'Document uploaded successfully.';
        if (data.ai_summary) {
            message += '\nAI Summary: ' + data.ai_summary;
        }
        showMessage('upload-success', message, false);
        await loadDocuments();
    } catch (err) {
        showMessage('document-error', err.message, true);
    }
}

async function updateApplicationStatus(applicationId, status) {
    if (!applicationId || !status) return;
    showMessage('pending-error', '');

    try {
        await apiFetch('/update-status', {
            method: 'POST',
            body: JSON.stringify({ id: applicationId, status })
        });
        await loadPendingApplications();
    } catch (err) {
        showMessage('pending-error', err.message, true);
    }
}

window.login = login;
window.submitApplication = submitApplication;
window.updateApplicationStatus = updateApplicationStatus;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('pending-applications-list')) {
        loadPendingApplications();
    }
    if (document.getElementById('applications-list')) {
        loadApplications();
    }
    if (document.getElementById('documents-list')) {
        loadDocuments();
    }
    if (document.getElementById('document-upload-form')) {
        document.getElementById('document-upload-form').addEventListener('submit', uploadDocument);
    }
});

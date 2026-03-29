const API_BASE = window.location.origin;
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const documentsList = document.getElementById('documentsList');
const messagesContainer = document.getElementById('messagesContainer');
const statusMessage = document.getElementById('statusMessage');
const providerSelect = document.getElementById('providerSelect');
const providerStatus = document.getElementById('providerStatus');

uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.style.background = '#e8ebff'; });
uploadArea.addEventListener('dragleave', () => { uploadArea.style.background = '#f8f9ff'; });
uploadArea.addEventListener('drop', (e) => { e.preventDefault(); uploadArea.style.background = '#f8f9ff'; handleFiles(e.dataTransfer.files); });
fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

async function handleFiles(files) {
    for (let file of files) {
        if (!file.name.endsWith('.pdf')) {
            showStatus('Only PDF files are supported', 'error');
            continue;
        }
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
            const data = await response.json();
            if (response.ok) {
                showStatus(`✓ ${file.name} uploaded successfully`, 'success');
                loadDocuments();
                enableQA();
            } else {
                showStatus(`✗ Error: ${data.detail}`, 'error');
            }
        } catch (error) {
            showStatus(`✗ Upload failed: ${error.message}`, 'error');
        }
    }
}

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/documents`);
        const data = await response.json();
        if (data.documents.length === 0) {
            documentsList.innerHTML = '<div class="empty-state"><p>No documents uploaded yet</p></div>';
        } else {
            documentsList.innerHTML = data.documents.map(doc => `
                <div class="document-item">
                    <div><strong>📄 ${doc.filename}</strong><br><small>${(doc.size/1000).toFixed(1)} KB</small></div>
                    <button class="delete-btn" onclick="deleteDocument('${doc.doc_id}')">Delete</button>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

async function deleteDocument(docId) {
    if (!confirm('Delete this document?')) return;
    try {
        const response = await fetch(`${API_BASE}/documents/${docId}`, { method: 'DELETE' });
        if (response.ok) {
            showStatus('Document deleted', 'success');
            loadDocuments();
            if (!documentsList.querySelector('.document-item')) disableQA();
        }
    } catch (error) {
        showStatus(`Delete failed: ${error.message}`, 'error');
    }
}

askBtn.addEventListener('click', askQuestion);
questionInput.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !askBtn.disabled) askQuestion(); });

async function askQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;
    askBtn.disabled = true;
    askBtn.textContent = '🔄 Asking...';
    addMessage('question', question);
    questionInput.value = '';
    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question,
                provider: providerSelect.value
            })
        });
        const data = await response.json();
        if (response.ok) {
            addMessage('answer', data.answer);
            showStatus(`✓ ${data.model} • ${data.documents_used.length} document(s)`, 'success');
        } else {
            addMessage('answer', `Error: ${data.detail}`);
        }
    } catch (error) {
        addMessage('answer', `Error: ${error.message}`);
    }
    askBtn.disabled = false;
    askBtn.textContent = 'Ask';
}

function addMessage(type, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    const label = type === 'question' ? '❓ You asked:' : '🤖 AI Response:';
    msgDiv.innerHTML = `<div class="message-label">${label}</div><div class="message-content">${escapeHtml(text)}</div>`;
    if (messagesContainer.querySelector('.empty-state')) {
        messagesContainer.innerHTML = '';
    }
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    setTimeout(() => { statusMessage.className = 'status-message'; }, 5000);
}

function enableQA() {
    questionInput.disabled = false;
    askBtn.disabled = false;
}

function disableQA() {
    questionInput.disabled = true;
    askBtn.disabled = true;
}

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

async function loadProviders() {
    try {
        const response = await fetch(`${API_BASE}/providers`);
        const data = await response.json();

        // Update provider selector based on availability
        const providers = data.providers;
        let availableCount = 0;
        let statusText = '';

        providers.forEach(provider => {
            const option = Array.from(providerSelect.options).find(o => o.value === provider.name);
            if (option) {
                if (provider.available) {
                    availableCount++;
                    option.text = `${provider.model} ✅`;
                } else {
                    option.disabled = true;
                    option.text = `${provider.model} (not configured)`;
                }
            }
        });

        if (availableCount === 0) {
            providerStatus.textContent = '⚠️ No providers configured';
            providerSelect.disabled = true;
        } else {
            providerStatus.textContent = `${availableCount} provider(s) ready`;
            providerSelect.disabled = false;
        }
    } catch (error) {
        console.error('Failed to load providers:', error);
    }
}

loadProviders();
loadDocuments();

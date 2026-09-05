/**
 * Athenaeum — RAG Library Assistant
 * Plain Vanilla JavaScript implementation
 */

// In-memory conversation state
let messageHistory = [];
let isRequestInProgress = false;
let messageCounter = 0;
let loadingTimer = null;
let healthRetryTimer = null;

// DOM Elements
const chatPanel = document.getElementById('chat-panel');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const emptyState = document.getElementById('empty-state');

/**
 * Sanitize text to prevent XSS attacks
 */
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Check backend health status with auto-wake retry
 */
async function checkHealth() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch('/health', {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (data && data.status === 'ok') {
        statusDot.classList.remove('offline');
        statusDot.classList.add('pulse');
        statusText.textContent = 'Online';
        if (healthRetryTimer) {
          clearTimeout(healthRetryTimer);
          healthRetryTimer = null;
        }
        return;
      }
    }
    throw new Error('Health check non-ok status');
  } catch (err) {
    statusDot.classList.add('offline');
    statusDot.classList.remove('pulse');
    statusText.textContent = 'Waking engine…';
    
    // Automatically retry pinging every 5 seconds until Render wakes up
    if (!healthRetryTimer) {
      healthRetryTimer = setTimeout(() => {
        healthRetryTimer = null;
        checkHealth();
      }, 5000);
    }
  }
}

/**
 * Toggle visibility of sources for a specific assistant message
 */
function toggleSources(messageId) {
  const sourcesList = document.getElementById(`sources-list-${messageId}`);
  const toggleBtn = document.getElementById(`sources-btn-${messageId}`);

  if (!sourcesList || !toggleBtn) return;

  const isShowing = sourcesList.classList.contains('show');
  if (isShowing) {
    sourcesList.classList.remove('show');
    toggleBtn.classList.remove('expanded');
    toggleBtn.setAttribute('aria-expanded', 'false');
  } else {
    sourcesList.classList.add('show');
    toggleBtn.classList.add('expanded');
    toggleBtn.setAttribute('aria-expanded', 'true');
  }
}

/**
 * Build collapsible sources UI safely
 */
function createSourcesElement(sources, messageId) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return null;
  }

  const container = document.createElement('div');
  container.className = 'sources-container';

  const count = sources.length;
  const toggleBtn = document.createElement('button');
  toggleBtn.type = 'button';
  toggleBtn.className = 'sources-toggle-btn';
  toggleBtn.id = `sources-btn-${messageId}`;
  toggleBtn.setAttribute('aria-expanded', 'false');
  toggleBtn.setAttribute('aria-controls', `sources-list-${messageId}`);

  toggleBtn.innerHTML = `
    <span>${count} ${count === 1 ? 'source' : 'sources'}</span>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
  `;

  toggleBtn.addEventListener('click', () => toggleSources(messageId));
  container.appendChild(toggleBtn);

  const list = document.createElement('div');
  list.className = 'sources-list';
  list.id = `sources-list-${messageId}`;

  sources.forEach((source) => {
    const card = document.createElement('div');
    card.className = 'source-card liquid-glass';

    const header = document.createElement('div');
    header.className = 'source-card-header';

    const docName = document.createElement('span');
    docName.className = 'source-doc-name';
    docName.textContent = source.doc || 'Library Documentation';
    header.appendChild(docName);

    if (source.score !== undefined && source.score !== null) {
      const scoreBadge = document.createElement('span');
      scoreBadge.className = 'source-score-badge';
      const percentage = typeof source.score === 'number'
        ? Math.round(source.score <= 1 ? source.score * 100 : source.score)
        : source.score;
      scoreBadge.textContent = `${percentage}% match`;
      header.appendChild(scoreBadge);
    }

    card.appendChild(header);

    if (source.snippet) {
      const snippetEl = document.createElement('p');
      snippetEl.className = 'source-snippet';
      const rawSnippet = source.snippet.trim();
      snippetEl.textContent = rawSnippet.length > 120 ? rawSnippet.slice(0, 120) + '…' : rawSnippet;
      card.appendChild(snippetEl);
    }

    list.appendChild(card);
  });

  container.appendChild(list);
  return container;
}

/**
 * Append message into the chat thread with animate-fade-rise
 */
function appendMessage(role, content, sources = [], isError = false) {
  if (emptyState && emptyState.parentNode) {
    emptyState.style.display = 'none';
  }

  const id = ++messageCounter;
  const messageRow = document.createElement('div');
  messageRow.className = `message-row ${role} animate-fade-rise`;
  messageRow.id = `msg-${id}`;

  if (role === 'user') {
    const userBubble = document.createElement('div');
    userBubble.className = 'user-bubble';
    userBubble.textContent = content;
    messageRow.appendChild(userBubble);
  } else {
    // Assistant message
    const assistantContent = document.createElement('div');
    assistantContent.className = 'assistant-content';

    const label = document.createElement('div');
    label.className = 'assistant-label';
    label.textContent = 'Athenaeum';
    assistantContent.appendChild(label);

    const text = document.createElement('div');
    text.className = `assistant-text${isError ? ' error-text' : ''}`;
    text.textContent = content;
    assistantContent.appendChild(text);

    if (sources && sources.length > 0) {
      const sourcesEl = createSourcesElement(sources, id);
      if (sourcesEl) {
        assistantContent.appendChild(sourcesEl);
      }
    }

    messageRow.appendChild(assistantContent);
  }

  chatPanel.appendChild(messageRow);
  chatPanel.scrollTop = chatPanel.scrollHeight;

  messageHistory.push({ role, content, sources, isError });
  return messageRow;
}

/**
 * Create and show the loading indicator with cold-start progressive messaging
 */
function showLoadingIndicator() {
  const loadingRow = document.createElement('div');
  loadingRow.className = 'message-row assistant animate-fade-rise';
  loadingRow.id = 'loading-row';

  const assistantContent = document.createElement('div');
  assistantContent.className = 'assistant-content';

  const label = document.createElement('div');
  label.className = 'assistant-label';
  label.textContent = 'Athenaeum';

  const loadingText = document.createElement('div');
  loadingText.className = 'loading-indicator';
  loadingText.id = 'loading-text';
  loadingText.textContent = 'Athenaeum is thinking…';

  assistantContent.appendChild(label);
  assistantContent.appendChild(loadingText);
  loadingRow.appendChild(assistantContent);

  chatPanel.appendChild(loadingRow);
  chatPanel.scrollTop = chatPanel.scrollHeight;

  // Progressive timer for cold start transparency
  let elapsed = 0;
  clearInterval(loadingTimer);
  loadingTimer = setInterval(() => {
    elapsed += 1;
    const textEl = document.getElementById('loading-text');
    if (!textEl) {
      clearInterval(loadingTimer);
      return;
    }
    if (elapsed >= 25) {
      textEl.textContent = 'Formulating grounded answer from library records…';
    } else if (elapsed >= 6) {
      textEl.textContent = 'Waking library engine from sleep… (~25s)';
    }
  }, 1000);
}

/**
 * Remove the loading indicator
 */
function removeLoadingIndicator() {
  clearInterval(loadingTimer);
  const loadingRow = document.getElementById('loading-row');
  if (loadingRow) {
    loadingRow.remove();
  }
}

/**
 * Send user message and fetch RAG response
 */
async function sendMessage(query) {
  const trimmed = query ? query.trim() : '';
  if (!trimmed || isRequestInProgress) return;

  isRequestInProgress = true;
  chatInput.value = '';
  sendBtn.disabled = true;

  // Append user message immediately
  appendMessage('user', trimmed);

  // Display loading indicator
  showLoadingIndicator();

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ query: trimmed })
    });

    removeLoadingIndicator();

    if (!response.ok) {
      throw new Error(`Server returned error HTTP ${response.status}`);
    }

    const data = await response.json();
    const answer = data && data.answer ? data.answer : 'No answer returned from knowledge base.';
    const sources = data && Array.isArray(data.sources) ? data.sources : [];

    appendMessage('assistant', answer, sources);
    
    // Confirmed backend active
    statusDot.classList.remove('offline');
    statusDot.classList.add('pulse');
    statusText.textContent = 'Online';
  } catch (error) {
    console.error('Error in /chat request:', error);
    removeLoadingIndicator();
    appendMessage('assistant', 'Something went wrong — try again.', [], true);
  } finally {
    isRequestInProgress = false;
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

// Form Submission Event
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const query = chatInput.value;
  sendMessage(query);
});

// Setup Click Handlers on Suggestion Chips
function setupSuggestionChips() {
  const chips = document.querySelectorAll('.suggestion-chip');
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const question = chip.textContent.trim();
      if (question) {
        chatInput.value = question;
        sendMessage(question);
      }
    });
  });
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  setupSuggestionChips();
  // Keep health updated every 45s
  setInterval(checkHealth, 45000);
});

// ===== STATE =====
const tabs = []; // { id, title, sessionId, messages: [{role, content}], attachments: [], isWaiting, abortController, toolCallElements, assistantEl, assistantText }
let activeTabId = null;
let pendingAttachments = []; // { filename, path, dataUrl? }
let expandedDirs = new Set();
let gitStatus = { modified: [], added: [], deleted: [] };
let uploadCount = 0; // Track in-progress uploads

// Safe localStorage wrappers (handles disabled/quota errors)
function safeGet(key, fallback) {
  try { return localStorage.getItem(key); } catch { return fallback !== undefined ? fallback : null; }
}
function safeSet(key, value) {
  try { localStorage.setItem(key, value); } catch {}
}
function safeJsonParse(str, fallback) {
  try { const v = JSON.parse(str); return v != null ? v : fallback; } catch { return fallback; }
}

// Derived convenience — true if any tab is streaming
function getIsWaiting() { return tabs.some(t => t.isWaiting); }

// ===== ARIA LIVE REGIONS (dual-container pattern from VS Code) =====
let ariaAlertContainer1, ariaAlertContainer2, lastAriaAlertTarget = 1;
let ariaStatusContainer1, ariaStatusContainer2, lastAriaStatusTarget = 1;
let _lastAriaAnnounce = 0;

function initAriaContainers() {
  ariaAlertContainer1 = document.createElement('div');
  ariaAlertContainer1.setAttribute('role', 'alert');
  ariaAlertContainer1.setAttribute('aria-atomic', 'true');
  ariaAlertContainer1.className = 'sr-only';

  ariaAlertContainer2 = document.createElement('div');
  ariaAlertContainer2.setAttribute('role', 'alert');
  ariaAlertContainer2.setAttribute('aria-atomic', 'true');
  ariaAlertContainer2.className = 'sr-only';

  ariaStatusContainer1 = document.createElement('div');
  ariaStatusContainer1.setAttribute('role', 'status');
  ariaStatusContainer1.setAttribute('aria-atomic', 'true');
  ariaStatusContainer1.className = 'sr-only';

  ariaStatusContainer2 = document.createElement('div');
  ariaStatusContainer2.setAttribute('role', 'status');
  ariaStatusContainer2.setAttribute('aria-atomic', 'true');
  ariaStatusContainer2.className = 'sr-only';

  document.body.appendChild(ariaAlertContainer1);
  document.body.appendChild(ariaAlertContainer2);
  document.body.appendChild(ariaStatusContainer1);
  document.body.appendChild(ariaStatusContainer2);
}

function ariaAlert(msg) {
  const target = lastAriaAlertTarget === 1 ? ariaAlertContainer2 : ariaAlertContainer1;
  const other = lastAriaAlertTarget === 1 ? ariaAlertContainer1 : ariaAlertContainer2;
  other.textContent = '';
  target.textContent = msg;
  lastAriaAlertTarget = lastAriaAlertTarget === 1 ? 2 : 1;
}

function ariaStatus(msg) {
  const target = lastAriaStatusTarget === 1 ? ariaStatusContainer2 : ariaStatusContainer1;
  const other = lastAriaStatusTarget === 1 ? ariaStatusContainer1 : ariaStatusContainer2;
  other.textContent = '';
  target.textContent = msg;
  lastAriaStatusTarget = lastAriaStatusTarget === 1 ? 2 : 1;
}

// Throttled ariaStatus — won't fire more than once per 5 seconds
function ariaStatusThrottled(msg) {
  const now = Date.now();
  if (now - _lastAriaAnnounce < 5000) return;
  _lastAriaAnnounce = now;
  ariaStatus(msg);
}

// ===== COMMAND PALETTE MRU HISTORY =====
let cmdHistory = safeJsonParse(safeGet('ea-cmd-history', '[]'), []);

function getCmdHistory() { return cmdHistory; }
function saveCmdHistory() {
  safeSet('ea-cmd-history', JSON.stringify(cmdHistory));
}
function addToCmdHistory(cmdId) {
  cmdHistory = cmdHistory.filter(id => id !== cmdId);
  cmdHistory.unshift(cmdId);
  if (cmdHistory.length > 50) cmdHistory.length = 50;
  saveCmdHistory();
}
function removeFromCmdHistory(cmdId) {
  cmdHistory = cmdHistory.filter(id => id !== cmdId);
  saveCmdHistory();
}

// Settings (persisted to localStorage)
const settings = {
  approvalMode: safeGet('ea-approval-mode', 'yolo') || 'yolo',
  model: safeGet('ea-model', '') || '',
  notifications: safeGet('ea-notifications', 'off') || 'off',
  verbose: safeGet('ea-verbose') === 'on',
};

// Session tags (persisted to localStorage)
// { sessionId: "red" | "blue" | "green" | "yellow" | "purple" }
let sessionTags = safeJsonParse(safeGet('ea-session-tags', '{}'), {});
let activeTagFilter = 'all';
let workspaceName = '...';

// Notification tracking
let requestStartTime = null;

const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const statusDot = document.getElementById('statusDot');
const tabBar = document.getElementById('tabBar');
const attachmentBar = document.getElementById('attachmentBar');

// Scoped icon rendering — avoids full-DOM rescan
function createIconsIn(el) {
  if (el) lucide.createIcons({ nameAttr: 'data-lucide', node: el });
  else lucide.createIcons();
}

// ===== WELCOME TEMPLATE =====
function getWelcomeHTML() {
  if (shouldShowOnboarding()) {
    return getOnboardingHTML();
  }
  return `<div class="welcome">
    <h2>Executive Assistant</h2>
    <p>Powered by Gemini CLI. Ask me anything, run workflows, or manage your workspace.</p>
    <div class="suggestions">
      <button type="button" class="suggestion" onclick="sendSuggestion('sign on')">Sign on</button>
      <button type="button" class="suggestion" onclick="sendSuggestion('What are my current priorities?')">Priorities</button>
      <button type="button" class="suggestion" onclick="sendSuggestion('Help me plan my day')">Plan my day</button>
      <button type="button" class="suggestion" onclick="sendSuggestion('Show me the project structure')">Project structure</button>
    </div>
  </div>`;
}

// ===== INIT =====
async function init() {
  initAriaContainers();
  const setupNeeded = await checkStatus();
  if (setupNeeded) return; // Setup wizard is showing, don't initialize chat UI
  createNewTab();
  loadSessions();
  loadFiles('');
  loadGitStatus();
  // Sync settings UI
  document.getElementById('settingApprovalMode').value = settings.approvalMode;
  document.getElementById('settingModel').value = settings.model;
  document.getElementById('settingNotifications').value = settings.notifications;
  document.getElementById('settingOnboarding').value = shouldShowOnboarding() ? 'on' : 'off';
  document.getElementById('settingVerbose').value = safeGet('ea-verbose') || 'off';
  if (safeGet('ea-verbose') === 'on') toggleVerboseMode('on');
  updateModelBadge();
  updateModeToggle();
  updateBreadcrumbs();
  updateStatusBar();
  pollTokenUsage();
  lucide.createIcons();
  // Initial minimap update after content renders
  setTimeout(updateMinimap, 500);
}

async function checkStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    statusDot.className = data.ready ? 'status-dot' : 'status-dot error';
    statusDot.setAttribute('aria-label', data.ready ? 'Connected' : 'Connection error');
    setConnectionStatus(data.ready);
    // Populate workspace indicator
    if (data.workspace_name) {
      workspaceName = data.workspace_name;
      document.getElementById('workspaceName').textContent = workspaceName;
      document.getElementById('workspaceIndicator').title = data.workspace || workspaceName;
      updateBreadcrumbs();
    }
    // Check if setup wizard is needed (first-time users or missing deps)
    // Skip for users who completed setup previously (localStorage flag)
    // BUT always show if dependencies are missing (can't function without CLI)
    try {
      const setupRes = await fetch('/api/setup/status');
      const setupData = await setupRes.json();
      const setupCompleted = safeGet('ea-setup-complete') === 'true';
      const depsOk = setupData.dependencies && Object.entries(setupData.dependencies)
        .filter(([k]) => k !== 'git')  // git is optional
        .every(([, v]) => v);
      if (setupData.phase !== 'ready' && (!setupCompleted || !depsOk)) {
        showSetupWizard(setupData);
        return true;
      }
    } catch {
      // /api/setup/status not available — fall back to old error modal if CLI missing
      if (!data.cli_available) {
        document.getElementById('errorModal').classList.add('open');
        const gotItBtn = document.querySelector('#errorModal .modal-actions button');
        if (gotItBtn) gotItBtn.focus();
        return true;
      }
    }
    if (!data.ready) {
      showToast('Server not ready', 'error', { id: 'server-status' });
    }
    return false;
  } catch {
    statusDot.className = 'status-dot error';
    statusDot.setAttribute('aria-label', 'Connection error');
    showToast('Connection lost', 'error', { id: 'connection', sticky: true });
    setConnectionStatus(false);
    return false;
  }
}

// ===== TABS =====
function createNewTab(sessionId = null, title = 'New Chat') {
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  tabs.push({ id, title, sessionId, messages: [], attachments: [], isWaiting: false, abortController: null, toolCallElements: {}, assistantEl: null, assistantText: '', pinned: false, hasDraft: false });
  switchTab(id);
  renderTabs();
  return id;
}

function switchTab(tabId) {
  if (activeTabId === tabId) return;

  // Save current chat content to the old tab
  if (activeTabId) {
    const current = tabs.find(t => t.id === activeTabId);
    if (current) {
      current._html = chatContainer.innerHTML;
      // If this tab is still streaming, create offscreen container so the stream can continue writing
      if (current.isWaiting) {
        current._offscreen = document.createElement('div');
        current._offscreen.innerHTML = current._html;
        // Re-bind assistantEl to the offscreen copy
        if (current.assistantEl) {
          const msgs = current._offscreen.querySelectorAll('.message.assistant');
          if (msgs.length) current.assistantEl = msgs[msgs.length - 1];
        }
        // Re-bind tool call elements to offscreen copies
        if (current.toolCallElements) {
          for (const [toolId] of Object.entries(current.toolCallElements)) {
            const el = current._offscreen.querySelector(`#tool-${CSS.escape(toolId)}`);
            if (el) current.toolCallElements[toolId] = el;
          }
        }
      }
    }
  }

  activeTabId = tabId;
  const tab = tabs.find(t => t.id === tabId);
  if (!tab) return;

  // Restore chat content — prefer offscreen container if it exists (streaming tab was backgrounded)
  if (tab._offscreen) {
    chatContainer.innerHTML = tab._offscreen.innerHTML;
    // Re-bind assistantEl to live DOM if still streaming
    if (tab.isWaiting && tab.assistantEl) {
      const msgs = chatContainer.querySelectorAll('.message.assistant');
      if (msgs.length) tab.assistantEl = msgs[msgs.length - 1];
    }
    // Re-bind tool call elements to live DOM
    if (tab.toolCallElements) {
      for (const [toolId] of Object.entries(tab.toolCallElements)) {
        const el = chatContainer.querySelector(`#tool-${CSS.escape(toolId)}`);
        if (el) tab.toolCallElements[toolId] = el;
      }
    }
    tab._offscreen = null;
    tab._html = null;
  } else if (tab._html) {
    chatContainer.innerHTML = tab._html;
  } else if (tab.messages.length > 0) {
    chatContainer.innerHTML = '';
    for (let i = 0; i < tab.messages.length; i++) {
      renderMessageToDOM(tab.messages[i].content, tab.messages[i].role, i);
    }
  } else {
    chatContainer.innerHTML = getWelcomeHTML();
  }

  renderTabs();
  highlightActiveSession();
  createIconsIn(chatContainer);
  updateBreadcrumbs();
  updateStatusBar();
  messageInput.focus();
  scrollToBottom();
  setTimeout(updateMinimap, 100);
}

function closeTab(tabId, e) {
  if (e) e.stopPropagation();
  const idx = tabs.findIndex(t => t.id === tabId);
  if (idx === -1) return;
  tabs.splice(idx, 1);

  if (tabs.length === 0) {
    createNewTab();
  } else if (activeTabId === tabId) {
    switchTab(tabs[Math.min(idx, tabs.length - 1)].id);
  }
  renderTabs();
}

function renderTabs() {
  const newTabBtn = tabBar.querySelector('.new-tab-btn');
  tabBar.innerHTML = '';
  // Sort: pinned tabs first, then unpinned in original order
  const sorted = [...tabs].sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));
  for (const tab of sorted) {
    const el = document.createElement('div');
    el.className = `tab${tab.id === activeTabId ? ' active' : ''}${tab.pinned ? ' pinned' : ''}`;
    el.setAttribute('role', 'tab');
    el.setAttribute('aria-selected', tab.id === activeTabId ? 'true' : 'false');
    el.setAttribute('draggable', 'true');
    el.onclick = () => switchTab(tab.id);
    el.dataset.tabId = tab.id;
    const draftDot = tab.hasDraft ? '<span class="draft-dot"> \u2022</span>' : '';
    el.innerHTML = `
      <span class="tab-pin-icon"><i data-lucide="pin"></i></span>
      <span class="tab-label" data-action="rename">${escapeHtml(tab.title)}${draftDot}</span>
      <button class="tab-close" data-action="close" title="Close"><i data-lucide="x"></i></button>
    `;
    tabBar.appendChild(el);
  }
  tabBar.appendChild(newTabBtn || createNewTabBtn());
  createIconsIn(tabBar);
  checkTabOverflow();
}

function checkTabOverflow() {
  tabBar.classList.toggle('scrollable', tabBar.scrollWidth > tabBar.clientWidth);
}

function startRenameTab(tabId, e) {
  e.stopPropagation();
  const tab = tabs.find(t => t.id === tabId);
  if (!tab) return;
  const labelEl = e.target;
  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'tab-rename-input';
  input.value = tab.title;
  input.onblur = () => finishRenameTab(tabId, input);
  input.onkeydown = (ev) => {
    if (ev.key === 'Enter') { ev.preventDefault(); input.blur(); }
    if (ev.key === 'Escape') { ev.preventDefault(); renderTabs(); }
  };
  labelEl.replaceWith(input);
  input.focus();
  input.select();
}

function finishRenameTab(tabId, input) {
  const tab = tabs.find(t => t.id === tabId);
  if (tab && input.value.trim()) {
    tab.title = input.value.trim().slice(0, 60);
  }
  renderTabs();
  updateBreadcrumbs();
}

function createNewTabBtn() {
  const btn = document.createElement('button');
  btn.className = 'new-tab-btn';
  btn.onclick = () => createNewTab();
  btn.title = 'New chat (Ctrl+N)';
  btn.innerHTML = '<i data-lucide="plus"></i>';
  return btn;
}

// Event delegation for tab bar
tabBar.addEventListener('click', e => {
  const closeBtn = e.target.closest('[data-action="close"]');
  if (closeBtn) {
    const tabEl = closeBtn.closest('.tab');
    if (tabEl && tabEl.dataset.tabId) {
      e.stopPropagation();
      closeTab(tabEl.dataset.tabId, e);
    }
    return;
  }
});
tabBar.addEventListener('dblclick', e => {
  const label = e.target.closest('[data-action="rename"]');
  if (label) {
    const tabEl = label.closest('.tab');
    if (tabEl && tabEl.dataset.tabId) {
      e.stopPropagation();
      startRenameTab(tabEl.dataset.tabId, e);
    }
  }
});

function getActiveTab() { return tabs.find(t => t.id === activeTabId); }

// ===== TAB-AWARE DOM CONTAINER =====
// Returns the correct container for DOM writes: chatContainer if tab is active, offscreen div if backgrounded.
function getTabContainer(tab) {
  if (!tab) return chatContainer;
  if (tab.id === activeTabId) return chatContainer;
  // Background tab — use an offscreen container so streaming doesn't spill into the visible tab
  if (!tab._offscreen) {
    tab._offscreen = document.createElement('div');
    tab._offscreen.innerHTML = tab._html || '';
  }
  return tab._offscreen;
}

function isTabVisible(tab) {
  return !tab || tab.id === activeTabId;
}

// ===== SESSIONS =====
async function loadSessions() {
  try {
    const res = await fetch('/api/sessions');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const list = document.getElementById('sessionList');
    if (!data.sessions || data.sessions.length === 0) {
      list.innerHTML = '<div style="padding: 8px; color: var(--text-muted); font-size: 0.78rem;">No previous sessions</div>';
      return;
    }
    list.innerHTML = '';
    for (const s of data.sessions) {
      const tag = sessionTags[s.session_id];
      // Filter by active tag
      if (activeTagFilter !== 'all' && tag !== activeTagFilter) continue;

      const div = document.createElement('div');
      div.className = 'sidebar-item';
      div.setAttribute('role', 'listitem');
      div.dataset.sessionId = s.session_id;
      div.dataset.sessionIndex = s.index;
      div.onclick = () => resumeSession(s.session_id, s.preview);

      const tagHtml = tag
        ? `<span class="session-tag tag-${escapeHtml(tag)}" data-action="tag-picker">${escapeHtml(tag)}</span>`
        : `<span class="session-tag" style="opacity:0.3;border:1px dashed var(--text-muted);padding:1px 4px;" data-action="tag-picker">+</span>`;

      div.innerHTML = `
        <span class="icon"><i data-lucide="message-square"></i></span>
        <span class="label">${escapeHtml(s.preview)}</span>
        ${tagHtml}
        <span class="meta">${s.time_ago}</span>
        <button class="delete-btn" data-action="archive-session" title="Archive (Shift+click to keep permanently)"><i data-lucide="archive"></i></button>
      `;
      list.appendChild(div);
    }
    highlightActiveSession();
    createIconsIn(list);
  } catch (err) {
    console.error('loadSessions failed:', err);
    document.getElementById('sessionList').innerHTML = '<div style="padding: 8px; color: var(--text-muted); font-size: 0.78rem;">Failed to load</div>';
    showToast('Failed to load sessions', 'error', { id: 'session-load' });
  }
}

async function resumeSession(sessionId, preview) {
  const existing = tabs.find(t => t.sessionId === sessionId);
  if (existing) { switchTab(existing.id); return; }

  const tabId = createNewTab(sessionId, preview.slice(0, 40));
  const tab = tabs.find(t => t.id === tabId);

  chatContainer.innerHTML = '<div class="thinking"><span>Loading conversation history...</span></div>';

  try {
    const res = await fetch(`/api/sessions/${sessionId}/messages`);
    const data = await res.json();
    chatContainer.innerHTML = '';

    if (data.messages && data.messages.length > 0) {
      for (const msg of data.messages) {
        renderMessageToDOM(msg.content, msg.role);
        tab.messages.push(msg);
      }
    } else {
      addMessage('Resumed session (no message history available).', 'system');
    }

    tab._html = chatContainer.innerHTML;
    createIconsIn(chatContainer);
  } catch (e) {
    chatContainer.innerHTML = '';
    addMessage('Failed to load history for session: ' + preview, 'system');
  }
}

function renderMessageToDOM(text, role, index) {
  const tab = getActiveTab();
  const div = document.createElement('div');
  div.className = `message ${role}`;
  if (index !== undefined) {
    div.dataset.msgIndex = index;
  } else if (tab) {
    div.dataset.msgIndex = tab.messages.length;
  }
  if (role === 'assistant') {
    div.innerHTML = renderMarkdown(text);
    addMessageActions(div, text, 'assistant');
  } else if (role === 'user') {
    div.textContent = text;
    addMessageActions(div, text, 'user');
  } else {
    div.textContent = text;
  }
  chatContainer.appendChild(div);
  return div;
}

function archiveSession(sessionId, permanent = false) {
  const item = document.querySelector(`[data-session-id="${CSS.escape(sessionId)}"]`);
  const index = item ? item.dataset.sessionIndex : null;
  
  // Optimistic removal from UI
  if (item) {
    if (permanent) {
      item.style.background = 'var(--accent-dim)';
    }
    item.style.transition = 'opacity 0.15s, transform 0.15s';
    item.style.opacity = '0';
    item.style.transform = 'translateX(-20px)';
    setTimeout(() => item.remove(), 150);
  }
  // Close any open tab for this session
  const tab = tabs.find(t => t.sessionId === sessionId);
  if (tab) closeTab(tab.id);
  // Background API call
  let endpoint = permanent
    ? `/api/sessions/${sessionId}/archive`
    : `/api/sessions/${sessionId}`;
  if (!permanent && index) {
    endpoint += `?index=${index}`;
  }
  const method = permanent ? 'POST' : 'DELETE';
  fetch(endpoint, { method }).then(() => {
    showToast(permanent ? 'Session permanently archived' : 'Session archived', 'success');
  }).catch(() => {
    showToast('Failed to archive session', 'error');
    loadSessions(); // Restore on failure
  });
}

function archiveAllSessions() {
  const items = document.querySelectorAll('#sessionList .sidebar-item');
  if (items.length === 0) return;
  // Optimistic removal
  items.forEach((item, i) => {
    item.style.transition = `opacity 0.15s ${i * 30}ms, transform 0.15s ${i * 30}ms`;
    item.style.opacity = '0';
    item.style.transform = 'translateX(-20px)';
  });
  setTimeout(() => {
    document.getElementById('sessionList').innerHTML =
      '<div style="padding: 8px; color: var(--text-muted); font-size: 0.78rem;">No previous sessions</div>';
  }, 150 + items.length * 30);
  // Background API calls
  fetch('/api/sessions').then(r => r.json()).then(data => {
    // Reverse order to keep indices stable while deleting
    const sorted = [...data.sessions].sort((a, b) => parseInt(b.index) - parseInt(a.index));
    Promise.allSettled(
      sorted.map(s => fetch(`/api/sessions/${s.session_id}?index=${s.index}`, { method: 'DELETE' }))
    );
  }).catch(() => loadSessions());
  // Detach all tabs
  tabs.forEach(t => { t.sessionId = null; });
}

// Event delegation for session list
document.getElementById('sessionList').addEventListener('click', e => {
  const actionEl = e.target.closest('[data-action]');
  if (!actionEl) return;
  const item = actionEl.closest('.sidebar-item');
  if (!item) return;
  const sessionId = item.dataset.sessionId;

  if (actionEl.dataset.action === 'tag-picker') {
    e.stopPropagation();
    toggleTagPicker(sessionId, e);
  } else if (actionEl.dataset.action === 'archive-session') {
    e.stopPropagation();
    archiveSession(sessionId, e.shiftKey);
  }
});

function highlightActiveSession() {
  const tab = getActiveTab();
  document.querySelectorAll('#sessionList .sidebar-item').forEach(el => {
    el.classList.toggle('active', tab && el.dataset.sessionId === tab.sessionId);
  });
}

// ===== FILE BROWSER =====
async function loadFiles(path) {
  try {
    const res = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
    const data = await res.json();

    if (path === '') {
      const list = document.getElementById('fileList');
      list.innerHTML = '';
      renderFileEntries(list, data.entries, 0);
    } else {
      const parentEl = document.querySelector(`[data-file-path="${CSS.escape(path)}"]`);
      if (!parentEl) return;
      const childContainer = parentEl.nextElementSibling;
      if (childContainer && childContainer.classList.contains('file-children')) {
        childContainer.remove();
        expandedDirs.delete(path);
        parentEl.querySelector('.icon').textContent = '\u{1F4C1}';
        return;
      }
      expandedDirs.add(path);
      parentEl.querySelector('.icon').textContent = '\u{1F4C2}';
      const container = document.createElement('div');
      container.className = 'file-children';
      renderFileEntries(container, data.entries, parseInt(parentEl.style.getPropertyValue('--depth') || '0') + 1);
      parentEl.after(container);
    }
  } catch {}
}

let _fileSearchTimer = null;
function handleFileSearch(query) {
  clearTimeout(_fileSearchTimer);
  if (!query.trim()) { loadFiles(''); return; }
  _fileSearchTimer = setTimeout(() => _doFileSearch(query), 200);
}

async function _doFileSearch(query) {
  try {
    const res = await fetch(`/api/files/search?query=${encodeURIComponent(query)}`);
    const data = await res.json();
    const list = document.getElementById('fileList');
    list.innerHTML = '';
    if (data.results.length === 0) {
      list.innerHTML = '<div style="padding: 12px; color: var(--text-muted); font-size: 0.8rem;">No matches found</div>';
      return;
    }
    renderFileEntries(list, data.results, 0, true);
  } catch (e) {
    console.error('Search failed:', e);
  }
}

function renderFileEntries(container, entries, depth, isSearch = false) {
  for (const entry of entries) {
    const div = document.createElement('div');
    div.className = 'sidebar-item file-item';
    div.style.setProperty('--depth', depth);
    div.dataset.filePath = entry.path;

    if (entry.is_dir) {
      const isOpen = expandedDirs.has(entry.path);
      div.innerHTML = `
        <span class="icon"><i data-lucide="${isOpen ? 'folder-open' : 'folder'}"></i></span>
        <span class="label">${escapeHtml(entry.name)}</span>
      `;
      div.onclick = () => loadFiles(entry.path);
    } else {
      const icon = getFileIcon(entry.name);
      const label = isSearch ? entry.path : entry.name;
      div.innerHTML = `
        <span class="icon"><i data-lucide="${icon}"></i></span>
        <span class="label" title="${escapeHtml(entry.path)}">${escapeHtml(label)}</span>
        <span class="meta">${formatSize(entry.size)}</span>
      `;
      div.onclick = () => previewFile(entry.path, entry.name);
    }
    container.appendChild(div);

    if (!isSearch && entry.is_dir && expandedDirs.has(entry.path)) {
      loadFiles(entry.path);
    }
  }
  createIconsIn(container);
  applyGitStatus();
}

async function loadGitStatus() {
  try {
    const res = await fetch('/api/files/git-status');
    gitStatus = await res.json();
    applyGitStatus();
  } catch {}
}

function applyGitStatus() {
  const changedDirs = new Set();
  const allChanged = [...gitStatus.modified, ...gitStatus.added, ...gitStatus.deleted];
  for (const filepath of allChanged) {
    const parts = filepath.split('/');
    for (let i = 1; i < parts.length; i++) {
      changedDirs.add(parts.slice(0, i).join('/'));
    }
  }
  document.querySelectorAll('.file-item').forEach(el => {
    const path = el.dataset.filePath;
    if (!path) return;
    el.classList.remove('git-modified', 'git-added', 'git-deleted', 'git-has-changes');
    if (gitStatus.modified.includes(path)) el.classList.add('git-modified');
    else if (gitStatus.added.includes(path)) el.classList.add('git-added');
    else if (gitStatus.deleted.includes(path)) el.classList.add('git-deleted');
    else if (changedDirs.has(path)) el.classList.add('git-has-changes');
  });
}

function getFileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  const icons = {
    md: 'file-text', py: 'terminal', js: 'file-code', ts: 'file-code-2', html: 'globe',
    json: 'settings', css: 'palette', sh: 'command', bat: 'command', txt: 'file',
    png: 'image', jpg: 'image', jpeg: 'image', gif: 'image', svg: 'image',
    pdf: 'file-digit', csv: 'table',
  };
  return icons[ext] || 'file';
}

function formatSize(bytes) {
  if (bytes == null) return '';
  if (bytes < 1024) return bytes + 'B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + 'K';
  return (bytes / (1024 * 1024)).toFixed(1) + 'M';
}

async function previewFile(path, name) {
  const panel = document.getElementById('filePreview');
  const title = document.getElementById('filePreviewTitle');
  const content = document.getElementById('filePreviewContent');
  title.textContent = name;
  content.textContent = 'Loading...';
  panel.classList.add('open');
  trapFocus(panel);

  try {
    const res = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
    const data = await res.json();
    content.textContent = data.content;
  } catch {
    content.textContent = '(Failed to load file)';
  }
}

function closeFilePreview() {
  const panel = document.getElementById('filePreview');
  releaseFocus(panel);
  panel.classList.remove('open');
}

// ===== SIDEBAR =====
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('collapsed');
  const backdrop = document.getElementById('sidebarBackdrop');
  if (window.innerWidth <= 900) {
    backdrop.classList.toggle('open', !sidebar.classList.contains('collapsed'));
  } else {
    backdrop.classList.remove('open');
  }
}

function toggleSection(header) {
  const section = header.parentElement;
  section.classList.toggle('expanded');
}

// ===== FILE UPLOAD =====
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  // Show progress indicator
  uploadCount++;
  renderAttachmentBar();

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    if (!res.ok) return null;
    const data = await res.json();

    let dataUrl = null;
    if (file.type.startsWith('image/')) {
      dataUrl = await new Promise(resolve => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.readAsDataURL(file);
      });
    }

    return { filename: data.filename, path: data.path, dataUrl };
  } finally {
    uploadCount--;
  }
}

function handleFileSelect(files) {
  for (const file of files) {
    uploadFile(file).then(att => {
      if (att) {
        pendingAttachments.push(att);
      }
      renderAttachmentBar();
    });
  }
  document.getElementById('fileInput').value = '';
}

function removeAttachment(idx) {
  pendingAttachments.splice(idx, 1);
  renderAttachmentBar();
}

function renderAttachmentBar() {
  attachmentBar.innerHTML = '';
  // Show upload progress if files are being uploaded
  if (uploadCount > 0) {
    const prog = document.createElement('div');
    prog.className = 'upload-progress';
    prog.innerHTML = `<div class="spinner"></div><span>Uploading ${uploadCount} file${uploadCount > 1 ? 's' : ''}...</span>`;
    attachmentBar.appendChild(prog);
  }
  pendingAttachments.forEach((att, i) => {
    const div = document.createElement('div');
    div.className = 'attachment-preview';
    div.innerHTML = `
      ${att.dataUrl ? `<img src="${att.dataUrl}" alt="">` : ''}
      <span>${escapeHtml(att.filename)}</span>
      <button class="remove" onclick="removeAttachment(${i})">&times;</button>
    `;
    attachmentBar.appendChild(div);
  });
}

// Drag and drop
let dragCounter = 0;
document.addEventListener('dragenter', e => {
  e.preventDefault();
  dragCounter++;
  document.getElementById('dropOverlay').classList.add('active');
});
document.addEventListener('dragleave', e => {
  e.preventDefault();
  dragCounter--;
  if (dragCounter <= 0) {
    dragCounter = 0;
    document.getElementById('dropOverlay').classList.remove('active');
  }
});
document.addEventListener('dragover', e => e.preventDefault());
document.addEventListener('drop', e => {
  e.preventDefault();
  dragCounter = 0;
  document.getElementById('dropOverlay').classList.remove('active');
  if (e.dataTransfer.files.length) handleFileSelect(e.dataTransfer.files);
});

// Paste handler for screenshots
document.addEventListener('paste', e => {
  if (e.target === messageInput && e.clipboardData.files.length > 0) {
    e.preventDefault();
    handleFileSelect(e.clipboardData.files);
  }
});

// ===== CHAT =====
async function cancelGeneration() {
  // Find the tab that is currently streaming (prefer active tab, fall back to any streaming tab)
  let tab = getActiveTab();
  if (!tab || !tab.isWaiting) {
    tab = tabs.find(t => t.isWaiting);
  }
  if (!tab) return;

  try {
    if (tab.sessionId) {
      await fetch('/api/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: tab.sessionId })
      });
    }
    if (tab.abortController) tab.abortController.abort();
  } catch (e) {
    console.error('Cancel failed:', e);
  } finally {
    tab.isWaiting = false;
    if (!getIsWaiting()) {
      sendBtn.style.display = 'flex';
      document.getElementById('stopBtn').classList.remove('active');
      statusDot.className = 'status-dot';
      statusDot.setAttribute('aria-label', 'Connected');
    }
  }
}

async function sendMessage(overrideText = null) {
  const text = overrideText || messageInput.value.trim();
  // Capture the originating tab at the START — use this reference throughout
  const tab = getActiveTab();
  if (!tab) return;
  if ((!text && pendingAttachments.length === 0) || tab.isWaiting) return;

  // Remove welcome/onboarding (tab is always active at this point — sendMessage is user-initiated)
  const welcome = chatContainer.querySelector('.welcome, .onboarding');
  if (welcome) {
    welcome.remove();
    // If onboarding was shown, mark as dismissed
    if (shouldShowOnboarding()) safeSet('ea-onboarded', 'true');
  }

  // Build message with attachment references
  let fullMessage = text;
  const attachments = overrideText ? [] : [...pendingAttachments];
  if (attachments.length > 0) {
    const refs = attachments.map(a => a.path).join(', ');
    fullMessage = `[Attached files: ${refs}]\n\n${text}`;
  }

  // Show user message (tab is active here, but pass it for consistency)
  const userEl = addMessage(text || '(attached files)', 'user', tab);
  if (attachments.length > 0) {
    const attDiv = document.createElement('div');
    attDiv.className = 'attachments';
    for (const att of attachments) {
      if (att.dataUrl) {
        const img = document.createElement('img');
        img.className = 'attachment-img';
        img.src = att.dataUrl;
        img.alt = att.filename;
        attDiv.appendChild(img);
      } else {
        const chip = document.createElement('span');
        chip.className = 'attachment-chip';
        chip.textContent = att.filename;
        attDiv.appendChild(chip);
      }
    }
    userEl.appendChild(attDiv);
  }

  // Update tab title from first message
  if (tab.messages.length === 0) {
    tab.title = text.slice(0, 40) || 'Chat';
    renderTabs();
  }

  tab.messages.push({ role: 'user', content: text });

  // Clear input and attachments
  if (!overrideText) {
    messageInput.value = '';
    autoResize(messageInput);
    pendingAttachments = [];
    renderAttachmentBar();
  }

  // Show thinking & Stop button
  requestStartTime = Date.now();
  tab.isWaiting = true;
  tab.toolCallElements = {};
  tab.assistantEl = null;
  tab.assistantText = '';
  tab.abortController = new AbortController();
  sendBtn.style.display = 'none';
  const stopBtn = document.getElementById('stopBtn');
  stopBtn.classList.add('active');
  statusDot.className = 'status-dot loading';
  statusDot.setAttribute('aria-label', 'Processing');

  const thinkingEl = addThinking(tab);
  let thinkingRemoved = false;
  let firstChunkAnnounced = false;
  ariaStatus('Generating response...');
  function removeThinking() {
    if (thinkingRemoved) return;
    cleanupThinking(thinkingEl);
    thinkingEl.remove();
    // Also remove from tab container (may differ from thinkingEl's parent after tab switch)
    const tc = getTabContainer(tab);
    const stale = tc.querySelector('.thinking-wrapper');
    if (stale) { cleanupThinking(stale); stale.remove(); }
    thinkingRemoved = true;
  }

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: fullMessage,
        session_id: tab.sessionId,
        approval_mode: settings.approvalMode,
        model: settings.model || null,
      }),
      signal: tab.abortController.signal
    });

    if (!res.ok) {
      removeThinking();
      const err = await res.json().catch(() => ({ detail: 'Connection failed' }));
      addMessage(`Error: ${err.detail || 'Something went wrong'}`, 'system', tab);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        if (data === '[DONE]') continue;

        let event;
        try { event = JSON.parse(data); } catch { continue; }
        debugLog(event);

        // Capture session ID
        if (event.type === 'init' && event.session_id) {
          tab.sessionId = event.session_id;
          highlightActiveSession();
          if (!thinkingRemoved) {
            updateThinkingStatus(thinkingEl, 'Connected — processing request...');
          }
        }

        // Remove thinking only on first assistant message (not tool_use — keep status visible during tool work)
        if (!thinkingRemoved && event.type === 'message' && event.role === 'assistant') {
          removeThinking();
        }

        switch (event.type) {
          case 'tool_use':
            // Update thinking status with tool name
            if (!thinkingRemoved) {
              updateThinkingStatus(thinkingEl, `Running ${event.tool_name}...`);
            }
            ariaAlert('Running tool: ' + event.tool_name);
            addToolUse(event, tab);
            break;
          case 'tool_result': {
            // Mark tool as done in thinking feed
            const toolName = tab.toolCallElements[event.tool_id]
              ? tab.toolCallElements[event.tool_id].querySelector('.tool-call-name')?.textContent || 'tool'
              : 'tool';
            if (!thinkingRemoved) {
              updateThinkingStatus(thinkingEl, `${toolName} ${event.status === 'success' ? 'completed' : 'failed'}`, event.status === 'success' ? 'done' : 'running');
            }
            ariaStatus(toolName + (event.status === 'success' ? ' completed' : ' failed'));
            updateToolResult(event, tab);
            break;
          }
          case 'message':
            if (event.role === 'assistant') {
              if (event.delta) {
                tab.assistantText += event.content;
                if (!tab.assistantEl) {
                  tab.assistantEl = addMessage('', 'assistant', tab);
                }
                if (!firstChunkAnnounced) {
                  firstChunkAnnounced = true;
                  ariaStatus('Response started');
                } else {
                  ariaStatusThrottled('Still generating...');
                }
                tab.assistantEl.innerHTML = renderMarkdown(tab.assistantText);
                if (isTabVisible(tab)) scrollToBottom();
              } else {
                // Fix 3: Non-delta full messages saved to state
                tab.messages.push({ role: 'assistant', content: event.content });
                const el = addMessage(event.content, 'assistant', tab);
                addMessageActions(el, event.content);
              }
            }
            break;
          case 'result':
            if (event.stats) {
              const container = getTabContainer(tab);
              const parts = [];
              if (event.stats.duration_ms) parts.push(`${(event.stats.duration_ms / 1000).toFixed(1)}s`);
              if (event.stats.total_tokens) parts.push(`${event.stats.total_tokens.toLocaleString()} tokens`);
              if (event.stats.tool_calls) parts.push(`${event.stats.tool_calls} tool calls`);
              if (parts.length) {
                const el = document.createElement('div');
                el.className = 'stats-bar';
                el.textContent = parts.join(' \u00b7 ');
                container.appendChild(el);
                if (isTabVisible(tab)) scrollToBottom();
              }
            }
            break;
          case 'error':
            removeThinking();
            addMessage(`Error: ${event.message}`, 'system', tab);
            break;
        }
      }
    }

    // Fix 8: Process remaining SSE buffer after stream ends
    if (buffer.trim()) {
      const remainingLines = buffer.split('\n');
      for (const line of remainingLines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        if (data === '[DONE]') continue;
        let event;
        try { event = JSON.parse(data); } catch { continue; }
        debugLog(event);
        if (event.type === 'message' && event.role === 'assistant') {
          if (event.delta) {
            tab.assistantText += event.content;
            if (!tab.assistantEl) tab.assistantEl = addMessage('', 'assistant', tab);
            tab.assistantEl.innerHTML = renderMarkdown(tab.assistantText);
          } else {
            tab.messages.push({ role: 'assistant', content: event.content });
            const el = addMessage(event.content, 'assistant', tab);
            addMessageActions(el, event.content);
          }
        }
      }
    }

    removeThinking();
    if (tab.assistantText) {
      tab.messages.push({ role: 'assistant', content: tab.assistantText });
      if (tab.assistantEl) addMessageActions(tab.assistantEl, tab.assistantText);
    }
    ariaStatus('Response complete');

    loadSessions();

  } catch (e) {
    if (e.name === 'AbortError') {
      removeThinking();
      addMessage('Generation stopped.', 'system', tab);
    } else {
      removeThinking();
      if (tab.assistantText) {
        tab.messages.push({ role: 'assistant', content: tab.assistantText });
      }
      addMessage('Connection lost. Partial response preserved above.', 'system', tab);
    }
  } finally {
    // Use captured `tab` reference, NOT getActiveTab()
    tab.isWaiting = false;
    tab.abortController = null;
    tab.assistantEl = null;

    // If the stream finished while this tab was backgrounded, sync _html from offscreen and discard
    if (tab._offscreen) {
      tab._html = tab._offscreen.innerHTML;
      tab._offscreen = null;
    }

    // Only update UI chrome if no other tab is still streaming
    if (!getIsWaiting()) {
      sendBtn.style.display = 'flex';
      stopBtn.classList.remove('active');
      statusDot.className = 'status-dot';
      statusDot.setAttribute('aria-label', 'Connected');
    }
    messageInput.focus();

    // Refresh token usage (updates both token bar and status bar)
    pollTokenUsage();

    // Browser notification if task took > 10s and tab is not focused
    if (settings.notifications === 'on' && requestStartTime) {
      const elapsed = Date.now() - requestStartTime;
      if (elapsed > 10000 && document.hidden) {
        sendNotification('Task complete', tab.assistantText ? tab.assistantText.slice(0, 100) : 'Your request has finished.');
      }
    }
    requestStartTime = null;
  }
}

// ===== TOOL CALLS =====
function addToolUse(event, tab) {
  const container = getTabContainer(tab);
  let wrapper = container.querySelector('.tool-calls:last-child');
  if (!wrapper || wrapper.nextElementSibling) {
    wrapper = document.createElement('div');
    wrapper.className = 'tool-calls';
    container.appendChild(wrapper);
  }
  const argsPreview = Object.entries(event.parameters || {})
    .map(([k, v]) => {
      const val = typeof v === 'string' ? v : JSON.stringify(v);
      return `${k}=${val.length > 45 ? val.slice(0, 45) + '...' : val}`;
    }).join(', ');

  const div = document.createElement('div');
  div.className = 'tool-call';
  div.id = `tool-${event.tool_id}`;
  div.dataset.startTime = Date.now();
  div.innerHTML = `
    <div class="tool-call-header" onclick="this.nextElementSibling.classList.toggle('open')">
      <span class="tool-call-icon spinning"><i data-lucide="settings"></i></span>
      <span class="tool-call-name">${escapeHtml(event.tool_name)}</span>
      <span class="tool-call-args">${escapeHtml(argsPreview)}</span>
      <span class="tool-call-status running">running</span>
    </div>
    <div class="tool-call-body">
      <pre>Waiting for result...</pre>
    </div>
  `;
  wrapper.appendChild(div);
  if (tab) tab.toolCallElements[event.tool_id] = div;
  createIconsIn(div);
  if (isTabVisible(tab)) scrollToBottom();
}

function updateToolResult(event, tab) {
  const tcElements = (tab && tab.toolCallElements) || {};
  const div = tcElements[event.tool_id];
  if (!div) return;

  const startTime = parseInt(div.dataset.startTime);
  const duration = ((Date.now() - startTime) / 1000).toFixed(1);

  div.querySelector('.tool-call-icon').classList.remove('spinning');
  // Remove approval buttons if still present
  const approval = div.querySelector('.tool-approval');
  if (approval) approval.remove();

  const st = div.querySelector('.tool-call-status');
  st.className = `tool-call-status ${event.status === 'success' ? 'success' : 'error'}`;
  st.textContent = `${event.status === 'success' ? 'done' : 'error'} (${duration}s)`;

  const output = event.output || '(no output)';
  const diffHtml = renderDiff(output);
  const bodyEl = div.querySelector('.tool-call-body pre');

  if (diffHtml) {
    bodyEl.outerHTML = diffHtml;
  } else if (output.length > 3000) {
    // Show truncated with expand toggle
    bodyEl.textContent = output.slice(0, 3000) + '\n...(truncated)';
    const expandBtn = document.createElement('button');
    expandBtn.className = 'copy-btn';
    expandBtn.style.cssText = 'margin: 8px 0 0; font-size: 0.75rem;';
    expandBtn.textContent = 'Show full output';
    expandBtn.onclick = () => {
      if (expandBtn.textContent === 'Show full output') {
        bodyEl.textContent = output;
        expandBtn.textContent = 'Collapse';
      } else {
        bodyEl.textContent = output.slice(0, 3000) + '\n...(truncated)';
        expandBtn.textContent = 'Show full output';
      }
    };
    div.querySelector('.tool-call-body').appendChild(expandBtn);
  } else {
    bodyEl.textContent = output;
  }
}

// ===== MESSAGE RENDERING =====
function addMessage(text, role, targetTab = null) {
  const tab = targetTab || getActiveTab();
  const container = getTabContainer(tab);
  const div = document.createElement('div');
  div.className = `message ${role}`;
  if (tab) div.dataset.msgIndex = tab.messages.length;
  if (role === 'assistant') {
    div.innerHTML = renderMarkdown(text);
  } else {
    div.textContent = text;
  }
  container.appendChild(div);

  if (role === 'user' || role === 'assistant') {
    addMessageActions(div, text, role);
  }
  createIconsIn(div);
  if (isTabVisible(tab)) scrollToBottom();
  return div;
}

function addMessageActions(el, text, role = 'assistant') {
  // Remove existing actions if re-rendering
  const existing = el.querySelector('.message-actions');
  if (existing) existing.remove();

  if (!text) return;

  const actions = document.createElement('div');
  actions.className = 'message-actions';
  if (role === 'assistant') {
    actions.innerHTML = `
      <button onclick="copyMessageText(this)" title="Copy"><i data-lucide="copy"></i></button>
      <button onclick="forkFromMessage(this)" title="Fork from here"><i data-lucide="git-branch"></i></button>
      <button onclick="regenerateMessage(this)" title="Regenerate"><i data-lucide="refresh-cw"></i></button>
    `;
  } else {
    actions.innerHTML = `
      <button onclick="copyMessageText(this)" title="Copy"><i data-lucide="copy"></i></button>
      <button onclick="forkFromMessage(this)" title="Fork from here"><i data-lucide="git-branch"></i></button>
    `;
  }
  el.style.position = 'relative';
  el.appendChild(actions);
}

function copyMessageText(btn) {
  const msg = btn.closest('.message');
  if (!msg) return;
  const clone = msg.cloneNode(true);
  const actions = clone.querySelector('.message-actions');
  if (actions) actions.remove();
  const text = clone.innerText;
  navigator.clipboard.writeText(text).then(() => {
    btn.innerHTML = '<i data-lucide="check"></i>';
    createIconsIn(btn);
    setTimeout(() => { btn.innerHTML = '<i data-lucide="copy"></i>'; createIconsIn(btn); }, 1500);
  });
}

function regenerateMessage(btn) {
  const msg = btn.closest('.message');
  if (!msg || getIsWaiting()) return;
  const tab = getActiveTab();
  if (!tab || tab.messages.length < 2) return;
  tab._html = null;

  // Find the last user message
  let lastUserIdx = -1;
  for (let i = tab.messages.length - 1; i >= 0; i--) {
    if (tab.messages[i].role === 'user') { lastUserIdx = i; break; }
  }
  if (lastUserIdx === -1) return;

  const lastUserText = tab.messages[lastUserIdx].content;

  // Remove the last assistant message(s) from state and DOM
  while (tab.messages.length > lastUserIdx + 1) {
    tab.messages.pop();
  }
  // Also remove the user message itself since sendMessage will re-add it
  tab.messages.pop();

  // Remove DOM elements from the last user message onward using data-msg-index
  const allEls = chatContainer.querySelectorAll('.message, .tool-calls, .stats-bar');
  const toRemove = [];
  let foundUser = false;
  for (let i = allEls.length - 1; i >= 0; i--) {
    const el = allEls[i];
    if (el.dataset.msgIndex !== undefined && parseInt(el.dataset.msgIndex) === lastUserIdx) {
      toRemove.push(el);
      foundUser = true;
      break;
    }
    toRemove.push(el);
  }
  toRemove.forEach(el => el.remove());

  // Re-send
  sendMessage(lastUserText);
}

function forkFromMessage(btn) {
  const msgEl = btn.closest('.message');
  if (!msgEl) return;
  const tab = getActiveTab();
  if (!tab) return;
  const idx = parseInt(msgEl.dataset.msgIndex);
  if (isNaN(idx) || idx < 0) return;

  const msgsUpTo = tab.messages.slice(0, idx + 1);
  const newTabId = createNewTab(null, 'Fork: ' + (tab.title || 'Chat'));
  const newTab = tabs.find(t => t.id === newTabId);
  if (newTab) {
    newTab.messages = JSON.parse(JSON.stringify(msgsUpTo));
    chatContainer.innerHTML = '';
    for (let i = 0; i < newTab.messages.length; i++) {
      renderMessageToDOM(newTab.messages[i].content, newTab.messages[i].role, i);
    }
    createIconsIn(chatContainer);
    showToast('Forked — ' + msgsUpTo.length + ' message' + (msgsUpTo.length !== 1 ? 's' : '') + ' copied', 'success');
  }
}

// ===== MESSAGE CONTEXT MENU =====
let _msgContextTarget = null; // { element, messageIndex }

chatContainer.addEventListener('contextmenu', function(e) {
  // Don't intercept right-click on code blocks or tool calls
  if (e.target.closest('pre, code, .tool-call')) return;

  const msgEl = e.target.closest('.message');
  if (!msgEl) return;
  e.preventDefault();

  // Close any open tab context menu
  closeTabContextMenu();

  const idx = parseInt(msgEl.dataset.msgIndex);
  _msgContextTarget = { element: msgEl, messageIndex: isNaN(idx) ? -1 : idx };

  const menu = document.getElementById('msgContextMenu');
  menu.style.left = e.clientX + 'px';
  menu.style.top = e.clientY + 'px';
  menu.style.display = 'block';

  createIconsIn(menu);

  // Ensure menu stays in viewport
  const rect = menu.getBoundingClientRect();
  if (rect.right > window.innerWidth) menu.style.left = (window.innerWidth - rect.width - 8) + 'px';
  if (rect.bottom > window.innerHeight) menu.style.top = (window.innerHeight - rect.height - 8) + 'px';
});

function closeMsgContextMenu() {
  document.getElementById('msgContextMenu').style.display = 'none';
  _msgContextTarget = null;
}

// Close on click outside
document.addEventListener('click', closeMsgContextMenu);

// Close on scroll or resize
chatContainer.addEventListener('scroll', closeMsgContextMenu);
window.addEventListener('resize', closeMsgContextMenu);

// Close on Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeMsgContextMenu();
});

document.getElementById('msgContextMenu').addEventListener('click', function(e) {
  const btn = e.target.closest('[data-action]');
  if (!btn || !_msgContextTarget) return;

  const action = btn.dataset.action;
  const tab = getActiveTab();

  switch (action) {
    case 'copy-text': {
      const clone = _msgContextTarget.element.cloneNode(true);
      const actionsEl = clone.querySelector('.message-actions');
      if (actionsEl) actionsEl.remove();
      const text = clone.innerText;
      navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard', 'success');
      }).catch(() => {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('Copied to clipboard', 'success');
      });
      break;
    }
    case 'copy-md': {
      if (tab && _msgContextTarget.messageIndex >= 0 && tab.messages[_msgContextTarget.messageIndex]) {
        const md = tab.messages[_msgContextTarget.messageIndex].content;
        navigator.clipboard.writeText(md).then(() => {
          showToast('Markdown copied', 'success');
        }).catch(() => {
          const ta = document.createElement('textarea');
          ta.value = md;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          showToast('Markdown copied', 'success');
        });
      }
      break;
    }
    case 'fork': {
      if (tab && _msgContextTarget.messageIndex >= 0) {
        const msgsUpTo = tab.messages.slice(0, _msgContextTarget.messageIndex + 1);
        const newTabId = createNewTab(null, 'Fork: ' + (tab.title || 'Chat'));
        const newTab = tabs.find(t => t.id === newTabId);
        if (newTab) {
          newTab.messages = JSON.parse(JSON.stringify(msgsUpTo));
          chatContainer.innerHTML = '';
          for (let i = 0; i < newTab.messages.length; i++) {
            renderMessageToDOM(newTab.messages[i].content, newTab.messages[i].role, i);
          }
          createIconsIn(chatContainer);
          showToast('Forked — ' + msgsUpTo.length + ' message' + (msgsUpTo.length !== 1 ? 's' : '') + ' copied', 'success');
        }
      }
      break;
    }
    case 'delete': {
      if (tab && _msgContextTarget.messageIndex >= 0) {
        tab.messages.splice(_msgContextTarget.messageIndex, 1);
        tab._html = null;
        chatContainer.innerHTML = '';
        if (tab.messages.length === 0) {
          chatContainer.innerHTML = getWelcomeHTML();
          createIconsIn(chatContainer);
        } else {
          for (let i = 0; i < tab.messages.length; i++) {
            renderMessageToDOM(tab.messages[i].content, tab.messages[i].role, i);
          }
          createIconsIn(chatContainer);
        }
        showToast('Message deleted', 'info');
      }
      break;
    }
  }

  closeMsgContextMenu();
});

function addThinking(targetTab = null) {
  const tab = targetTab || getActiveTab();
  const container = getTabContainer(tab);

  // Wrapper holds both the thinking bar and the activity feed
  const wrapper = document.createElement('div');
  wrapper.className = 'thinking-wrapper';

  const div = document.createElement('div');
  div.className = 'thinking';
  div.innerHTML = `
    <div class="thinking-dots"><span></span><span></span><span></span></div>
    <span class="thinking-label">Thinking...</span>
    <span class="thinking-elapsed"></span>
  `;
  wrapper.appendChild(div);

  // Activity feed for real-time status
  const feed = document.createElement('div');
  feed.className = 'activity-feed';
  wrapper.appendChild(feed);

  container.appendChild(wrapper);

  // Elapsed timer
  const startTime = Date.now();
  const elapsedEl = div.querySelector('.thinking-elapsed');
  const labelEl = div.querySelector('.thinking-label');
  const timer = setInterval(() => {
    const secs = Math.floor((Date.now() - startTime) / 1000);
    if (secs < 60) elapsedEl.textContent = `${secs}s`;
    else elapsedEl.textContent = `${Math.floor(secs / 60)}m ${secs % 60}s`;
  }, 1000);

  // Attach methods to the wrapper for updating status
  wrapper._timer = timer;
  wrapper._feed = feed;
  wrapper._label = labelEl;

  if (isTabVisible(tab)) scrollToBottom();
  return wrapper;
}

function updateThinkingStatus(thinkingEl, text, icon = 'running') {
  if (!thinkingEl || !thinkingEl._feed) return;
  const feed = thinkingEl._feed;
  const label = thinkingEl._label;

  // Update the main label
  if (label) label.textContent = text;

  // Add to activity feed
  const item = document.createElement('div');
  item.className = 'activity-item';
  const iconClass = icon === 'done' ? 'activity-icon done' : 'activity-icon';
  const iconChar = icon === 'done' ? '✓' : '›';
  item.innerHTML = `<span class="${iconClass}">${iconChar}</span><span class="activity-text">${escapeHtml(text)}</span>`;
  feed.appendChild(item);

  // Keep feed trimmed to last 8 items
  while (feed.children.length > 8) feed.removeChild(feed.firstChild);

  feed.scrollTop = feed.scrollHeight;
}

function cleanupThinking(thinkingEl) {
  if (thinkingEl && thinkingEl._timer) clearInterval(thinkingEl._timer);
}

// ===== MARKDOWN & HIGHLIGHTING =====
const mdRenderer = new marked.Renderer();
mdRenderer.code = function(codeObj) {
  // marked v15+ passes an object { text, lang, escaped }
  const code = typeof codeObj === 'object' ? codeObj.text : codeObj;
  const lang = typeof codeObj === 'object' ? codeObj.lang : arguments[1];
  const validLang = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
  const highlighted = hljs.highlight(code, { language: validLang }).value;
  return `<div class="code-container">
    <div class="code-header">
      <span>${validLang}</span>
      <button class="copy-btn">Copy</button>
    </div>
    <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
    <template class="raw-code">${escapeHtml(code)}</template>
  </div>`;
};

marked.setOptions({ renderer: mdRenderer, breaks: true, gfm: true });

function renderMarkdown(text) {
  if (!text) return '';
  return DOMPurify.sanitize(marked.parse(text));
}

// Optimized escapeHtml — avoids DOM element creation per call
const _escapeMap = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, m => _escapeMap[m]);
}

// ===== HELPERS =====
function scrollToBottom() {
  requestAnimationFrame(() => { chatContainer.scrollTop = chatContainer.scrollHeight; });
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 180) + 'px';
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function sendSuggestion(text) {
  messageInput.value = text;
  sendMessage();
}

// ===== UTILITIES =====
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.innerHTML;
    btn.innerHTML = '&#10003; Copied';
    btn.style.borderColor = 'var(--success)';
    btn.style.color = 'var(--success)';
    setTimeout(() => {
      btn.innerHTML = original;
      btn.style.borderColor = '';
      btn.style.color = '';
    }, 2000);
  });
}

// ===== KEYBOARD SHORTCUTS =====
function isTyping() {
  const el = document.activeElement;
  return el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT');
}

document.addEventListener('keydown', e => {
  // Escape always works
  if (e.key === 'Escape') {
    e.preventDefault();
    // Priority: command palette > notification center > cancel gen > close settings > close lightbox > close file preview
    if (document.getElementById('cmdPalette').classList.contains('open')) { closeCommandPalette(); }
    else if (notificationCenterOpen) { toggleNotificationCenter(); }
    else if (getIsWaiting()) { cancelGeneration(); }
    else if (document.getElementById('settingsPanel').classList.contains('open')) { closeSettings(); }
    else if (document.getElementById('imageLightbox').classList.contains('open')) { closeLightbox(); }
    else { closeFilePreview(); }
    return;
  }

  // Ctrl+K always works (even when typing)
  if (e.ctrlKey && e.key === 'k') {
    e.preventDefault();
    toggleCommandPalette();
    return;
  }

  // Skip other shortcuts when typing in textarea/input
  if (isTyping() && !e.ctrlKey) return;

  if (e.ctrlKey && e.key === 'n') { e.preventDefault(); createNewTab(); return; }
  if (e.ctrlKey && e.key === '/') { e.preventDefault(); toggleSidebar(); return; }
  if (e.ctrlKey && e.key === 'u') { e.preventDefault(); document.getElementById('fileInput').click(); return; }
  if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
    e.preventDefault();
    const tab = getActiveTab();
    if (tab && tab.sessionId) {
      archiveSession(tab.sessionId);
      showToast('Session archived', 'success');
    }
  }
});

// ===== THEME =====
function initTheme() {
  const saved = safeGet('ea-theme', 'dark') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
  document.getElementById('hljs-dark').disabled = (saved === 'light');
  document.getElementById('hljs-light').disabled = (saved === 'dark');
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  safeSet('ea-theme', next);
  updateThemeIcon(next);
  document.getElementById('hljs-dark').disabled = (next === 'light');
  document.getElementById('hljs-light').disabled = (next === 'dark');
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('themeToggle');
  btn.innerHTML = theme === 'dark' ? '<i data-lucide="sun"></i>' : '<i data-lucide="moon"></i>';
  btn.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  createIconsIn(btn);
}

initTheme();

// ===== FOCUS TRAP (upgraded with focusout guard) =====
let _focusTrapPrev = null;
let _focusTrapHandler = null;
let _focusTrapFocusout = null;

function trapFocus(containerEl) {
  _focusTrapPrev = document.activeElement;
  const focusable = containerEl.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (focusable.length === 0) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  first.focus();
  _focusTrapHandler = (e) => {
    if (e.key !== 'Tab') return;
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  };
  containerEl.addEventListener('keydown', _focusTrapHandler);

  // Guard: if focus escapes the container, pull it back
  _focusTrapFocusout = (e) => {
    if (e.relatedTarget && !containerEl.contains(e.relatedTarget)) {
      const currentFocusable = containerEl.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (currentFocusable.length > 0) currentFocusable[0].focus();
    }
  };
  containerEl.addEventListener('focusout', _focusTrapFocusout);
}

function releaseFocus(containerEl) {
  if (_focusTrapHandler && containerEl) {
    containerEl.removeEventListener('keydown', _focusTrapHandler);
    _focusTrapHandler = null;
  }
  if (_focusTrapFocusout && containerEl) {
    containerEl.removeEventListener('focusout', _focusTrapFocusout);
    _focusTrapFocusout = null;
  }
  if (_focusTrapPrev) { _focusTrapPrev.focus(); _focusTrapPrev = null; }
}

// ===== SETTINGS =====
let activeSettingsCategory = 'general';

function switchSettingsCategory(category) {
  activeSettingsCategory = category;
  // Update sidebar nav items
  document.querySelectorAll('.settings-nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.category === category);
  });
  // Update mobile tab items
  document.querySelectorAll('.settings-mobile-tab').forEach(el => {
    el.classList.toggle('active', el.dataset.category === category);
  });
  // Show/hide content sections
  document.querySelectorAll('.settings-section').forEach(el => {
    el.style.display = el.dataset.section === category ? '' : 'none';
  });
  // Update content header
  const headers = { general: 'General', profile: 'Profile', reset: 'Reset & Maintenance', developer: 'Developer' };
  document.querySelector('.settings-content-header').textContent = headers[category] || category;
  // Load profile data on first visit
  if (category === 'profile' && !profileDataLoaded) {
    loadProfileData();
  }
  if (category === 'reset') {
    loadFolderStats();
  }
  createIconsIn(document.getElementById('settingsPanel'));
}

function openSettings() {
  const panel = document.getElementById('settingsPanel');
  panel.classList.add('open');
  document.getElementById('settingsBackdrop').classList.add('open');
  switchSettingsCategory('general');
  trapFocus(panel);
}

function closeSettings() {
  const panel = document.getElementById('settingsPanel');
  releaseFocus(panel);
  panel.classList.remove('open');
  document.getElementById('settingsBackdrop').classList.remove('open');
}

function saveSetting(key, value) {
  settings[key] = value;
  safeSet(`ea-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`, value);
  if (key === 'approvalMode') updateModeToggle();
  updateStatusBar();
}

function toggleApprovalMode() {
  const next = settings.approvalMode === 'yolo' ? 'plan' : 'yolo';
  saveSetting('approvalMode', next);
  document.getElementById('settingApprovalMode').value = next;
}

function updateModeToggle() {
  const label = document.getElementById('modeLabel');
  const toggle = document.getElementById('modeToggle');
  if (settings.approvalMode === 'yolo') {
    label.textContent = 'Auto-approve all';
    toggle.classList.remove('active');
  } else {
    label.textContent = 'Plan (read-only)';
    toggle.classList.add('active');
  }
}

// ===== PROFILE EDITOR & RESET =====
let profileDataLoaded = false;

function toggleProfileEditor() {
  switchSettingsCategory('profile');
}

function toggleResetSection() {
  switchSettingsCategory('reset');
}

const profileFileConfig = [
  {
    file: 'me.md', title: 'About You',
    sections: { 'Name': 'Name', 'Role': 'Role', 'Tech Comfort Level': 'Tech Comfort Level', 'Goals': 'Goals' },
    fields: [
      { key: 'Name', label: 'Name', type: 'text' },
      { key: 'Role', label: 'Role / What you teach', type: 'text' },
      { key: 'Tech Comfort Level', label: 'Tech Comfort Level', type: 'select', options: ['Beginner', 'Intermediate', 'Advanced'] },
      { key: 'Goals', label: 'Goals', type: 'textarea' },
    ],
    format: (vals) => `# About Me\n\n## Role\n${vals['Role'] || ''}\n\n## Name\n${vals['Name'] || ''}\n\n## Tech Comfort Level\n${vals['Tech Comfort Level'] || 'Intermediate'}\n\n## Goals\n${vals['Goals'] || ''}\n\n## Preferences\n<!-- Add personal workflow preferences as you discover them -->\n`
  },
  {
    file: 'work.md', title: 'Your Workspace',
    fields: [
      { key: 'Student Devices', label: 'Hardware / Student Devices', type: 'textarea' },
      { key: 'Teaching Tools', label: 'Software / Teaching Tools', type: 'textarea' },
      { key: 'Constraints', label: 'Constraints', type: 'textarea' },
    ],
    format: (vals) => `# Work Environment\n\n## Student Devices\n${vals['Student Devices'] || 'Not specified'}\n\n## Teaching Tools\n${vals['Teaching Tools'] || ''}\n\n## Constraints\n${vals['Constraints'] || 'None specified'}\n\n## Deployment\n<!-- Updated as you configure integrations -->\n`
  },
  {
    file: 'team.md', title: 'Your Team',
    fields: [
      { key: 'Collaborators', label: 'Collaborators', type: 'textarea' },
      { key: 'Other Users', label: 'Other Users', type: 'textarea' },
    ],
    format: (vals) => `# Team\n\n## Collaborators\n${vals['Collaborators'] || 'None currently'}\n\n## Other Users\n${vals['Other Users'] || 'Just me'}\n\n## Collaboration Norms\n<!-- How does your team communicate? -->\n`
  },
  {
    file: 'current_priorities.md', title: 'Your Priorities',
    fields: [
      { key: 'Current Work', label: 'Current Work', type: 'textarea' },
      { key: 'Automation Goals', label: 'Automation Goals', type: 'textarea' },
    ],
    format: (vals) => {
      let md = '# Current Priorities\n\n';
      const work = vals['Current Work'] || '';
      if (work) {
        const items = work.split(/\n/).map(s => s.trim()).filter(Boolean);
        items.forEach((item, i) => { md += `## Priority ${i + 1}: ${item}\n**Status:** In Progress\n\n`; });
      } else {
        md += '## Priority 1: [Your Top Priority]\n**Goal:** [What does success look like?]\n**Status:** Not Started\n\n';
      }
      if (vals['Automation Goals']) md += `## Automation Wishlist\n${vals['Automation Goals']}\n`;
      return md;
    }
  },
  {
    file: 'rules.md', title: 'Communication Style',
    fields: [
      { key: 'Tone', label: 'Tone', type: 'select', options: ['Casual', 'Professional', 'Technical'] },
      { key: 'Detail Level', label: 'Detail Level', type: 'select', options: ['Concise', 'Mid-detail', 'Detailed'] },
      { key: 'Custom Rules', label: 'Custom Rules', type: 'textarea' },
    ],
    format: (vals) => {
      const tone = vals['Tone'] || 'Casual';
      const detailMap = { 'Concise': 'Concise one-liners', 'Mid-detail': 'Mid-detail', 'Detailed': 'Detailed explanations' };
      const detail = detailMap[vals['Detail Level']] || 'Mid-detail';
      let md = `# Communication & Operating Rules\n\n## Communication Style\n- **Tone:** ${tone}\n- **Format:** ${detail}\n- **Decision-making:** Present options for me to choose from\n\n## Hard Rules\n- Never modify files outside the user's home directory\n- Once a task has been agreed upon, execute without asking for further permissions\n- Never commit secrets, API keys, or credentials to version control\n`;
      if (vals['Custom Rules']) {
        md += `\n## Custom Rules\n${vals['Custom Rules'].split(/\n/).map(r => r.trim()).filter(Boolean).map(r => r.startsWith('- ') ? r : `- ${r}`).join('\n')}\n`;
      }
      return md;
    }
  }
];

function parseContextMarkdown(content, fileConfig) {
  const vals = {};
  for (const field of fileConfig.fields) {
    const key = field.key;
    let val = '';

    // Special-case fields that aren't under their own ## header
    if (key === 'Tone') {
      const m = content.match(/\*\*Tone:\*\*\s*(.+)/);
      val = m ? m[1].trim() : '';
    } else if (key === 'Detail Level') {
      const m = content.match(/\*\*Format:\*\*\s*(.+)/);
      if (m) {
        const raw = m[1].trim();
        if (raw.includes('Concise')) val = 'Concise';
        else if (raw.includes('Mid')) val = 'Mid-detail';
        else if (raw.includes('Detailed')) val = 'Detailed';
        else val = raw;
      } else { val = 'Mid-detail'; }
    } else if (key === 'Current Work') {
      // Extract priority titles from "## Priority N: Title" patterns
      const priorities = [];
      const re = /##\s+Priority\s+\d+:\s*(.+)/g;
      let pm;
      while ((pm = re.exec(content)) !== null) priorities.push(pm[1].trim());
      val = priorities.join('\n');
    } else if (key === 'Automation Goals') {
      const am = content.match(/##\s+Automation Wishlist[^\n]*\n([\s\S]*?)(?=\n##\s|$)/);
      val = am ? am[1].trim() : '';
    } else {
      // Standard: find ## Key header and grab content until next ## or end
      const pattern = new RegExp(`##\\s+${key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^\\n]*\\n([\\s\\S]*?)(?=\\n##\\s|$)`);
      const match = content.match(pattern);
      val = match ? match[1].trim() : '';
    }

    // Strip markdown comments and list-item prefixes for clean display
    val = val.replace(/<!--[\s\S]*?-->/g, '').trim();
    vals[key] = val;
  }
  return vals;
}

async function loadProfileData() {
  const container = document.getElementById('profileEditorContent');
  const loading = document.getElementById('profileLoading');
  if (loading) loading.style.display = 'block';

  try {
    const results = await Promise.all(
      profileFileConfig.map(cfg =>
        fetch(`/api/setup/context/${cfg.file}`).then(r => r.json()).catch(() => ({ content: '', exists: false }))
      )
    );

    let html = '';
    profileFileConfig.forEach((cfg, i) => {
      const data = results[i];
      const vals = data.exists ? parseContextMarkdown(data.content || '', cfg) : {};
      const fileId = cfg.file.replace('.md', '').replace('_', '-');

      html += `<div class="profile-section">`;
      html += `<div class="profile-section-title">${cfg.title}</div>`;

      for (const field of cfg.fields) {
        const val = vals[field.key] || '';
        const inputId = `profile-${fileId}-${field.key.toLowerCase().replace(/\s+/g, '-')}`;

        html += `<div class="profile-field">`;
        html += `<label for="${inputId}">${field.label}</label>`;

        if (field.type === 'text') {
          html += `<input type="text" id="${inputId}" data-file="${cfg.file}" data-key="${field.key}" value="${val.replace(/"/g, '&quot;')}">`;
        } else if (field.type === 'textarea') {
          html += `<textarea id="${inputId}" data-file="${cfg.file}" data-key="${field.key}" rows="2">${val.replace(/</g, '&lt;')}</textarea>`;
        } else if (field.type === 'select') {
          html += `<select id="${inputId}" data-file="${cfg.file}" data-key="${field.key}">`;
          for (const opt of field.options) {
            const selected = val === opt ? ' selected' : '';
            html += `<option value="${opt}"${selected}>${opt}</option>`;
          }
          html += `</select>`;
        }
        html += `</div>`;
      }

      html += `<div class="profile-section-actions">`;
      html += `<button class="profile-save-btn" onclick="saveProfileSection('${cfg.file}')" type="button">Save</button>`;
      html += `</div></div>`;
    });

    html += `<div class="profile-section-actions" style="margin-top:8px;"><button class="reset-btn" onclick="rerunInterview()" type="button">Re-run Interview</button></div>`;

    container.innerHTML = html;
    profileDataLoaded = true;
  } catch (err) {
    container.innerHTML = `<div class="profile-loading" style="color:var(--error)">Failed to load profile data: ${err.message}</div>`;
  }
}

async function saveProfileSection(filename) {
  const cfg = profileFileConfig.find(c => c.file === filename);
  if (!cfg) return;

  const vals = {};
  for (const field of cfg.fields) {
    const fileId = cfg.file.replace('.md', '').replace('_', '-');
    const inputId = `profile-${fileId}-${field.key.toLowerCase().replace(/\s+/g, '-')}`;
    const el = document.getElementById(inputId);
    vals[field.key] = el ? el.value : '';
  }

  const content = cfg.format(vals);
  try {
    const resp = await fetch('/api/setup/save-context', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: filename, content })
    });
    if (!resp.ok) throw new Error(`Server returned ${resp.status}`);
    showToast(`Saved ${cfg.title}`, 'success');
  } catch (err) {
    showToast(`Failed to save: ${err.message}`, 'error');
  }
}

async function rerunInterview() {
  closeSettings();
  localStorage.removeItem('ea-setup-complete');
  profileDataLoaded = false;
  try {
    const resp = await fetch('/api/setup/status');
    const data = await resp.json();
    data.phase = 'interview';
    showSetupWizard(data);
  } catch (err) {
    // Fallback: construct minimal setup data
    showSetupWizard({ phase: 'interview', dependencies: {}, auth: {} });
  }
}

function showResetConfirm(scope) {
  const el = document.getElementById(`resetConfirm${scope.charAt(0).toUpperCase() + scope.slice(1)}`);
  if (el) el.classList.add('visible');
}

function hideResetConfirm(scope) {
  const el = document.getElementById(`resetConfirm${scope.charAt(0).toUpperCase() + scope.slice(1)}`);
  if (el) el.classList.remove('visible');
}

function showFactoryResetModal() {
  hideResetConfirm('factory');
  const modal = document.getElementById('factoryResetModal');
  const input = document.getElementById('factoryResetInput');
  const btn = document.getElementById('factoryResetConfirmBtn');
  input.value = '';
  btn.disabled = true;
  modal.classList.add('open');
  input.focus();
  input.oninput = () => { btn.disabled = input.value !== 'RESET'; };
}

function closeFactoryResetModal() {
  document.getElementById('factoryResetModal').classList.remove('open');
  document.getElementById('factoryResetInput').value = '';
}

async function performReset(scope) {
  if (scope === 'factory') {
    const input = document.getElementById('factoryResetInput');
    if (input.value !== 'RESET') return;
    closeFactoryResetModal();
  }

  hideResetConfirm(scope);

  if (scope === 'preferences') {
    ['ea-sidebar-width', 'ea-cmd-history', 'ea-theme', 'ea-notification-history'].forEach(k => localStorage.removeItem(k));
    showToast('Preferences reset to defaults', 'success');
    setTimeout(() => location.reload(), 800);
    return;
  }

  try {
    const resp = await fetch('/api/setup/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scope })
    });
    if (!resp.ok) throw new Error(`Server returned ${resp.status}`);
    const result = await resp.json();

    if (scope === 'history') {
      const archived = result.results?.history?.archived || 0;
      showToast(`Chat history cleared — ${archived} session${archived !== 1 ? 's' : ''} archived`, 'success');
      // Reload sessions in sidebar
      if (typeof loadSessions === 'function') loadSessions();
    } else if (scope === 'factory') {
      // Clear all localStorage and reload
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('ea-')) keysToRemove.push(key);
      }
      keysToRemove.forEach(k => localStorage.removeItem(k));
      localStorage.removeItem('ea-setup-complete');
      showToast('Factory reset complete — reloading...', 'info');
      setTimeout(() => location.reload(), 800);
    }
  } catch (err) {
    showToast(`Reset failed: ${err.message}`, 'error');
  }
}

// ===== FOLDER CLEANUP =====
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

async function loadFolderStats() {
  try {
    const resp = await fetch('/api/folders/stats');
    if (!resp.ok) throw new Error(`${resp.status}`);
    const stats = await resp.json();
    for (const [folder, data] of Object.entries(stats)) {
      const el = document.getElementById(`folderStats${folder.charAt(0).toUpperCase() + folder.slice(1)}`);
      if (!el) continue;
      if (data.files === 0) {
        el.textContent = 'Empty';
        el.className = 'folder-stats empty';
      } else {
        el.textContent = `${data.files} file${data.files !== 1 ? 's' : ''}, ${formatBytes(data.size)}`;
        el.className = 'folder-stats loaded';
      }
    }
  } catch (err) {
    ['Temp', 'Assets', 'Projects'].forEach(name => {
      const el = document.getElementById(`folderStats${name}`);
      if (el) { el.textContent = 'Unable to load'; el.className = 'folder-stats'; }
    });
  }
}

async function clearFolder(folder) {
  hideResetConfirm(folder);
  try {
    const resp = await fetch('/api/folders/clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder })
    });
    if (!resp.ok) throw new Error(`Server returned ${resp.status}`);
    const result = await resp.json();
    const labels = { temp: 'Temp files', assets: 'Assets', projects: 'Projects' };
    showToast(`${labels[folder] || folder} cleared — ${result.deleted} item${result.deleted !== 1 ? 's' : ''} deleted`, 'success');
    loadFolderStats();
  } catch (err) {
    showToast(`Failed to clear ${folder}: ${err.message}`, 'error');
  }
}

function showCompleteResetModal() {
  hideResetConfirm('complete');
  const modal = document.getElementById('completeResetModal');
  const input = document.getElementById('completeResetInput');
  const btn = document.getElementById('completeResetConfirmBtn');
  input.value = '';
  btn.disabled = true;
  modal.classList.add('open');
  input.focus();
  input.oninput = () => { btn.disabled = input.value !== 'RESET'; };
}

function closeCompleteResetModal() {
  document.getElementById('completeResetModal').classList.remove('open');
  document.getElementById('completeResetInput').value = '';
}

async function performCompleteReset() {
  const input = document.getElementById('completeResetInput');
  if (input.value !== 'RESET') return;
  closeCompleteResetModal();
  try {
    const resp = await fetch('/api/setup/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scope: 'complete' })
    });
    if (!resp.ok) throw new Error(`Server returned ${resp.status}`);
    // Clear ALL localStorage
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) keysToRemove.push(key);
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
    showToast('Complete reset done — reloading...', 'info');
    setTimeout(() => location.reload(), 800);
  } catch (err) {
    showToast(`Complete reset failed: ${err.message}`, 'error');
  }
}

// ===== IMAGE LIGHTBOX =====
let _lightboxPrevFocus = null;

function openLightbox(src) {
  _lightboxPrevFocus = document.activeElement;
  const overlay = document.getElementById('imageLightbox');
  const img = document.getElementById('lightboxImg');
  img.src = src;
  overlay.classList.add('open');
  // Focus the close button
  const closeBtn = overlay.querySelector('button[aria-label="Close preview"]');
  if (closeBtn) closeBtn.focus();
}

function closeLightbox() {
  document.getElementById('imageLightbox').classList.remove('open');
  if (_lightboxPrevFocus) { _lightboxPrevFocus.focus(); _lightboxPrevFocus = null; }
}

// ===== CONVERSATION EXPORT =====
function exportConversation() {
  const tab = getActiveTab();
  if (!tab || tab.messages.length === 0) {
    addMessage('No messages to export.', 'system');
    return;
  }

  let md = `# ${tab.title}\n\n`;
  md += `*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;

  for (const msg of tab.messages) {
    if (msg.role === 'user') {
      md += `## You\n\n${msg.content}\n\n`;
    } else if (msg.role === 'assistant') {
      md += `## Assistant\n\n${msg.content}\n\n`;
    }
    md += '---\n\n';
  }

  const blob = new Blob([md], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${tab.title.replace(/[^a-z0-9]/gi, '_').slice(0, 40)}_export.md`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ===== DIFF RENDERING =====
function renderDiff(text) {
  if (!(/(^|\n)--- /.test(text)) || !(/(^|\n)\+\+\+ /.test(text))) return null;
  const lines = text.split('\n');
  let html = '<div class="diff-block">';
  for (const line of lines) {
    if (line.startsWith('--- ') || line.startsWith('+++ ')) {
      html += `<div class="diff-header">${escapeHtml(line)}</div>`;
    } else if (line.startsWith('+')) {
      html += `<div class="diff-line added">${escapeHtml(line)}</div>`;
    } else if (line.startsWith('-')) {
      html += `<div class="diff-line removed">${escapeHtml(line)}</div>`;
    } else if (line.startsWith('@@')) {
      html += `<div class="diff-header">${escapeHtml(line)}</div>`;
    } else {
      html += `<div class="diff-line context">${escapeHtml(line)}</div>`;
    }
  }
  html += '</div>';
  return html;
}

// ===== EVENT DELEGATION =====
chatContainer.addEventListener('click', e => {
  // Copy button on code blocks
  const copyBtn = e.target.closest('.copy-btn');
  if (copyBtn) {
    const container = copyBtn.closest('.code-container');
    if (container) {
      const raw = container.querySelector('.raw-code')?.textContent;
      if (raw) {
        copyToClipboard(raw, copyBtn);
      }
    }
    return;
  }

  // Image lightbox on attachment images
  const img = e.target.closest('.attachment-img');
  if (img) {
    openLightbox(img.src);
    return;
  }
});

// ===== MODEL BADGE =====
function updateModelBadge() {
  const badge = document.getElementById('modelBadge');
  const model = settings.model || 'default';
  const labels = {
    '': 'default',
    'gemini-3.1-pro-preview': 'gemini-3.1-pro',
    'gemini-2.5-pro': 'gemini-2.5-pro',
    'gemini-2.5-flash': 'gemini-2.5-flash',
  };
  badge.textContent = labels[settings.model] || model;
}

// ===== TOKEN USAGE =====
async function loadTokenUsage() {
  try {
    const res = await fetch('/api/token-usage');
    const data = await res.json();
    const t = data.total || {};
    document.getElementById('tokenTotal').textContent = (t.total_tokens || 0).toLocaleString();
    document.getElementById('tokenIn').textContent = (t.input_tokens || 0).toLocaleString();
    document.getElementById('tokenOut').textContent = (t.output_tokens || 0).toLocaleString();
    document.getElementById('tokenRequests').textContent = (t.requests || 0).toLocaleString();
  } catch {}
}

async function resetTokenUsage() {
  showConfirmModal(
    'Reset Token Usage',
    'Reset all token usage counters? This cannot be undone.',
    async function() {
      await fetch('/api/token-usage', { method: 'DELETE' });
      loadTokenUsage();
    },
    { confirmText: 'Reset' }
  );
}

// ===== SESSION TAGS =====
function setSessionTag(sessionId, tag) {
  if (!tag || sessionTags[sessionId] === tag) {
    delete sessionTags[sessionId]; // Clear or toggle off
  } else {
    sessionTags[sessionId] = tag;
  }
  safeSet('ea-session-tags', JSON.stringify(sessionTags));
  closeAllTagPickers();
  loadSessions();
}

function toggleTagPicker(sessionId, e) {
  e.stopPropagation();
  closeAllTagPickers();
  const item = e.target.closest('.sidebar-item') || e.target.closest('[data-session-id]');
  if (!item) return;

  const picker = document.createElement('div');
  picker.className = 'tag-picker open';
  picker.dataset.sessionId = sessionId;
  picker.innerHTML = ['red','blue','green','yellow','purple'].map(color =>
    `<span class="session-tag tag-${color}" data-tag-color="${color}">${color}</span>`
  ).join('') + `<span class="session-tag" style="border:1px dashed var(--text-muted);color:var(--text-muted);" data-tag-color="">clear</span>`;

  picker.addEventListener('click', ev => {
    ev.stopPropagation();
    const tagEl = ev.target.closest('[data-tag-color]');
    if (tagEl) {
      setSessionTag(sessionId, tagEl.dataset.tagColor || undefined);
    }
  });

  item.appendChild(picker);
  // Close on outside click
  setTimeout(() => {
    document.addEventListener('click', closeAllTagPickers, { once: true });
  }, 0);
}

function closeAllTagPickers() {
  document.querySelectorAll('.tag-picker').forEach(p => p.remove());
}

function filterSessions(tag) {
  activeTagFilter = tag;
  // Update filter button states
  document.querySelectorAll('.sidebar-filter-btn').forEach(btn => {
    btn.classList.toggle('active', (tag === 'all' && !btn.dataset.tag) || btn.dataset.tag === tag);
  });
  loadSessions();
}

// ===== NOTIFICATIONS =====
function requestNotificationPermission() {
  if (settings.notifications === 'on' && 'Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

function sendNotification(title, body) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;
  try {
    const n = new Notification(title, {
      body: body,
      icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🤖</text></svg>',
      tag: 'ea-completion',
    });
    n.onclick = () => { window.focus(); n.close(); };
  } catch {}
}

// Request permission on load if enabled
requestNotificationPermission();

// ===== TOAST NOTIFICATIONS =====
const toastContainer = document.getElementById('toastContainer');
const toastIcons = { success: '&#10003;', error: '&#10007;', warning: '&#9888;', info: '&#8505;' };
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

// Notification log for the notification center
const notificationLog = [];
let notificationUnread = 0;
let notificationCenterOpen = false;

// Severity-based default durations
const toastDurations = { info: 10000, success: 10000, warning: 12000, error: 15000 };

function showToast(message, type = 'info', opts = {}) {
  // Support legacy 3rd-arg as number (duration)
  if (typeof opts === 'number') opts = { duration: opts };
  const { duration = toastDurations[type] || 10000, id, sticky = false, progress = true } = opts;

  // Log to notification center
  addNotificationEntry(message, type);

  // If notification center is open, don't show toast visually
  if (notificationCenterOpen) return null;

  // Deduplication: replace existing toast with same id
  if (id) {
    const existing = toastContainer.querySelector(`[data-toast-id="${CSS.escape(id)}"]`);
    if (existing) dismissToast(existing);
  }

  // Max 3 visible
  const visible = toastContainer.querySelectorAll('.toast:not(.removing)');
  if (visible.length >= 3) {
    dismissToast(visible[0]);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.setAttribute('role', 'status');
  if (id) toast.dataset.toastId = id;

  const progressHtml = (!sticky && progress)
    ? `<div class="toast-progress ${type}" style="animation-duration: ${duration}ms;"></div>`
    : '';

  toast.innerHTML = `
    <span class="toast-icon ${type}">${toastIcons[type] || toastIcons.info}</span>
    <span class="toast-message">${escapeHtml(message)}</span>
    <button class="toast-close" onclick="dismissToast(this.parentElement)" aria-label="Dismiss">&times;</button>
    ${progressHtml}
  `;
  toastContainer.appendChild(toast);

  // Hover pause/resume for non-sticky toasts
  if (!sticky) {
    let remaining = duration;
    let startedAt = Date.now();

    toast._timeout = setTimeout(() => dismissToast(toast), duration);

    toast.addEventListener('mouseenter', () => {
      clearTimeout(toast._timeout);
      remaining -= (Date.now() - startedAt);
      toast.classList.add('paused');
    });

    toast.addEventListener('mouseleave', () => {
      startedAt = Date.now();
      toast.classList.remove('paused');
      toast._timeout = setTimeout(() => dismissToast(toast), Math.max(remaining, 500));
      // Restart progress bar with remaining time
      const bar = toast.querySelector('.toast-progress');
      if (bar) {
        const pct = (remaining / duration) * 100;
        bar.style.animation = 'none';
        bar.offsetHeight; // reflow
        bar.style.width = pct + '%';
        bar.style.animation = `toastProgress ${remaining}ms linear forwards`;
      }
    });
  }

  return toast;
}

function dismissToast(toast) {
  if (!toast || toast.classList.contains('removing')) return;
  clearTimeout(toast._timeout);
  toast.classList.add('removing');
  if (prefersReducedMotion.matches) {
    toast.remove();
  } else {
    setTimeout(() => toast.remove(), 250);
  }
}

// ===== NOTIFICATION CENTER =====
function addNotificationEntry(message, type) {
  notificationLog.unshift({ message, type, time: Date.now() });
  if (notificationLog.length > 50) notificationLog.length = 50;

  if (!notificationCenterOpen) {
    notificationUnread++;
    updateNotificationBadge();
  }

  if (notificationCenterOpen) renderNotificationList();
}

function updateNotificationBadge() {
  const badge = document.getElementById('statusBadge');
  if (notificationUnread > 0) {
    badge.textContent = notificationUnread > 99 ? '99+' : notificationUnread;
    badge.style.display = '';
  } else {
    badge.style.display = 'none';
  }
}

function toggleNotificationCenter() {
  const panel = document.getElementById('notificationCenter');
  notificationCenterOpen = !notificationCenterOpen;
  panel.classList.toggle('open', notificationCenterOpen);

  if (notificationCenterOpen) {
    notificationUnread = 0;
    updateNotificationBadge();
    renderNotificationList();
    // Hide active toasts
    toastContainer.style.display = 'none';
  } else {
    // Show toasts again
    toastContainer.style.display = '';
  }
}

function renderNotificationList() {
  const list = document.getElementById('notificationList');
  if (notificationLog.length === 0) {
    list.innerHTML = '<div class="notification-center-empty">No notifications</div>';
    return;
  }
  list.innerHTML = notificationLog.map(entry => {
    const icon = toastIcons[entry.type] || toastIcons.info;
    return `<div class="notification-entry">
      <span class="notif-icon ${entry.type}">${icon}</span>
      <div class="notif-body">
        <div class="notif-message">${escapeHtml(entry.message)}</div>
        <div class="notif-time">${relativeTime(entry.time)}</div>
      </div>
    </div>`;
  }).join('');
}

function clearNotifications() {
  notificationLog.length = 0;
  notificationUnread = 0;
  updateNotificationBadge();
  renderNotificationList();
}

function relativeTime(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return diff + 's ago';
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  return Math.floor(diff / 86400) + 'd ago';
}

// Update relative times periodically
setInterval(() => {
  if (notificationCenterOpen) renderNotificationList();
}, 15000);

// Close notification center on outside click
document.addEventListener('click', e => {
  if (!notificationCenterOpen) return;
  const panel = document.getElementById('notificationCenter');
  const bell = document.getElementById('statusBell');
  if (!panel.contains(e.target) && !bell.contains(e.target)) {
    toggleNotificationCenter();
  }
});

// ===== STATUS BAR =====
let statusBarConnected = true;

function formatTokenCount(n) {
  if (n == null || n === 0) return '0';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function updateStatusBar() {
  // Model
  const modelEl = document.getElementById('statusModel');
  const modelLabels = {
    '': 'default',
    'gemini-3.1-pro-preview': 'gemini-3.1-pro',
    'gemini-2.5-pro': 'gemini-2.5-pro',
    'gemini-2.5-flash': 'gemini-2.5-flash',
  };
  modelEl.textContent = modelLabels[settings.model] || settings.model || 'default';

  // Approval mode
  const approvalEl = document.getElementById('statusApproval');
  approvalEl.textContent = settings.approvalMode === 'yolo' ? 'Auto' : 'Plan';

  // Connection dot
  const dot = document.getElementById('statusBarDot');
  dot.className = statusBarConnected ? 'status-dot connected' : 'status-dot disconnected';
}

function setConnectionStatus(connected) {
  statusBarConnected = connected;
  const dot = document.getElementById('statusBarDot');
  dot.className = connected ? 'status-dot connected' : 'status-dot disconnected';
}

async function pollTokenUsage() {
  try {
    const res = await fetch('/api/token-usage');
    const data = await res.json();
    const t = data.total || {};
    const input = t.input_tokens || 0;
    const output = t.output_tokens || 0;
    document.getElementById('statusTokenLabel').innerHTML =
      `&#8593;${formatTokenCount(input)} &#8595;${formatTokenCount(output)}`;
    // Also update the full token bar
    document.getElementById('tokenTotal').textContent = (t.total_tokens || 0).toLocaleString();
    document.getElementById('tokenIn').textContent = input.toLocaleString();
    document.getElementById('tokenOut').textContent = output.toLocaleString();
    document.getElementById('tokenRequests').textContent = (t.requests || 0).toLocaleString();
    setConnectionStatus(true);
  } catch {
    setConnectionStatus(false);
  }
}

async function resetTokenUsageFromBar() {
  showToast('Resetting token usage...', 'info', { duration: 2000, id: 'token-reset' });
  try {
    await fetch('/api/token-usage', { method: 'DELETE' });
    await pollTokenUsage();
    showToast('Token usage reset', 'info', { id: 'token-reset' });
  } catch {
    showToast('Failed to reset token usage', 'error', { id: 'token-reset' });
  }
}

// Start token polling (every 30s)
setInterval(pollTokenUsage, 30000);

    // ===== COMMAND PALETTE =====
const commands = [
  { id: 'new-chat', label: 'New Chat', icon: 'plus', shortcut: 'Ctrl+N', description: 'Open a new conversation tab', action: () => createNewTab() },
  { id: 'archive', label: 'Archive Session', icon: 'archive', shortcut: 'Ctrl+Shift+A', description: 'Archive the current session', action: () => {
    const tab = getActiveTab();
    if (tab && tab.sessionId) { archiveSession(tab.sessionId); showToast('Session archived', 'success'); }
    else showToast('No session to archive', 'warning');
  }},
  { id: 'archive-all', label: 'Archive All Sessions', icon: 'trash-2', description: 'Archive every session in the sidebar', action: () => { const items = document.querySelectorAll('#sessionList .sidebar-item'); if (items.length === 0) { showToast('No sessions to archive', 'warning'); } else { archiveAllSessions(); showToast('All sessions archived', 'success'); } } },
  { id: 'toggle-sidebar', label: 'Toggle Sidebar', icon: 'panel-left', shortcut: 'Ctrl+/', description: 'Show or hide the sidebar', action: () => toggleSidebar() },
  { id: 'settings', label: 'Open Settings', icon: 'settings', description: 'Change model, theme, and preferences', action: () => openSettings() },
  { id: 'export', label: 'Export Conversation', icon: 'download', description: 'Download chat as markdown', action: () => { const tab = getActiveTab(); if (!tab || tab.messages.length === 0) { showToast('No conversation to export', 'warning'); } else { exportConversation(); showToast('Conversation exported', 'success'); } } },
  { id: 'toggle-theme', label: 'Toggle Theme', icon: 'sun', description: 'Switch between dark and light mode', action: () => toggleTheme() },
  { id: 'toggle-approval', label: 'Toggle Approval Mode', icon: 'shield', description: 'Switch between auto and plan mode', action: () => { toggleApprovalMode(); showToast(`Mode: ${settings.approvalMode}`, 'info'); } },
  { id: 'shutdown', label: 'Shut Down Server', icon: 'power', description: 'Stop the assistant server', action: () => { confirmShutdown(); } },
];

let cmdPaletteIndex = 0;

function toggleCommandPalette() {
  const palette = document.getElementById('cmdPalette');
  if (palette.classList.contains('open')) { closeCommandPalette(); }
  else { openCommandPalette(); }
}

function openCommandPalette() {
  const palette = document.getElementById('cmdPalette');
  const backdrop = document.getElementById('cmdPaletteBackdrop');
  const input = document.getElementById('cmdPaletteInput');
  palette.classList.add('open');
  backdrop.classList.add('open');
  input.value = '';
  cmdPaletteIndex = 0;
  renderCommandList('');
  trapFocus(palette);
}

function closeCommandPalette() {
  const palette = document.getElementById('cmdPalette');
  releaseFocus(palette);
  palette.classList.remove('open');
  document.getElementById('cmdPaletteBackdrop').classList.remove('open');
  messageInput.focus();
}

function renderCommandList(query) {
  const list = document.getElementById('cmdPaletteList');
  const input = document.getElementById('cmdPaletteInput');
  const q = query.toLowerCase().trim();

  // Filter with match indices
  let filtered;
  if (q) {
    filtered = [];
    for (const c of commands) {
      const indices = fuzzyMatch(c.label.toLowerCase(), q);
      if (indices) filtered.push({ cmd: c, indices });
    }
  } else {
    filtered = commands.map(c => ({ cmd: c, indices: null }));
  }

  if (filtered.length === 0) {
    list.innerHTML = '<div class="command-palette-empty">No matching commands</div>';
    input.removeAttribute('aria-activedescendant');
    return;
  }

  // Split into "Recently Used" and "All Commands" groups
  const history = getCmdHistory();
  const recentItems = [];
  const otherItems = [];
  for (const item of filtered) {
    if (history.includes(item.cmd.id)) {
      recentItems.push(item);
    } else {
      otherItems.push(item);
    }
  }
  // Sort recent items by history order
  recentItems.sort((a, b) => history.indexOf(a.cmd.id) - history.indexOf(b.cmd.id));

  const allItems = [...recentItems, ...otherItems];

  // Clamp index
  if (cmdPaletteIndex >= allItems.length) cmdPaletteIndex = allItems.length - 1;
  if (cmdPaletteIndex < 0) cmdPaletteIndex = 0;

  // Update aria-activedescendant
  input.setAttribute('aria-activedescendant', `cmd-item-${cmdPaletteIndex}`);

  // Build HTML with group separators
  let html = '';
  let globalIdx = 0;

  if (recentItems.length > 0) {
    html += '<div class="command-palette-separator" role="separator"><span>Recently Used</span></div>';
    for (const item of recentItems) {
      html += renderCommandItem(item, globalIdx, true);
      globalIdx++;
    }
  }

  if (otherItems.length > 0) {
    if (recentItems.length > 0) {
      html += '<div class="command-palette-separator" role="separator"><span>All Commands</span></div>';
    }
    for (const item of otherItems) {
      html += renderCommandItem(item, globalIdx, false);
      globalIdx++;
    }
  }

  list.innerHTML = html;
  createIconsIn(list);
}

function renderCommandItem(item, index, inHistory) {
  const cmd = item.cmd;
  const isActive = index === cmdPaletteIndex;
  const labelHtml = item.indices ? highlightFuzzyMatch(cmd.label, item.indices) : escapeHtml(cmd.label);
  const removeBtn = inHistory
    ? `<button class="cmd-remove-history" onclick="event.stopPropagation(); removeFromCmdHistory('${cmd.id}'); renderCommandList(document.getElementById('cmdPaletteInput').value)" title="Remove from history" aria-label="Remove from recent">&times;</button>`
    : '';
  return `
    <div class="command-palette-item${isActive ? ' active' : ''}"
         id="cmd-item-${index}"
         role="option" aria-selected="${isActive}"
         data-cmd-id="${cmd.id}"
         onmouseenter="cmdPaletteIndex=${index}; renderCommandList(document.getElementById('cmdPaletteInput').value)"
         onclick="executeCommand('${cmd.id}')">
      <span class="cmd-icon"><i data-lucide="${cmd.icon}"></i></span>
      <span class="cmd-label">${labelHtml}</span>
      ${cmd.description ? `<span class="cmd-description">${escapeHtml(cmd.description)}</span>` : ''}
      ${cmd.shortcut ? `<span class="cmd-shortcut">${cmd.shortcut}</span>` : ''}
      ${removeBtn}
    </div>`;
}

function fuzzyMatch(str, query) {
  let qi = 0;
  const indices = [];
  for (let i = 0; i < str.length && qi < query.length; i++) {
    if (str[i] === query[qi]) {
      indices.push(i);
      qi++;
    }
  }
  return qi === query.length ? indices : null;
}

function highlightFuzzyMatch(label, indices) {
  const indexSet = new Set(indices);
  let result = '';
  for (let i = 0; i < label.length; i++) {
    if (indexSet.has(i)) {
      result += `<strong>${escapeHtml(label[i])}</strong>`;
    } else {
      result += escapeHtml(label[i]);
    }
  }
  return result;
}

function executeCommand(id) {
  const cmd = commands.find(c => c.id === id);
  if (cmd) {
    addToCmdHistory(id);
    closeCommandPalette();
    cmd.action();
  }
}

// Command palette input handling
document.getElementById('cmdPaletteInput').addEventListener('input', e => {
  cmdPaletteIndex = 0;
  renderCommandList(e.target.value);
});

document.getElementById('cmdPaletteInput').addEventListener('keydown', e => {
  const q = e.target.value.toLowerCase().trim();
  // Rebuild filtered list to get count (same logic as renderCommandList)
  let filtered;
  if (q) {
    filtered = [];
    for (const c of commands) {
      const indices = fuzzyMatch(c.label.toLowerCase(), q);
      if (indices) filtered.push(c);
    }
  } else {
    filtered = [...commands];
  }
  // Reorder: recent first, then others
  const history = getCmdHistory();
  const recent = filtered.filter(c => history.includes(c.id)).sort((a, b) => history.indexOf(a.id) - history.indexOf(b.id));
  const others = filtered.filter(c => !history.includes(c.id));
  const allItems = [...recent, ...others];

  if (e.key === 'ArrowDown') {
    e.preventDefault();
    cmdPaletteIndex = Math.min(cmdPaletteIndex + 1, allItems.length - 1);
    renderCommandList(e.target.value);
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    cmdPaletteIndex = Math.max(cmdPaletteIndex - 1, 0);
    renderCommandList(e.target.value);
  } else if (e.key === 'Enter') {
    e.preventDefault();
    if (allItems[cmdPaletteIndex]) {
      executeCommand(allItems[cmdPaletteIndex].id);
    }
  }
});

// ===== ONBOARDING / WELCOME =====
function getOnboardingHTML() {
  return `<div class="onboarding">
    <h2>Welcome to Executive Assistant</h2>
    <p>Your AI-powered workspace, built on Gemini CLI. Here's a quick overview to get you started.</p>
    <div class="onboarding-grid">
      <div class="onboarding-card">
        <div class="card-icon"><i data-lucide="message-circle"></i></div>
        <h3>Start a Conversation</h3>
        <p>Type a message in the input box below to chat with your assistant. It can answer questions, run tasks, and manage files.</p>
      </div>
      <div class="onboarding-card">
        <div class="card-icon"><i data-lucide="folder-open"></i></div>
        <h3>Browse Your Files</h3>
        <p>The sidebar on the left has a file browser. Click any file to preview it, or use the search bar to find files quickly.</p>
      </div>
      <div class="onboarding-card">
        <div class="card-icon"><i data-lucide="history"></i></div>
        <h3>Manage Sessions</h3>
        <p>Your chat history is saved automatically. Resume past sessions from the sidebar, or archive ones you no longer need.</p>
      </div>
      <div class="onboarding-card">
        <div class="card-icon"><i data-lucide="palette"></i></div>
        <h3>Customize Your Workspace</h3>
        <p>Open Settings to choose your model and theme. Use Ctrl+K to open the command palette for quick access to any action.</p>
      </div>
    </div>
    <div class="onboarding-actions">
      <button class="onboarding-btn" onclick="dismissOnboarding()">Get Started</button>
    </div>
  </div>`;
}

function shouldShowOnboarding() {
  return safeGet('ea-onboarded') !== 'true';
}

function dismissOnboarding() {
  safeSet('ea-onboarded', 'true');
  chatContainer.innerHTML = getWelcomeHTML();
  createIconsIn(chatContainer);
  // Update settings dropdown
  document.getElementById('settingOnboarding').value = 'off';
}

function toggleOnboardingSetting(value) {
  if (value === 'on') {
    try { localStorage.removeItem('ea-onboarded'); } catch {}
    showToast('Onboarding will show on next new chat', 'info');
  } else {
    safeSet('ea-onboarded', 'true');
  }
}

// ===== SETUP WIZARD =====
let setupState = { phase: null, step: 1, data: {}, setupData: null };

function detectPlatform() {
  const ua = navigator.userAgent.toLowerCase();
  const platform = (navigator.platform || '').toLowerCase();
  if (platform.includes('win') || ua.includes('windows')) return 'windows';
  if (platform.includes('mac') || ua.includes('macintosh') || ua.includes('mac os')) return 'mac';
  return 'linux';
}

function showSetupWizard(setupData) {
  setupState.setupData = setupData;
  setupState.phase = setupData.phase;
  setupState.step = 1;
  setupState.data = {};
  // Render wizard into chatContainer
  chatContainer.innerHTML = '';
  const wizard = document.createElement('div');
  wizard.className = 'setup-wizard';
  wizard.setAttribute('role', 'region');
  wizard.setAttribute('aria-label', 'Setup Wizard');
  wizard.innerHTML = `
    <div class="setup-wizard-inner">
      <div class="setup-header">
        <h2>Welcome to Executive Assistant</h2>
        <p>Let's get everything set up. This takes about 5 minutes.</p>
      </div>
      <div class="setup-progress" id="setupProgress"></div>
      <div id="setupPhaseContent"></div>
    </div>`;
  chatContainer.appendChild(wizard);
  renderSetupProgress();
  renderSetupPhase();
  createIconsIn(wizard);
}

function renderSetupProgress() {
  const phases = [
    { key: 'dependencies', label: 'Install' },
    { key: 'auth', label: 'Connect' },
    { key: 'interview', label: 'Personalize' }
  ];
  const phaseOrder = ['dependencies', 'auth', 'interview'];
  const currentIdx = phaseOrder.indexOf(setupState.phase);
  const el = document.getElementById('setupProgress');
  if (!el) return;
  el.innerHTML = phases.map((p, i) => {
    let cls = '';
    if (i < currentIdx) cls = 'done';
    else if (i === currentIdx) cls = 'active';
    const dot = i < currentIdx ? '<i data-lucide="check" style="width:14px;height:14px"></i>' : (i + 1);
    return `
      <div class="setup-progress-step ${cls}">
        <span class="setup-progress-dot">${dot}</span>
        <span>${p.label}</span>
      </div>
      ${i < phases.length - 1 ? `<div class="setup-progress-line ${i < currentIdx ? 'done' : ''}"></div>` : ''}`;
  }).join('');
  createIconsIn(el);
}

function renderSetupPhase() {
  const container = document.getElementById('setupPhaseContent');
  if (!container) return;
  switch (setupState.phase) {
    case 'dependencies': renderDepPhase(container); break;
    case 'auth': renderAuthPhase(container); break;
    case 'interview': renderInterviewPhase(container); break;
    default: renderDepPhase(container);
  }
  createIconsIn(container);
}

// --- Phase 1: Dependencies ---
function renderDepPhase(container) {
  const deps = setupState.setupData?.dependencies || {};
  const platform = detectPlatform();
  const items = [
    { key: 'python', name: 'Python 3', required: true, ok: !!deps.python },
    { key: 'node', name: 'Node.js', required: true, ok: !!deps.node },
    { key: 'npm', name: 'npm', required: true, ok: !!deps.npm },
    { key: 'git', name: 'Git', required: false, ok: !!deps.git },
    { key: 'gemini', name: 'Gemini CLI', required: true, ok: !!deps.gemini },
  ];
  const allRequired = items.filter(d => d.required).every(d => d.ok);

  container.innerHTML = `
    <div class="setup-phase" role="group" aria-label="Dependencies check">
      <div class="setup-dep-list">
        ${items.map(d => `
          <div class="setup-dep-item ${d.ok ? 'ok' : 'missing'}">
            <div class="setup-dep-row">
              <span class="setup-dep-icon">
                <i data-lucide="${d.ok ? 'check-circle' : 'circle-alert'}" style="width:20px;height:20px"></i>
              </span>
              <span class="setup-dep-name">${d.name}</span>
              <span class="setup-dep-tag ${!d.required ? 'optional' : ''}">${d.ok ? 'Installed' : (d.required ? 'Required' : 'Recommended')}</span>
            </div>
            ${!d.ok ? `<div class="setup-dep-instructions">${getDepInstructions(d.key, platform)}</div>` : ''}
          </div>
        `).join('')}
      </div>
      ${platform === 'windows' && !allRequired ? `<div style="margin:8px 0 4px;padding:8px 12px;background:var(--bg-tertiary);border-radius:8px;font-size:0.82rem;color:var(--text-secondary);line-height:1.5;">
        <i data-lucide="info" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;color:var(--accent)"></i>
        After installing, close and reopen the assistant for changes to take effect.
      </div>` : ''}
      <div class="setup-actions">
        <span></span>
        <div style="display:flex;gap:8px;align-items:center;">
          <button class="setup-btn setup-btn-secondary" onclick="refreshSetupStatus()">
            <i data-lucide="refresh-cw" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>Refresh
          </button>
          ${allRequired ? `<button class="setup-btn setup-btn-primary" onclick="advanceSetupPhase('auth')">Continue</button>` : ''}
        </div>
      </div>
    </div>`;
}

function getDepInstructions(key, platform) {
  const instructions = {
    node: {
      windows: 'Download the installer from <a href="https://nodejs.org" target="_blank" rel="noopener">nodejs.org</a> and run it. This also installs npm.',
      mac: 'Run <code>brew install node</code> in Terminal, or download from <a href="https://nodejs.org" target="_blank" rel="noopener">nodejs.org</a>.',
      linux: 'Run <code>sudo apt install nodejs npm</code> (Debian/Ubuntu) or <code>sudo pacman -S nodejs npm</code> (Arch), or download from <a href="https://nodejs.org" target="_blank" rel="noopener">nodejs.org</a>.'
    },
    npm: {
      windows: 'npm is included with Node.js. Install Node.js first.',
      mac: 'npm is included with Node.js. Install Node.js first.',
      linux: 'npm is included with Node.js. Install Node.js first.'
    },
    git: {
      windows: 'Download from <a href="https://git-scm.com" target="_blank" rel="noopener">git-scm.com</a> and run the installer.<span class="platform-note">Optional — needed for version control features.</span>',
      mac: 'Run <code>xcode-select --install</code> or <code>brew install git</code>.<span class="platform-note">Optional — needed for version control features.</span>',
      linux: 'Run <code>sudo apt install git</code> or <code>sudo pacman -S git</code>.<span class="platform-note">Optional — needed for version control features.</span>'
    },
    gemini: {
      windows: 'After installing Node.js, open a terminal and run: <code>npm install -g @google/gemini-cli</code>',
      mac: 'After installing Node.js, open Terminal and run: <code>npm install -g @google/gemini-cli</code>',
      linux: 'After installing Node.js, open a terminal and run: <code>npm install -g @google/gemini-cli</code>'
    },
    python: {
      windows: 'Download from <a href="https://python.org" target="_blank" rel="noopener">python.org</a>.',
      mac: 'Run <code>brew install python3</code> or download from <a href="https://python.org" target="_blank" rel="noopener">python.org</a>.',
      linux: 'Run <code>sudo apt install python3</code> or <code>sudo pacman -S python</code>.'
    }
  };
  return instructions[key]?.[platform] || instructions[key]?.linux || '';
}

async function refreshSetupStatus() {
  try {
    showToast('Checking dependencies...', 'info', { id: 'setup-refresh', duration: 2000 });
    const res = await fetch('/api/setup/status');
    const data = await res.json();
    setupState.setupData = data;
    // If phase advanced (all deps met), auto-advance
    if (setupState.phase === 'dependencies' && data.phase !== 'dependencies') {
      advanceSetupPhase(data.phase);
      return;
    }
    // Re-render current phase
    renderSetupPhase();
    renderSetupProgress();
  } catch {
    showToast('Could not check setup status', 'error');
  }
}

function advanceSetupPhase(newPhase) {
  setupState.phase = newPhase;
  setupState.step = 1;
  renderSetupProgress();
  renderSetupPhase();
  // Focus the phase content for screen readers
  const content = document.getElementById('setupPhaseContent');
  if (content) content.focus();
}

// --- Phase 2: Authentication ---
function renderAuthPhase(container) {
  const platform = detectPlatform();
  const terminalInstructions = {
    windows: 'Press <strong>Win + R</strong>, type <code>cmd</code>, and press Enter',
    mac: 'Press <strong>Cmd + Space</strong>, type <code>Terminal</code>, and press Enter',
    linux: 'Press <strong>Ctrl + Alt + T</strong> or open Terminal from your applications'
  };
  container.innerHTML = `
    <div class="setup-phase" role="group" aria-label="Authentication">
      <div class="setup-auth-card">
        <h3 style="font-size:1.1rem;font-weight:600;color:var(--text-primary);margin-bottom:4px;">
          <i data-lucide="link" style="width:18px;height:18px;vertical-align:-3px;margin-right:6px;color:var(--accent)"></i>
          Let's connect your Google account
        </h3>
        <p style="font-size:0.88rem;color:var(--text-secondary);line-height:1.5;">
          The Gemini CLI needs access to your Google account to work. Follow these steps:
        </p>
        <div class="setup-auth-steps">
          <div class="setup-auth-step">
            <span class="setup-auth-step-num">1</span>
            <span class="setup-auth-step-text">Open a terminal: ${terminalInstructions[platform]}</span>
          </div>
          <div class="setup-auth-step">
            <span class="setup-auth-step-num">2</span>
            <span class="setup-auth-step-text">Run this command: <code>gemini auth login</code></span>
          </div>
          <div class="setup-auth-step">
            <span class="setup-auth-step-num">3</span>
            <span class="setup-auth-step-text">A browser window will open — sign in with your Google account and allow access.</span>
          </div>
          <div class="setup-auth-step">
            <span class="setup-auth-step-num">4</span>
            <span class="setup-auth-step-text">Come back here and click <strong>Verify Connection</strong> below.</span>
          </div>
        </div>
        <div class="setup-auth-result" id="setupAuthResult"></div>
      </div>
      ${platform === 'windows' ? `<div style="margin:8px 0 4px;padding:8px 12px;background:var(--bg-tertiary);border-radius:8px;font-size:0.82rem;color:var(--text-secondary);line-height:1.5;">
        <i data-lucide="info" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;color:var(--accent)"></i>
        If verification fails, close and reopen the assistant, then try again.
      </div>` : ''}
      <div class="setup-actions">
        <button class="setup-btn setup-btn-ghost" onclick="advanceSetupPhase('dependencies')">Back</button>
        <div style="display:flex;gap:8px;align-items:center;">
          <button class="setup-btn setup-btn-secondary" id="setupVerifyBtn" onclick="verifyAuth()">
            <i data-lucide="shield-check" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>Verify Connection
          </button>
        </div>
      </div>
    </div>`;
}

async function verifyAuth() {
  const btn = document.getElementById('setupVerifyBtn');
  const result = document.getElementById('setupAuthResult');
  if (!btn || !result) return;
  btn.disabled = true;
  btn.textContent = 'Verifying...';
  result.className = 'setup-auth-result';
  result.style.display = 'none';
  try {
    const res = await fetch('/api/setup/verify-auth', { method: 'POST' });
    const data = await res.json();
    if (data.authenticated) {
      result.className = 'setup-auth-result success';
      result.style.display = 'block';
      result.innerHTML = '<i data-lucide="check-circle" style="width:16px;height:16px;vertical-align:-3px;margin-right:6px"></i>Connected successfully! Advancing...';
      createIconsIn(result);
      setTimeout(() => advanceSetupPhase('interview'), 1200);
    } else {
      result.className = 'setup-auth-result error';
      result.style.display = 'block';
      const errorMsg = document.createTextNode(data.error || 'Not authenticated yet. Complete the steps above and try again.');
      result.innerHTML = `<i data-lucide="alert-circle" style="width:16px;height:16px;vertical-align:-3px;margin-right:6px"></i>`;
      result.appendChild(errorMsg);
      createIconsIn(result);
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="shield-check" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>Verify Connection';
      createIconsIn(btn);
    }
  } catch {
    result.className = 'setup-auth-result error';
    result.style.display = 'block';
    result.textContent = 'Could not reach the server. Make sure the assistant is running.';
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="shield-check" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px"></i>Verify Connection';
    createIconsIn(btn);
  }
}

// --- Phase 3: Interview ---
const interviewSteps = [
  {
    key: 'about',
    file: 'me.md',
    title: 'About You',
    desc: 'Help the assistant understand who you are so it can tailor responses to your needs.',
    fields: [
      { id: 'iv_name', label: 'What\'s your name?', type: 'text', placeholder: 'e.g., Ms. Johnson' },
      { id: 'iv_teaches', label: 'What do you teach?', type: 'text', placeholder: 'e.g., 9th grade Physics and Forensic Science' },
      { id: 'iv_techcomfort', label: 'How comfortable are you with technology?', type: 'radio', options: ['Beginner', 'Intermediate', 'Advanced'] },
      { id: 'iv_hopes', label: 'What are you hoping this assistant can help you with?', type: 'textarea', placeholder: 'e.g., Lesson planning, grading rubrics, creating activities...' },
    ],
    format: (d) => `# About Me\n\n## Role\n${d.iv_teaches || 'Teacher'}\n\n## Name\n${d.iv_name || ''}\n\n## Tech Comfort Level\n${d.iv_techcomfort || 'Intermediate'}\n\n## Goals\n${d.iv_hopes || ''}\n\n## Preferences\n<!-- Add personal workflow preferences as you discover them -->\n`
  },
  {
    key: 'workspace',
    file: 'work.md',
    title: 'Your Workspace',
    desc: 'Tell the assistant about your teaching environment and tools.',
    fields: [
      { id: 'iv_devices', label: 'What devices do your students use?', type: 'checkbox', options: ['Chromebooks', 'iPads', 'Laptops', 'Desktops', 'Phones'] },
      { id: 'iv_tools', label: 'What tools do you use for teaching?', type: 'checkbox', options: ['Google Classroom', 'Canvas', 'Schoology', 'Google Slides', 'Other'] },
      { id: 'iv_tools_other', label: 'Other tools (if applicable)', type: 'text', placeholder: 'e.g., Desmos, PhET simulations, Kahoot', conditional: 'iv_tools', conditionValue: 'Other' },
      { id: 'iv_limitations', label: 'Any technical limitations to be aware of?', type: 'textarea', placeholder: 'e.g., School blocks certain websites, students can\'t install apps...' },
    ],
    format: (d) => {
      const devices = (d.iv_devices || []).join(', ') || 'Not specified';
      const tools = (d.iv_tools || []).filter(t => t !== 'Other').join(', ');
      const other = d.iv_tools_other ? `, ${d.iv_tools_other}` : '';
      return `# Work Environment\n\n## Student Devices\n${devices}\n\n## Teaching Tools\n${tools}${other || ''}\n\n## Constraints\n${d.iv_limitations || 'None specified'}\n\n## Deployment\n<!-- Updated as you configure integrations -->\n`;
    }
  },
  {
    key: 'team',
    file: 'team.md',
    title: 'Your Team',
    desc: 'Let the assistant know about the people you work with.',
    fields: [
      { id: 'iv_collab', label: 'Do you collaborate with other teachers?', type: 'radio', options: ['Yes', 'No'] },
      { id: 'iv_collabwho', label: 'Who do you work with? (names and subjects)', type: 'textarea', placeholder: 'e.g., Mr. Smith — Chemistry, Ms. Lee — Biology', conditional: 'iv_collab', conditionValue: 'Yes' },
      { id: 'iv_otherusers', label: 'Who else might use this assistant?', type: 'textarea', placeholder: 'e.g., My co-teacher, student teacher, department head...' },
    ],
    format: (d) => {
      let team = '# Team\n\n';
      if (d.iv_collab === 'Yes' && d.iv_collabwho) {
        team += `## Collaborators\n${d.iv_collabwho}\n\n`;
      } else {
        team += '## Collaborators\nNone currently\n\n';
      }
      team += `## Other Users\n${d.iv_otherusers || 'Just me'}\n\n## Collaboration Norms\n<!-- How does your team communicate? -->\n`;
      return team;
    }
  },
  {
    key: 'priorities',
    file: 'current_priorities.md',
    title: 'Your Priorities',
    desc: 'What\'s on your plate right now? The assistant checks this at the start of each session.',
    fields: [
      { id: 'iv_workon', label: 'What are you working on right now?', type: 'textarea', placeholder: 'e.g., Planning the next unit on forces, grading lab reports...' },
      { id: 'iv_automate', label: 'What takes up the most time that you\'d like to automate?', type: 'textarea', placeholder: 'e.g., Writing rubrics, creating review activities, formatting handouts...' },
    ],
    format: (d) => {
      let md = '# Current Priorities\n\n';
      if (d.iv_workon) {
        const items = d.iv_workon.split(/[,\n]/).map(s => s.trim()).filter(Boolean);
        items.forEach((item, i) => {
          md += `## Priority ${i + 1}: ${item}\n**Status:** In Progress\n\n`;
        });
      } else {
        md += '## Priority 1: [Your Top Priority]\n**Goal:** [What does success look like?]\n**Status:** Not Started\n\n';
      }
      if (d.iv_automate) {
        md += `## Automation Wishlist\n${d.iv_automate}\n`;
      }
      return md;
    }
  },
  {
    key: 'rules',
    file: 'rules.md',
    title: 'Communication Style',
    desc: 'Tell the assistant how you\'d like it to communicate with you.',
    fields: [
      { id: 'iv_tone', label: 'How should the assistant talk to you?', type: 'radio', options: ['Casual', 'Professional', 'Technical'] },
      { id: 'iv_detail', label: 'How detailed should responses be?', type: 'radio', options: ['Brief one-liners', 'Mid-detail', 'Detailed explanations'] },
      { id: 'iv_rules', label: 'Any rules or boundaries?', type: 'textarea', placeholder: 'e.g., Never contact parents directly, always use metric units...' },
    ],
    format: (d) => {
      const tone = d.iv_tone || 'Casual';
      const detailMap = { 'Brief one-liners': 'Concise one-liners', 'Mid-detail': 'Mid-detail', 'Detailed explanations': 'Detailed explanations' };
      const detail = detailMap[d.iv_detail] || 'Mid-detail';
      let md = `# Communication & Operating Rules\n\n## Communication Style\n- **Tone:** ${tone}\n- **Format:** ${detail}\n- **Decision-making:** Present options for me to choose from\n\n## Hard Rules\n- Never modify files outside the user's home directory\n- Once a task has been agreed upon, execute without asking for further permissions\n- Never commit secrets, API keys, or credentials to version control\n`;
      if (d.iv_rules) {
        md += `\n## Custom Rules\n${d.iv_rules.split(/\n/).map(r => r.trim()).filter(Boolean).map(r => `- ${r}`).join('\n')}\n`;
      }
      return md;
    }
  }
];

function renderInterviewPhase(container) {
  const stepIdx = setupState.step - 1;
  const step = interviewSteps[stepIdx];
  if (!step) { renderSetupComplete(container); return; }

  container.innerHTML = `
    <div class="setup-phase">
      <div class="setup-step-counter">Step ${setupState.step} of ${interviewSteps.length}</div>
      <div class="setup-interview-step" id="setupInterviewStep">
        <h3>${step.title}</h3>
        <p class="setup-step-desc">${step.desc}</p>
        ${step.fields.map(f => renderInterviewField(f)).join('')}
      </div>
      <div class="setup-actions">
        <button class="setup-btn setup-btn-ghost" onclick="interviewBack()">
          ${setupState.step === 1 ? 'Back' : 'Previous'}
        </button>
        <button class="setup-btn setup-btn-primary" onclick="interviewNext()">
          ${setupState.step === interviewSteps.length ? 'Finish' : 'Next'}
        </button>
      </div>
    </div>`;

  // Restore saved data for this step
  step.fields.forEach(f => {
    const el = document.getElementById(f.id);
    if (!el) return;
    const saved = setupState.data[f.id];
    if (saved === undefined) return;
    if (f.type === 'text' || f.type === 'textarea') el.value = saved;
  });
  // Restore radio selections
  step.fields.filter(f => f.type === 'radio').forEach(f => {
    const saved = setupState.data[f.id];
    if (saved) {
      const radio = document.querySelector(`input[name="${f.id}"][value="${saved}"]`);
      if (radio) { radio.checked = true; updateConditionalFields(f.id); }
    }
  });
  // Restore checkbox selections
  step.fields.filter(f => f.type === 'checkbox').forEach(f => {
    const saved = setupState.data[f.id];
    if (Array.isArray(saved)) {
      saved.forEach(v => {
        const cb = document.querySelector(`input[name="${f.id}"][value="${v}"]`);
        if (cb) cb.checked = true;
      });
      updateConditionalFields(f.id);
    }
  });

  // Focus first input
  const firstInput = container.querySelector('input, textarea');
  if (firstInput) setTimeout(() => firstInput.focus(), 100);
}

function renderInterviewField(field) {
  const isConditional = !!field.conditional;
  const shouldShow = isConditional ? checkConditionalVisible(field) : true;

  let html = `<div class="setup-field ${isConditional ? 'setup-conditional' : ''}" id="field_${field.id}" ${!shouldShow ? 'style="display:none"' : ''}>`;
  html += `<label for="${field.id}">${field.label}</label>`;

  switch (field.type) {
    case 'text':
      html += `<input type="text" id="${field.id}" placeholder="${field.placeholder || ''}" autocomplete="off">`;
      break;
    case 'textarea':
      html += `<textarea id="${field.id}" placeholder="${field.placeholder || ''}" rows="3"></textarea>`;
      break;
    case 'radio':
      html += `<div class="setup-radio-group">`;
      field.options.forEach(opt => {
        html += `<label class="setup-radio-option">
          <input type="radio" name="${field.id}" value="${opt}" onchange="updateConditionalFields('${field.id}')"> ${opt}
        </label>`;
      });
      html += `</div>`;
      break;
    case 'checkbox':
      html += `<div class="setup-checkbox-group">`;
      field.options.forEach(opt => {
        html += `<label class="setup-checkbox-option">
          <input type="checkbox" name="${field.id}" value="${opt}" onchange="updateConditionalFields('${field.id}')"> ${opt}
        </label>`;
      });
      html += `</div>`;
      break;
  }
  html += `</div>`;
  return html;
}

function checkConditionalVisible(field) {
  if (!field.conditional) return true;
  const saved = setupState.data[field.conditional];
  if (Array.isArray(saved)) return saved.includes(field.conditionValue);
  return saved === field.conditionValue;
}

function updateConditionalFields(changedId) {
  // Save the changed value first
  collectCurrentStepData();
  // Show/hide conditional fields
  const stepIdx = setupState.step - 1;
  const step = interviewSteps[stepIdx];
  if (!step) return;
  step.fields.forEach(f => {
    if (f.conditional === changedId) {
      const fieldEl = document.getElementById('field_' + f.id);
      if (fieldEl) {
        fieldEl.style.display = checkConditionalVisible(f) ? '' : 'none';
      }
    }
  });
}

function collectCurrentStepData() {
  const stepIdx = setupState.step - 1;
  const step = interviewSteps[stepIdx];
  if (!step) return;
  step.fields.forEach(f => {
    switch (f.type) {
      case 'text':
      case 'textarea': {
        const el = document.getElementById(f.id);
        if (el) setupState.data[f.id] = el.value;
        break;
      }
      case 'radio': {
        const checked = document.querySelector(`input[name="${f.id}"]:checked`);
        if (checked) setupState.data[f.id] = checked.value;
        break;
      }
      case 'checkbox': {
        const checked = document.querySelectorAll(`input[name="${f.id}"]:checked`);
        setupState.data[f.id] = Array.from(checked).map(c => c.value);
        break;
      }
    }
  });
}

async function saveInterviewStep() {
  const stepIdx = setupState.step - 1;
  const step = interviewSteps[stepIdx];
  if (!step) return true;
  collectCurrentStepData();
  const content = step.format(setupState.data);
  try {
    const res = await fetch('/api/setup/save-context', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: step.file, content })
    });
    const data = await res.json();
    return data.status === 'ok';
  } catch {
    showToast('Could not save — check your connection', 'error');
    return false;
  }
}

async function interviewNext() {
  const saved = await saveInterviewStep();
  if (!saved) return;
  if (setupState.step >= interviewSteps.length) {
    // Done — show completion
    setupState.step = interviewSteps.length + 1;
    const container = document.getElementById('setupPhaseContent');
    if (container) renderSetupComplete(container);
    return;
  }
  setupState.step++;
  renderSetupPhase();
}

function interviewBack() {
  collectCurrentStepData();
  if (setupState.step <= 1) {
    advanceSetupPhase('auth');
    return;
  }
  setupState.step--;
  renderSetupPhase();
}

function renderSetupComplete(container) {
  container.innerHTML = `
    <div class="setup-complete">
      <div class="setup-complete-icon">
        <i data-lucide="sparkles"></i>
      </div>
      <h3>You're All Set!</h3>
      <p>Your assistant has been personalized and is ready to go.<br>
      You can always update your preferences in the context files later.</p>
      <button class="setup-btn setup-btn-primary" onclick="dismissSetupWizard()" style="margin:0 auto;">
        Start Using Assistant
      </button>
    </div>`;
  createIconsIn(container);
}

function dismissSetupWizard() {
  setupState = { phase: null, step: 1, data: {}, setupData: null };
  safeSet('ea-onboarded', 'true');
  safeSet('ea-setup-complete', 'true');
  // Re-initialize the full app
  chatContainer.innerHTML = '';
  createNewTab();
  loadSessions();
  loadFiles('');
  loadGitStatus();
  document.getElementById('settingApprovalMode').value = settings.approvalMode;
  document.getElementById('settingModel').value = settings.model;
  document.getElementById('settingNotifications').value = settings.notifications;
  document.getElementById('settingOnboarding').value = 'off';
  updateModelBadge();
  updateModeToggle();
  updateBreadcrumbs();
  updateStatusBar();
  pollTokenUsage();
  lucide.createIcons();
  setTimeout(updateMinimap, 500);
  showToast('Setup complete — welcome!', 'success');
}

// ===== BREADCRUMB NAVIGATION =====
function updateBreadcrumbs() {
  const wsEl = document.getElementById('breadcrumbWorkspace');
  const sessionEl = document.getElementById('breadcrumbSession');
  wsEl.textContent = workspaceName || '...';
  const tab = getActiveTab();
  sessionEl.textContent = tab ? tab.title : 'New Chat';
}

// ===== CONVERSATION MINIMAP =====
function updateMinimap() {
  const minimap = document.getElementById('minimap');
  const viewport = document.getElementById('minimapViewport');

  // Collect message elements
  const messages = chatContainer.querySelectorAll('.message, .tool-calls, .tool-call');
  const msgEls = Array.from(messages).filter(el =>
    el.classList.contains('message') || el.classList.contains('tool-call')
  );

  // Only show if 5+ messages
  if (msgEls.length < 5) {
    minimap.classList.remove('visible');
    return;
  }
  minimap.classList.add('visible');

  // Remove old blocks
  minimap.querySelectorAll('.minimap-block').forEach(b => b.remove());

  const containerHeight = chatContainer.scrollHeight;
  const visibleHeight = chatContainer.clientHeight;
  const minimapHeight = minimap.clientHeight;

  if (containerHeight === 0) return;

  const scale = minimapHeight / containerHeight;

  // Add blocks
  for (const el of msgEls) {
    const block = document.createElement('div');
    block.className = 'minimap-block';
    if (el.classList.contains('user')) block.classList.add('user');
    else if (el.classList.contains('assistant')) block.classList.add('assistant');
    else if (el.classList.contains('tool-call')) block.classList.add('tool');
    else if (el.classList.contains('system')) block.classList.add('system');
    else block.classList.add('assistant');

    const top = el.offsetTop * scale;
    const height = Math.max(3, el.offsetHeight * scale);
    block.style.top = top + 'px';
    block.style.height = height + 'px';

    // Click to scroll
    block.addEventListener('click', () => {
      chatContainer.scrollTo({ top: el.offsetTop - 50, behavior: 'smooth' });
    });

    minimap.appendChild(block);
  }

  // Update viewport indicator
  const vpTop = chatContainer.scrollTop * scale;
  const vpHeight = visibleHeight * scale;
  viewport.style.top = vpTop + 'px';
  viewport.style.height = vpHeight + 'px';
}

// Update minimap on scroll
chatContainer.addEventListener('scroll', () => {
  const minimap = document.getElementById('minimap');
  if (!minimap.classList.contains('visible')) return;
  const viewport = document.getElementById('minimapViewport');
  const containerHeight = chatContainer.scrollHeight;
  const visibleHeight = chatContainer.clientHeight;
  const minimapHeight = minimap.clientHeight;
  if (containerHeight === 0) return;
  const scale = minimapHeight / containerHeight;
  viewport.style.top = (chatContainer.scrollTop * scale) + 'px';
  viewport.style.height = (visibleHeight * scale) + 'px';
});

// Periodically update minimap (catches new messages)
setInterval(() => {
  const minimap = document.getElementById('minimap');
  if (minimap && minimap.classList.contains('visible')) updateMinimap();
}, 2000);


// ===== TAB CONTEXT MENU =====
let _activeContextMenu = null;

function closeTabContextMenu() {
  if (_activeContextMenu) {
    _activeContextMenu.remove();
    _activeContextMenu = null;
  }
  document.removeEventListener('click', closeTabContextMenu);
  document.removeEventListener('keydown', _contextMenuKeyHandler);
}

function _contextMenuKeyHandler(e) {
  if (e.key === 'Escape') { closeTabContextMenu(); return; }
  if (!_activeContextMenu) return;
  const items = Array.from(_activeContextMenu.querySelectorAll('.tab-context-menu-item'));
  if (items.length === 0) return;
  const focused = _activeContextMenu.querySelector('.tab-context-menu-item:focus');
  let idx = items.indexOf(focused);
  if (e.key === 'ArrowDown') { e.preventDefault(); idx = (idx + 1) % items.length; items[idx].focus(); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); idx = (idx - 1 + items.length) % items.length; items[idx].focus(); }
  else if (e.key === 'Enter' && focused) { e.preventDefault(); focused.click(); }
}

function showTabContextMenu(tabId, x, y) {
  closeTabContextMenu();
  const tab = tabs.find(t => t.id === tabId);
  if (!tab) return;

  const menu = document.createElement('div');
  menu.className = 'tab-context-menu';
  menu.setAttribute('role', 'menu');

  const items = [
    { label: 'Close', icon: 'x', action: () => closeTab(tabId) },
    { label: 'Close Others', icon: 'x-circle', action: () => { const keep = tabs.filter(t => t.id === tabId || t.pinned); tabs.length = 0; tabs.push(...keep); if (!tabs.find(t => t.id === activeTabId)) switchTab(tabs[0].id); renderTabs(); } },
    { label: 'Close All', icon: 'x-square', action: () => { tabs.length = 0; createNewTab(); } },
    'sep',
    { label: tab.pinned ? 'Unpin Tab' : 'Pin Tab', icon: 'pin', action: () => { tab.pinned = !tab.pinned; renderTabs(); } },
    'sep',
    { label: 'Export Session', icon: 'download', action: () => { switchTab(tabId); exportConversation(); } },
  ];

  for (const item of items) {
    if (item === 'sep') {
      const sep = document.createElement('div');
      sep.className = 'tab-context-menu-sep';
      menu.appendChild(sep);
      continue;
    }
    const el = document.createElement('div');
    el.className = 'tab-context-menu-item';
    el.setAttribute('role', 'menuitem');
    el.setAttribute('tabindex', '-1');
    el.innerHTML = '<i data-lucide="' + item.icon + '"></i><span>' + escapeHtml(item.label) + '</span>';
    el.addEventListener('click', (e) => { e.stopPropagation(); closeTabContextMenu(); item.action(); });
    menu.appendChild(el);
  }

  // Position: ensure it stays on screen
  document.body.appendChild(menu);
  createIconsIn(menu);
  const rect = menu.getBoundingClientRect();
  if (x + rect.width > window.innerWidth) x = window.innerWidth - rect.width - 8;
  if (y + rect.height > window.innerHeight) y = window.innerHeight - rect.height - 8;
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';

  _activeContextMenu = menu;
  // Focus first item
  const firstItem = menu.querySelector('.tab-context-menu-item');
  if (firstItem) firstItem.focus();

  setTimeout(() => {
    document.addEventListener('click', closeTabContextMenu);
    document.addEventListener('keydown', _contextMenuKeyHandler);
  }, 0);
}

// Right-click handler on tab bar
tabBar.addEventListener('contextmenu', e => {
  const tabEl = e.target.closest('.tab');
  if (!tabEl || !tabEl.dataset.tabId) return;
  e.preventDefault();
  showTabContextMenu(tabEl.dataset.tabId, e.clientX, e.clientY);
});

// ===== TAB DRAG-TO-REORDER =====
let _dragTabId = null;

tabBar.addEventListener('dragstart', e => {
  const tabEl = e.target.closest('.tab');
  if (!tabEl || !tabEl.dataset.tabId) return;
  _dragTabId = tabEl.dataset.tabId;
  tabEl.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', tabEl.dataset.tabId);
});

tabBar.addEventListener('dragover', e => {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  const tabEl = e.target.closest('.tab');
  if (!tabEl || tabEl.dataset.tabId === _dragTabId) return;
  // Clear all indicators
  tabBar.querySelectorAll('.tab').forEach(t => t.classList.remove('drag-over-left', 'drag-over-right'));
  // Determine left/right
  const rect = tabEl.getBoundingClientRect();
  const midX = rect.left + rect.width / 2;
  if (e.clientX < midX) tabEl.classList.add('drag-over-left');
  else tabEl.classList.add('drag-over-right');
});

tabBar.addEventListener('dragleave', e => {
  const tabEl = e.target.closest('.tab');
  if (tabEl) tabEl.classList.remove('drag-over-left', 'drag-over-right');
});

tabBar.addEventListener('drop', e => {
  e.preventDefault();
  tabBar.querySelectorAll('.tab').forEach(t => t.classList.remove('drag-over-left', 'drag-over-right', 'dragging'));
  const targetEl = e.target.closest('.tab');
  if (!targetEl || !_dragTabId || targetEl.dataset.tabId === _dragTabId) return;

  const dragTab = tabs.find(t => t.id === _dragTabId);
  const targetTab = tabs.find(t => t.id === targetEl.dataset.tabId);
  if (!dragTab || !targetTab) return;

  // Enforce: pinned tabs stay before unpinned
  if (dragTab.pinned && !targetTab.pinned) return;
  if (!dragTab.pinned && targetTab.pinned) return;

  // Reorder
  const dragIdx = tabs.indexOf(dragTab);
  tabs.splice(dragIdx, 1);
  let targetIdx = tabs.indexOf(targetTab);
  const rect = targetEl.getBoundingClientRect();
  if (e.clientX > rect.left + rect.width / 2) targetIdx++;
  tabs.splice(targetIdx, 0, dragTab);
  renderTabs();
});

tabBar.addEventListener('dragend', () => {
  tabBar.querySelectorAll('.tab').forEach(t => t.classList.remove('dragging', 'drag-over-left', 'drag-over-right'));
  _dragTabId = null;
});

// ===== DIRTY INDICATOR (UNSENT DRAFT) =====
messageInput.addEventListener('input', () => {
  const tab = getActiveTab();
  if (!tab) return;
  const hasText = messageInput.value.trim().length > 0;
  if (tab.hasDraft !== hasText) {
    tab.hasDraft = hasText;
    renderTabs();
  }
});

// Clear draft when input becomes empty (e.g. after send)
setInterval(() => {
  const tab = getActiveTab();
  if (tab && tab.hasDraft && messageInput.value.trim() === '') {
    tab.hasDraft = false;
    renderTabs();
  }
}, 500);

// ===== SIDEBAR RESIZE =====
(function initSidebarResize() {
  const handle = document.getElementById('sidebarResizeHandle');
  const sidebar = document.getElementById('sidebar');
  if (!handle || !sidebar) return;

  const DEFAULT_WIDTH = 280;
  const MIN_WIDTH = 170;
  const getMaxWidth = () => window.innerWidth * 0.5;
  let isResizing = false;

  // Restore saved width
  const savedWidth = parseInt(safeGet('ea-sidebar-width', ''), 10);
  if (savedWidth && savedWidth >= MIN_WIDTH) {
    sidebar.style.width = savedWidth + 'px';
  }

  function startResize(clientX) {
    isResizing = true;
    handle.classList.add('active');
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
    // Disable sidebar transition during drag
    sidebar.style.transition = 'none';
  }

  function doResize(clientX) {
    if (!isResizing) return;
    const maxWidth = getMaxWidth();
    const width = Math.max(MIN_WIDTH, Math.min(clientX, maxWidth));
    sidebar.style.width = width + 'px';
  }

  function stopResize() {
    if (!isResizing) return;
    isResizing = false;
    handle.classList.remove('active');
    document.body.style.userSelect = '';
    document.body.style.cursor = '';
    sidebar.style.transition = '';
    // Save width
    const currentWidth = parseInt(sidebar.style.width, 10);
    if (currentWidth) safeSet('ea-sidebar-width', currentWidth.toString());
  }

  // Mouse events
  handle.addEventListener('mousedown', e => { e.preventDefault(); startResize(e.clientX); });
  document.addEventListener('mousemove', e => { if (isResizing) doResize(e.clientX); });
  document.addEventListener('mouseup', () => stopResize());

  // Touch events
  handle.addEventListener('touchstart', e => { e.preventDefault(); startResize(e.touches[0].clientX); }, { passive: false });
  document.addEventListener('touchmove', e => { if (isResizing) doResize(e.touches[0].clientX); }, { passive: true });
  document.addEventListener('touchend', () => stopResize());

  // Double-click to reset
  handle.addEventListener('dblclick', () => {
    sidebar.style.width = DEFAULT_WIDTH + 'px';
    safeSet('ea-sidebar-width', DEFAULT_WIDTH.toString());
  });

  // Keyboard support: arrow keys to resize
  handle.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const current = parseInt(sidebar.style.width || getComputedStyle(sidebar).width, 10);
      const delta = e.key === 'ArrowRight' ? 10 : -10;
      const maxWidth = getMaxWidth();
      const newWidth = Math.max(MIN_WIDTH, Math.min(current + delta, maxWidth));
      sidebar.style.width = newWidth + 'px';
      safeSet('ea-sidebar-width', newWidth.toString());
    }
  });
})();

// ===== TAB OVERFLOW CHECK ON RESIZE =====
window.addEventListener('resize', () => { checkTabOverflow(); });

// ===== DEBUG / VERBOSE MODE =====
let debugStartTime = null;
let debugFirstTokenTime = null;

function toggleVerboseMode(value) {
  settings.verbose = value === 'on';
  safeSet('ea-verbose', value);
  const panel = document.getElementById('debugPanel');
  if (settings.verbose) {
    panel.style.display = 'flex';
    createIconsIn(panel);
  } else {
    panel.style.display = 'none';
  }
}

function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function debugLog(event) {
  if (!settings.verbose) return;

  const log = document.getElementById('debugLog');
  const now = new Date();
  const timeStr = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const type = event.type || 'unknown';
  const entry = document.createElement('div');
  entry.className = 'debug-entry';

  let detail = '';
  switch (type) {
    case 'init':
      debugStartTime = performance.now();
      debugFirstTokenTime = null;
      detail = `session=${escapeHtml(event.session_id || 'new')} <span class="debug-model-badge">${escapeHtml(event.model || 'unknown')}</span>`;
      break;
    case 'message':
      if (!debugFirstTokenTime && debugStartTime) {
        debugFirstTokenTime = performance.now();
        const ttft = ((debugFirstTokenTime - debugStartTime) / 1000).toFixed(2);
        detail = `role=${escapeHtml(event.role || '?')} TTFT=${ttft}s`;
      } else {
        const delta = event.delta ? event.content?.substring(0, 80) : (event.content ? event.content.substring(0, 80) : '');
        detail = `role=${escapeHtml(event.role || '?')} ${delta ? '"' + escapeHtml(delta) + '..."' : ''}`;
      }
      break;
    case 'tool_use':
      detail = `tool=${escapeHtml(event.tool_name || '?')} id=${escapeHtml(event.tool_id || '?')}`;
      break;
    case 'tool_result': {
      const status = escapeHtml(event.status || '?');
      const outputLen = event.output ? event.output.length : 0;
      detail = `id=${escapeHtml(event.tool_id || '?')} status=${status} output=${outputLen} chars`;
      break;
    }
    case 'result':
      if (debugStartTime) {
        const totalTime = ((performance.now() - debugStartTime) / 1000).toFixed(2);
        const stats = event.stats || {};
        detail = `total=${totalTime}s tokens: &uarr;${stats.input_tokens || 0} &darr;${stats.output_tokens || 0}`;
        if (stats.model) detail += ` <span class="debug-model-badge">${escapeHtml(stats.model)}</span>`;
      }
      break;
    case 'error':
      detail = escapeHtml(event.message || 'Unknown error');
      break;
    default:
      detail = escapeHtml(JSON.stringify(event).substring(0, 120));
  }

  entry.innerHTML = `
    <span class="debug-time">${timeStr}</span>
    <span class="debug-type debug-type-${escapeHtml(type)}">${escapeHtml(type)}</span>
    <span class="debug-detail">${detail}</span>
  `;

  log.appendChild(entry);

  if (document.getElementById('debugAutoScroll').checked) {
    log.scrollTop = log.scrollHeight;
  }
}

function clearDebugLog() {
  document.getElementById('debugLog').innerHTML = '';
  debugStartTime = null;
  debugFirstTokenTime = null;
}

// Debug panel resize
(function() {
  const handle = document.getElementById('debugResizeHandle');
  const panel = document.getElementById('debugPanel');
  if (!handle || !panel) return;

  let startY, startHeight;

  handle.addEventListener('mousedown', function(e) {
    startY = e.clientY;
    startHeight = panel.offsetHeight;

    function onMouseMove(e) {
      const delta = startY - e.clientY;
      const newHeight = Math.max(80, Math.min(window.innerHeight * 0.6, startHeight + delta));
      panel.style.height = newHeight + 'px';
    }

    function onMouseUp() {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    e.preventDefault();
  });
})();

// ===== CONFIRM MODAL =====
let _confirmCallback = null;

function showConfirmModal(title, message, onConfirm, options = {}) {
  const modal = document.getElementById('confirmModal');
  document.getElementById('confirmModalTitle').textContent = title;
  document.getElementById('confirmModalMessage').textContent = message;

  const confirmBtn = document.getElementById('confirmModalConfirm');
  confirmBtn.textContent = options.confirmText || 'Confirm';
  confirmBtn.className = 'confirm-modal-btn confirm' + (options.danger ? ' danger' : '');

  _confirmCallback = onConfirm;
  confirmBtn.onclick = function() {
    const cb = _confirmCallback;
    closeConfirmModal();
    if (cb) cb();
  };

  modal.classList.add('open');

  // Focus Cancel for safety (prevents accidental Enter confirmation)
  document.getElementById('confirmModalCancel').focus();

  // Close on Escape
  modal._escHandler = function(e) {
    if (e.key === 'Escape') closeConfirmModal();
  };
  document.addEventListener('keydown', modal._escHandler);
}

function closeConfirmModal() {
  const modal = document.getElementById('confirmModal');
  modal.classList.remove('open');
  _confirmCallback = null;
  if (modal._escHandler) {
    document.removeEventListener('keydown', modal._escHandler);
    modal._escHandler = null;
  }
}

// ===== SHUTDOWN =====
function confirmShutdown() {
  showConfirmModal(
    'Stop Server',
    'This will shut down the assistant server. You\'ll need to run start.sh or start.bat again to restart.',
    function() {
      fetch('/api/shutdown', { method: 'POST' })
        .then(res => res.json())
        .then(() => {
          // Show shutdown overlay
          const overlay = document.createElement('div');
          overlay.className = 'shutdown-overlay';
          overlay.innerHTML = `
            <i data-lucide="power-off" style="width:48px;height:48px;color:var(--text-muted)"></i>
            <h2>Server Stopped</h2>
            <p>The assistant has been shut down. You can close this browser tab.</p>
            <p style="color:var(--text-muted);font-size:0.85rem;">To restart, run <code style="background:var(--bg-input);padding:2px 6px;border-radius:4px;">start.sh</code> or <code style="background:var(--bg-input);padding:2px 6px;border-radius:4px;">start.bat</code></p>
          `;
          document.body.appendChild(overlay);
          lucide.createIcons();
        })
        .catch(() => {
          showToast('Failed to stop server', 'error');
        });
    },
    { danger: true, confirmText: 'Shut Down' }
  );
}

// ===== LAUNCH =====
init();

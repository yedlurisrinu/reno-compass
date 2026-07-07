/**
 * Reno Compass Frontend Application Script
 * Orchestrates session cycles, client chat, and PDF restore gates.
 */

let activeToken = null;
let currentStage = 'scope';

// Elements
const chatHistory = document.getElementById('chatHistory');
const chatInput = document.getElementById('chatInput');
const btnSend = document.getElementById('btnSend');
const btnRestorePdf = document.getElementById('btnRestorePdf');
const fileUpload = document.getElementById('fileUpload');
const btnDownload = document.getElementById('btnDownload');
const chatInputBar = document.getElementById('chatInputBar');
const sessionCompleteBar = document.getElementById('sessionCompleteBar');
const btnDownloadAgain = document.getElementById('btnDownloadAgain');
const btnNewProject = document.getElementById('btnNewProject');

// The chat input's default placeholder, captured so a stage-specific hint (e.g. the
// DIY "just type your question" invitation) can be applied and then reset.
const DEFAULT_INPUT_PLACEHOLDER = chatInput ? chatInput.placeholder : '';

function applyInputHint(hint) {
    if (!chatInput) return;
    chatInput.placeholder = hint || DEFAULT_INPUT_PLACEHOLDER;
}

// 1. Initial Session Load / Resume
window.addEventListener('DOMContentLoaded', async () => {
    const savedToken = localStorage.getItem("reno_active_token");
    if (savedToken && savedToken !== "undefined" && savedToken !== "null") {
        try {
            const res = await fetch('/api/session/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_token: savedToken })
            });
            const data = await res.json();
            if (res.ok && data.session_token) {
                activeToken = data.session_token;
                renderConversationHistory(data);
                updateUIState(data);
                appendSystemMessage("Resumed existing session.");
                return;
            }
        } catch (err) {
            console.error("Failed to load saved session:", err);
        }
    }
    
    // Clear any invalid tokens
    localStorage.removeItem("reno_active_token");
    
    // Fallback if no saved session or load failed
    await startNewSession();
});

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// --- "Thinking…" progress indicator (shown while awaiting an agent reply) ---
const THINKING_PHRASES = [
    "Thinking it through…",
    "Measuring the space…",
    "Cross-checking building codes…",
    "Consulting the safety constitution…",
    "Calibrating the budget…",
    "Reviewing your design…",
    "Tallying materials…",
    "Auditing the details…",
];
let thinkingTimer = null;

function showThinking() {
    hideThinking();
    if (btnSend) btnSend.disabled = true;
    const wrap = document.createElement('div');
    wrap.className = 'chat-message agent-message thinking-message';
    wrap.id = 'thinkingBubble';
    wrap.innerHTML =
        '<span class="thinking-dots"><span></span><span></span><span></span></span>' +
        '<span class="thinking-label"></span>';
    chatHistory.appendChild(wrap);
    const label = wrap.querySelector('.thinking-label');
    let i = 0;
    const tick = () => { label.textContent = THINKING_PHRASES[i % THINKING_PHRASES.length]; i++; };
    tick();
    thinkingTimer = setInterval(tick, 2200);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function hideThinking() {
    if (thinkingTimer) { clearInterval(thinkingTimer); thinkingTimer = null; }
    const b = document.getElementById('thinkingBubble');
    if (b) b.remove();
    if (btnSend) btnSend.disabled = false;
}

// --- One-tap quick-reply chips (inline confirmation) ------------------------
function clearQuickReplies() {
    const existing = document.getElementById('quickReplies');
    if (existing) existing.remove();
}

function renderQuickReplies(replies) {
    clearQuickReplies();
    if (!Array.isArray(replies) || replies.length === 0) return;
    const row = document.createElement('div');
    row.className = 'quick-replies';
    row.id = 'quickReplies';
    replies.forEach(text => {
        const chip = document.createElement('button');
        chip.className = 'quick-reply-chip';
        chip.textContent = text;
        chip.addEventListener('click', () => {
            clearQuickReplies();
            sendMessage(text);
        });
        row.appendChild(chip);
    });
    chatHistory.appendChild(row);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function startNewSession() {
    try {
        const res = await fetch('/api/session/new', { method: 'POST' });
        const data = await res.json();
        if (!res.ok || !data.session_token) {
            console.error("Session initialization failed:", data);
            appendSystemWarning(`Session initialization failed: ${data.detail || 'Server error'}`);
            return;
        }
        activeToken = data.session_token;
        localStorage.setItem("reno_active_token", activeToken);
        chatHistory.innerHTML = ''; // Ensure chat pane starts completely clean
        updateUIState(data);
        appendSystemMessage("Fresh session initialized.");
        
        // Dynamic elicitation: Fetch initial questions from the ScopeAgent
        await fetchInitialQuestions();
    } catch (err) {
        console.error("Failed to boot session:", err);
        appendSystemWarning("Network error: Failed to connect to session service.");
    }
}

async function fetchInitialQuestions() {
    showThinking();
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_token: activeToken,
                message: "Let's get started. Please introduce yourself and ask me the first set of questions to begin planning my bathroom remodel."
            })
        });
        const data = await res.json();
        if (res.ok) {
            appendAgentMessage(data.response);
            updateUIState(data);
        } else {
            appendSystemWarning(`Failed to retrieve initial questions: ${data.detail || 'Error'}`);
        }
    } catch (err) {
        console.error("Failed to fetch initial questions:", err);
        appendSystemWarning("Network error encountered while loading initial questions.");
    } finally {
        hideThinking();
    }
}

function renderConversationHistory(state) {
    chatHistory.innerHTML = '';
    if (state.conversation) {
        state.conversation.forEach(turn => {
            // Hide the system's hidden starter prompt from the chat viewport
            if (turn.role === 'user' && turn.text.includes("Let's get started. Please introduce yourself")) {
                return;
            }
            if (turn.role === 'user') {
                appendUserMessage(turn.text);
            } else {
                appendAgentMessage(turn.text);
            }
        });
    }
}

// 2. Render Dossier State and Pipeline Step Indicators
function updateUIState(state) {
    if (!state) return;
    
    const oldStage = currentStage;
    currentStage = state.current_stage;
    
    // Refresh stage highlight classes
    const stages = [
        "scope", "design", "safety_permit", "logistics_feasibility",
        "materials", "contractor_validation", "diy_planning", "synthesis"
    ];
    
    let activeFound = false;
    stages.forEach(st => {
        const stepEl = document.getElementById(`step-${st}`);
        if (!stepEl) return;
        
        stepEl.classList.remove('active', 'completed');
        
        if (st === currentStage) {
            stepEl.classList.add('active');
            activeFound = true;
        } else if (!activeFound) {
            stepEl.classList.add('completed');
        }
    });

    // Keep the active step visible when the pipeline scrolls horizontally
    // (narrow screens). block:'nearest' avoids scrolling the page vertically.
    const activeEl = document.getElementById(`step-${currentStage}`);
    if (activeEl && typeof activeEl.scrollIntoView === 'function') {
        activeEl.scrollIntoView({ block: 'nearest', inline: 'center' });
    }

    if (oldStage !== currentStage && oldStage !== 'complete' && currentStage !== 'scope') {
        appendSystemMessage(`Stage successfully advanced to ${capitalize(currentStage.replace('_', ' '))}!`);
        // If advanced, rerender conversation history of the new stage
        renderConversationHistory(state);
    }

    // Enable download trigger at synthesis/complete stages
    if (currentStage === 'synthesis' || currentStage === 'complete') {
        btnDownload.style.display = 'inline-block';
    } else {
        btnDownload.style.display = 'none';
    }
}

// 3. Post Message
btnSend.addEventListener('click', () => sendMessage());
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// `overrideText` is supplied when a quick-reply chip is clicked; otherwise the
// message is read from the input box.
async function sendMessage(overrideText) {
    const fromChip = typeof overrideText === 'string';
    const text = (fromChip ? overrideText : chatInput.value).trim();
    if (!text) return;

    clearQuickReplies();
    appendUserMessage(text);
    if (!fromChip) chatInput.value = '';

    // Show the "thinking…" indicator while the agent works.
    showThinking();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_token: activeToken, message: text })
        });

        if (res.status === 429) {
            appendSystemWarning("Rate limit exceeded! Please wait 1 minute before sending another message.");
            return;
        }

        const data = await res.json();
        if (res.ok) {
            appendAgentMessage(data.response);
            updateUIState(data);
            renderQuickReplies(data.quick_replies);
            applyInputHint(data.input_hint);
        } else {
            appendSystemWarning(`Error: ${data.detail || 'Failed to process message'}`);
        }
    } catch (err) {
        console.error("Chat communication failure:", err);
        appendSystemWarning("Network error encountered.");
    } finally {
        hideThinking();
    }
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Helper to push text nodes
function appendUserMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message user-message';
    wrapper.textContent = text;
    chatHistory.appendChild(wrapper);
}

function appendAgentMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message agent-message';
    wrapper.textContent = text;
    chatHistory.appendChild(wrapper);
}

function appendSystemMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message agent-message';
    wrapper.style.borderColor = 'var(--accent-color)';
    wrapper.innerHTML = `<strong>System:</strong> ${text}`;
    chatHistory.appendChild(wrapper);
}

function appendSystemWarning(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message agent-message';
    wrapper.style.borderColor = 'var(--danger-color)';
    wrapper.style.color = 'var(--danger-color)';
    wrapper.innerHTML = `<strong>Warning:</strong> ${text}`;
    chatHistory.appendChild(wrapper);
}

// 4. Restore Session from PDF
btnRestorePdf.addEventListener('click', () => {
    fileUpload.click();
});

fileUpload.addEventListener('change', async () => {
    if (!fileUpload.files || fileUpload.files.length === 0) return;
    
    const file = fileUpload.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    appendSystemMessage(`Restoring session from blueprint PDF: ${file.name}...`);
    
    try {
        const res = await fetch('/api/session/restore-pdf', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (res.ok) {
            activeToken = data.session_token;
            localStorage.setItem("reno_active_token", activeToken);
            renderConversationHistory(data);
            updateUIState(data);
            appendSystemMessage(`Session successfully restored. Active token updated: ${activeToken}`);
            appendSystemWarning(data.warning || "Dossier reloaded.");
        } else {
            appendSystemWarning(`Restore failure: ${data.detail}`);
        }
    } catch (err) {
        console.error("File upload restore failed:", err);
        appendSystemWarning("Failed to restore session from document.");
    }
});


// 5. Download artifacts helper
// The last successfully generated artifacts, kept in memory so "Download Again" on
// the end-screen still works after the server session has been deleted at finalize.
let cachedArtifacts = null;
// Set once the completed session's server checkpoint has been deleted.
let sessionFinalized = false;

function triggerArtifactDownloads(data) {
    downloadBase64(data.pdf_base64, data.pdf_filename, 'application/pdf');
    downloadBase64(data.xlsx_base64, data.xlsx_filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
}

async function downloadArtifacts() {
    // After finalize the server checkpoint is gone — re-download from the copy we
    // captured at completion instead of hitting the (now deleted) session.
    if (sessionFinalized && cachedArtifacts) {
        triggerArtifactDownloads(cachedArtifacts);
        appendSystemMessage("Re-downloaded your saved blueprints. Check your browser downloads.");
        return true;
    }

    appendSystemMessage("Generating project artifacts. Please wait...");
    try {
        const res = await fetch('/api/session/download-artifacts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_token: activeToken })
        });
        const data = await res.json();
        if (res.ok) {
            cachedArtifacts = data;
            triggerArtifactDownloads(data);
            appendSystemMessage("Artifacts compiled successfully! Check your browser downloads.");
            // Once the plan is complete AND downloaded, close out the session: delete
            // the server-side checkpoint from storage, drop the persisted token so a
            // reload starts fresh, and show the terminal end-screen. "Restore PDF"
            // still works — it rebuilds state from the uploaded blueprint, not the
            // deleted checkpoint; "Download Again" uses the cached copy above.
            if (currentStage === 'complete') {
                await finalizeServerSession();
                finalizeSession();
            }
            return true;
        }
        appendSystemWarning(`Failed to compile blueprints: ${data.detail}`);
    } catch (err) {
        console.error("Failed to download artifacts:", err);
        appendSystemWarning("Network error while compiling blueprints.");
    }
    return false;
}

// Ask the server to remove the completed session's checkpoint from storage.
async function finalizeServerSession() {
    try {
        await fetch('/api/session/finalize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_token: activeToken })
        });
    } catch (err) {
        // Non-fatal: TTL cleanup will eventually reclaim the checkpoint.
        console.error("Failed to finalize/delete server session:", err);
    }
    sessionFinalized = true;
}

btnDownload.addEventListener('click', downloadArtifacts);
btnDownloadAgain.addEventListener('click', downloadArtifacts);

// Terminal end-screen: plan complete + artifacts downloaded.
function finalizeSession() {
    // The server checkpoint has already been deleted (finalizeServerSession). Drop the
    // CLIENT-side persisted token too so a reload does not try to resume a finished,
    // now-deleted session; "Download Again" serves from the cached artifacts instead.
    clearQuickReplies();
    localStorage.removeItem("reno_active_token");
    if (chatInputBar) chatInputBar.style.display = 'none';
    if (sessionCompleteBar) sessionCompleteBar.style.display = 'flex';
    btnDownload.style.display = 'none';
}

// Start a brand-new project from the end-screen.
btnNewProject.addEventListener('click', async () => {
    if (sessionCompleteBar) sessionCompleteBar.style.display = 'none';
    if (chatInputBar) chatInputBar.style.display = 'flex';
    await startNewSession();
});

function downloadBase64(base64Data, filename, contentType) {
    const raw = window.atob(base64Data);
    const rawLength = raw.length;
    const array = new Uint8Array(new ArrayBuffer(rawLength));
    
    for (let i = 0; i < rawLength; i++) {
        array[i] = raw.charCodeAt(i);
    }
    
    const blob = new Blob([array], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

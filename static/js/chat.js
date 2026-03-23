/* global sb, syncSession, escapeHtml */

const matchId = window.__MATCH_ID__;
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');

let myProfileId = null;

// ── Auth guard & init ────────────────────────────────────────

(async () => {
  const { data: { session } } = await sb.auth.getSession();
  if (!session) {
    window.location.href = '/';
    return;
  }
  await syncSession(session);
  await loadHistory();
  subscribeRealtime();
})();

// ── Load chat history ────────────────────────────────────────

async function loadHistory() {
  try {
    const res = await fetch(`/api/messages/${matchId}`, { credentials: 'same-origin' });
    const data = await res.json();

    if (!data.ok) {
      chatMessages.innerHTML = `<p class="chat-error">${data.message || 'Could not load messages.'}</p>`;
      return;
    }

    myProfileId = data.my_profile_id;
    chatMessages.innerHTML = '';

    if (data.messages.length === 0) {
      chatMessages.innerHTML = '<p class="chat-empty">No messages yet. Say hello!</p>';
    } else {
      for (const msg of data.messages) {
        appendMessage(msg);
      }
    }

    scrollToBottom();
  } catch {
    chatMessages.innerHTML = '<p class="chat-error">Failed to load messages.</p>';
  }
}

// ── Render a single message ──────────────────────────────────

function appendMessage(msg) {
  // Remove empty/error placeholders
  const placeholder = chatMessages.querySelector('.chat-empty, .chat-loading');
  if (placeholder) placeholder.remove();

  const isMine = msg.sender_id === myProfileId;
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${isMine ? 'chat-bubble--mine' : 'chat-bubble--theirs'}`;
  bubble.dataset.id = msg.id;

  const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  bubble.innerHTML = `
    <p class="chat-text">${escapeHtml(msg.content)}</p>
    <span class="chat-time">${time}</span>
  `;

  chatMessages.appendChild(bubble);
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── Send message ─────────────────────────────────────────────

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const content = chatInput.value.trim();
  if (!content) return;

  const sendBtn = chatForm.querySelector('.chat-send-btn');
  sendBtn.disabled = true;
  chatInput.value = '';

  try {
    const res = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ match_id: matchId, content }),
    });
    if (!res.ok) {
      chatInput.value = content;
    }
  } catch {
    chatInput.value = content;
  }

  sendBtn.disabled = false;
  chatInput.focus();
});

// ── Supabase Realtime subscription ───────────────────────────

function subscribeRealtime() {
  sb.channel(`match-${matchId}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'messages',
        filter: `match_id=eq.${matchId}`,
      },
      (payload) => {
        const msg = payload.new;
        // Avoid duplicates
        if (chatMessages.querySelector(`[data-id="${msg.id}"]`)) return;
        appendMessage(msg);
        scrollToBottom();
      },
    )
    .subscribe();
}

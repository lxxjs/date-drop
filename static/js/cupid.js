/* global sb, syncSession, escapeHtml */

const cupidForm = document.getElementById('cupidForm');
const shipBtn = document.getElementById('shipBtn');
const shipStatus = document.getElementById('shipStatus');
const firstEmailInput = document.getElementById('firstEmail');
const secondEmailInput = document.getElementById('secondEmail');

let shipsLeft = 4;

// ── Auth guard ───────────────────────────────────────────────

document.getElementById('signOutBtn').addEventListener('click', async () => {
  await sb.auth.signOut();
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
  window.location.href = '/';
});

(async () => {
  const { data: { session } } = await sb.auth.getSession();
  if (!session) {
    window.location.href = '/';
    return;
  }
  await syncSession(session);
  loadLeaderboard();
})();

// ── Helpers ──────────────────────────────────────────────────

function normalizeEmail(value) {
  return String(value || '').trim().toLowerCase();
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizeEmail(value));
}

function getCurrentMatchRound() {
  const now = new Date();
  const oneJan = new Date(now.getFullYear(), 0, 1);
  const week = Math.ceil(((now - oneJan) / 86400000 + oneJan.getDay() + 1) / 7);
  return `${now.getFullYear()}-W${String(week).padStart(2, '0')}`;
}

function refreshShipButton() {
  shipBtn.textContent = shipsLeft > 0 ? `Ship It! (${shipsLeft} left)` : 'No ships left';
  shipBtn.disabled = shipsLeft <= 0;
}

function setStatus(message, isError = false) {
  shipStatus.textContent = message;
  shipStatus.style.color = isError ? '#ffd9d9' : '#fff2d8';
}

// ── Submit nomination ────────────────────────────────────────

cupidForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  if (shipsLeft <= 0) {
    setStatus('No ships left this round.', true);
    return;
  }

  const firstEmail = normalizeEmail(firstEmailInput.value);
  const secondEmail = normalizeEmail(secondEmailInput.value);

  if (!isValidEmail(firstEmail) || !isValidEmail(secondEmail)) {
    setStatus('Please enter two valid email addresses.', true);
    return;
  }

  if (firstEmail === secondEmail) {
    setStatus('Please enter two different people.', true);
    return;
  }

  shipBtn.disabled = true;
  setStatus('Submitting...');

  try {
    const res = await fetch('/api/cupid/nominate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        nominee_a_email: firstEmail,
        nominee_b_email: secondEmail,
        match_round: getCurrentMatchRound(),
      }),
    });

    const data = await res.json();

    if (!data.ok) {
      setStatus(data.message || 'Could not submit nomination.', true);
      shipBtn.disabled = false;
      return;
    }

    shipsLeft = data.remaining;
    refreshShipButton();
    setStatus(`Shipped ${firstEmail} + ${secondEmail}. Good luck!`);
    cupidForm.reset();
  } catch {
    setStatus('Network error. Please try again.', true);
    shipBtn.disabled = false;
  }
});

// ── Leaderboard ──────────────────────────────────────────────

async function loadLeaderboard() {
  try {
    const res = await fetch('/api/cupid/leaderboard');
    const data = await res.json();

    if (!data.ok || !data.leaderboard || data.leaderboard.length === 0) return;

    const tbody = document.querySelector('.leaderboard tbody');
    tbody.innerHTML = '';

    data.leaderboard.forEach((entry, i) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${i + 1}</td>
        <td>${escapeHtml(entry.initials)}</td>
        <td>${entry.points}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch {
    // Keep static leaderboard if API fails
  }
}

refreshShipButton();

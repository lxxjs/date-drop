/* global sb, syncSession, escapeHtml */

const matchesContainer = document.querySelector('.home-shell');

// ── Sign out ─────────────────────────────────────────────────

document.getElementById('signOutBtn').addEventListener('click', async () => {
  await sb.auth.signOut();
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
  window.location.href = '/';
});

// ── Auth guard ───────────────────────────────────────────────

(async () => {
  const { data: { session } } = await sb.auth.getSession();
  if (!session) {
    window.location.href = '/';
    return;
  }
  await syncSession(session);

  // Redeem invite if pending (user just completed questionnaire)
  await redeemPendingInvite();

  // Check opt-in status before loading matches
  let isOptedIn = false;
  try {
    const statusRes = await fetch('/api/profile-status', { credentials: 'same-origin' });
    const statusData = await statusRes.json();
    if (statusData.ok) isOptedIn = statusData.is_opted_in;
  } catch { /* ignore */ }

  loadMatches(isOptedIn);
  loadInvites();
})();

// ── Invite redemption (from sessionStorage) ──────────────────

async function redeemPendingInvite() {
  const code = sessionStorage.getItem('invite_code');
  if (!code) return;

  try {
    const res = await fetch('/api/invite/redeem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ invite_code: code }),
    });
    const data = await res.json();
    sessionStorage.removeItem('invite_code');

    if (data.ok && data.inviter_name) {
      const banner = document.getElementById('inviterBanner');
      document.getElementById('inviterName').textContent = data.inviter_name;
      banner.hidden = false;
    }
  } catch {
    // Fire-and-forget
  }
}

// ── Invite link management ───────────────────────────────────

async function loadInvites() {
  try {
    const res = await fetch('/api/invite/mine', { credentials: 'same-origin' });
    const data = await res.json();
    if (!data.ok) return;

    document.getElementById('invitesRemaining').textContent = data.remaining;
    renderInviteList(data.invites);

    if (data.remaining <= 0) {
      document.getElementById('createInviteBtn').disabled = true;
      document.getElementById('createInviteBtn').textContent = 'No invites remaining';
    }
  } catch {
    // silent
  }
}

function renderInviteList(invites) {
  const list = document.getElementById('inviteList');
  list.innerHTML = '';

  for (const inv of invites) {
    const item = document.createElement('div');
    item.className = 'invite-item';

    const link = `${window.location.origin}/invite/${inv.invite_code}`;
    const statusClass = `invite-item__status--${inv.status}`;

    item.innerHTML = `
      <span class="invite-item__link">${escapeHtml(link)}</span>
      <span class="invite-item__status ${statusClass}">${escapeHtml(inv.status)}</span>
      ${inv.status === 'active' ? `<button class="invite-item__copy" data-link="${escapeHtml(link)}">Copy</button>` : ''}
    `;
    list.appendChild(item);
  }

  // Copy button handler
  list.addEventListener('click', (e) => {
    const btn = e.target.closest('.invite-item__copy');
    if (!btn) return;
    navigator.clipboard.writeText(btn.dataset.link).then(() => {
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    });
  });
}

document.getElementById('createInviteBtn').addEventListener('click', async () => {
  const btn = document.getElementById('createInviteBtn');
  btn.disabled = true;
  btn.textContent = 'Creating...';

  try {
    const res = await fetch('/api/invite/create', {
      method: 'POST',
      credentials: 'same-origin',
    });
    const data = await res.json();

    if (!data.ok) {
      btn.textContent = data.message || 'Error';
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = 'Create invite link';
      }, 2000);
      return;
    }

    // Reload invite list
    await loadInvites();
    btn.disabled = false;
    btn.textContent = 'Create invite link';
  } catch {
    btn.textContent = 'Network error';
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = 'Create invite link';
    }, 2000);
  }
});

// ── Load & render matches ────────────────────────────────────

async function loadMatches(isOptedIn) {
  try {
    const res = await fetch('/api/matches', { credentials: 'same-origin' });
    const data = await res.json();

    if (!data.ok || !data.matches || data.matches.length === 0) {
      showEmptyState(isOptedIn);
      return;
    }

    renderMatches(data.matches, isOptedIn);
  } catch {
    showEmptyState(isOptedIn);
  }
}

function showEmptyState(isOptedIn) {
  const hero = matchesContainer.querySelector('.matches-hero');
  const existing = matchesContainer.querySelector('.empty-state-card');
  if (existing) return; // already showing

  const btnText = isOptedIn ? "You're in! We'll match you soon." : 'Opt in for this week';

  const section = document.createElement('section');
  section.className = 'empty-state-card';
  section.innerHTML = `
    <div class="polaroid"><div class="polaroid-photo"></div></div>
    <h2>No matches yet</h2>
    <p>Your match history will show up here</p>
    <button class="btn-primary" id="optInBtn" style="margin-top:1rem"${isOptedIn ? ' disabled' : ''}>${btnText}</button>
  `;
  hero.insertAdjacentElement('afterend', section);

  if (!isOptedIn) {
    document.getElementById('optInBtn').addEventListener('click', async () => {
      const btn = document.getElementById('optInBtn');
      btn.disabled = true;
      btn.textContent = 'Opting in...';
      try {
        const res = await fetch('/api/profile/opt-in', {
          method: 'POST',
          credentials: 'same-origin',
        });
        const result = await res.json();
        btn.textContent = result.ok ? "You're in! We'll match you soon." : (result.message || 'Error');
      } catch {
        btn.textContent = 'Network error';
      }
    });
  }
}

function renderMatches(matches, isOptedIn) {
  // Remove empty state if present
  const empty = matchesContainer.querySelector('.empty-state-card');
  if (empty) empty.remove();

  const hero = matchesContainer.querySelector('.matches-hero');

  // Add opt-in button to hero
  if (!hero.querySelector('#optInBtn')) {
    const optBtn = document.createElement('button');
    optBtn.className = 'btn-primary';
    optBtn.id = 'optInBtn';
    optBtn.style.marginTop = '1rem';

    if (isOptedIn) {
      optBtn.textContent = "You're in for this week!";
      optBtn.disabled = true;
    } else {
      optBtn.textContent = 'Opt in for next week';
      optBtn.addEventListener('click', async () => {
        optBtn.disabled = true;
        optBtn.textContent = 'Opting in...';
        try {
          const res = await fetch('/api/profile/opt-in', { method: 'POST', credentials: 'same-origin' });
          const result = await res.json();
          optBtn.textContent = result.ok ? "You're in!" : (result.message || 'Error');
        } catch {
          optBtn.textContent = 'Network error';
        }
      });
    }

    hero.appendChild(optBtn);
  }

  const grid = document.createElement('section');
  grid.className = 'matches-grid';

  for (const match of matches) {
    const card = document.createElement('div');
    card.className = 'match-card';

    const score = Math.round(match.compatibility_score);
    const reasons = (match.match_reasons || [])
      .map((r) => `<li>${escapeHtml(r)}</li>`)
      .join('');
    const photoSrc = match.partner.photo_url || '';
    const name = escapeHtml(match.partner.name);
    const major = escapeHtml(match.partner.major);
    const photoHtml = photoSrc
      ? `<img class="match-photo" src="${escapeHtml(photoSrc)}" alt="${name}" />`
      : `<div class="match-photo match-photo--placeholder"></div>`;

    card.innerHTML = `
      ${photoHtml}
      <div class="match-info">
        <h3>${name}</h3>
        <p class="match-major">${major}</p>
        <p class="match-score">${score}% compatibility</p>
        ${reasons ? `<ul class="match-reasons">${reasons}</ul>` : ''}
        ${match.partner.date_ideas ? `<p class="match-date-ideas">${escapeHtml(match.partner.date_ideas)}</p>` : ''}
        <div class="match-actions">
          ${match.status === 'pending' ? `
            <button class="btn-primary btn-sm match-accept" data-id="${escapeHtml(match.id)}">Accept</button>
            <button class="btn-ghost btn-sm match-decline" data-id="${escapeHtml(match.id)}">Decline</button>
          ` : match.status === 'accepted' ? `
            <a href="/chat/${encodeURIComponent(match.id)}" class="btn-primary btn-sm">Chat</a>
          ` : `
            <span class="match-status">${escapeHtml(match.status)}</span>
          `}
        </div>
      </div>
    `;

    grid.appendChild(card);
  }

  hero.insertAdjacentElement('afterend', grid);

  // Handle accept/decline buttons
  grid.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-id]');
    if (!btn) return;

    const matchId = btn.dataset.id;
    const action = btn.classList.contains('match-accept') ? 'accepted' : 'declined';

    btn.disabled = true;
    try {
      await fetch(`/api/matches/${matchId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ action }),
      });
      // Reload to reflect new state
      window.location.reload();
    } catch {
      btn.disabled = false;
    }
  });
}

/* global sb, syncSession */

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
  loadMatches();
})();

// ── Load & render matches ────────────────────────────────────

async function loadMatches() {
  try {
    const res = await fetch('/api/matches', { credentials: 'same-origin' });
    const data = await res.json();

    if (!data.ok || !data.matches || data.matches.length === 0) {
      showEmptyState();
      return;
    }

    renderMatches(data.matches);
  } catch {
    showEmptyState();
  }
}

function showEmptyState() {
  const hero = matchesContainer.querySelector('.matches-hero');
  const existing = matchesContainer.querySelector('.empty-state-card');
  if (existing) return; // already showing

  const section = document.createElement('section');
  section.className = 'empty-state-card';
  section.innerHTML = `
    <div class="polaroid"><div class="polaroid-photo"></div></div>
    <h2>No matches yet</h2>
    <p>Your match history will show up here</p>
    <button class="btn-primary" id="optInBtn" style="margin-top:1rem">Opt in for this week</button>
  `;
  hero.insertAdjacentElement('afterend', section);

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

function renderMatches(matches) {
  // Remove empty state if present
  const empty = matchesContainer.querySelector('.empty-state-card');
  if (empty) empty.remove();

  const hero = matchesContainer.querySelector('.matches-hero');

  // Add opt-in button to hero
  if (!hero.querySelector('#optInBtn')) {
    const optBtn = document.createElement('button');
    optBtn.className = 'btn-primary';
    optBtn.id = 'optInBtn';
    optBtn.textContent = 'Opt in for next week';
    optBtn.style.marginTop = '1rem';
    hero.appendChild(optBtn);
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

  const grid = document.createElement('section');
  grid.className = 'matches-grid';

  for (const match of matches) {
    const card = document.createElement('div');
    card.className = 'match-card';

    const score = Math.round(match.compatibility_score);
    const reasons = (match.match_reasons || [])
      .map((r) => `<li>${r}</li>`)
      .join('');
    const photoSrc = match.partner.photo_url || '';
    const photoHtml = photoSrc
      ? `<img class="match-photo" src="${photoSrc}" alt="${match.partner.name}" />`
      : `<div class="match-photo match-photo--placeholder"></div>`;

    card.innerHTML = `
      ${photoHtml}
      <div class="match-info">
        <h3>${match.partner.name}</h3>
        <p class="match-major">${match.partner.major}</p>
        <p class="match-score">${score}% compatibility</p>
        ${reasons ? `<ul class="match-reasons">${reasons}</ul>` : ''}
        ${match.partner.date_ideas ? `<p class="match-date-ideas">${match.partner.date_ideas}</p>` : ''}
        <div class="match-actions">
          ${match.status === 'pending' ? `
            <button class="btn-primary btn-sm match-accept" data-id="${match.id}">Accept</button>
            <button class="btn-ghost btn-sm match-decline" data-id="${match.id}">Decline</button>
          ` : match.status === 'accepted' ? `
            <a href="/chat/${match.id}" class="btn-primary btn-sm">Chat</a>
          ` : `
            <span class="match-status">${match.status}</span>
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

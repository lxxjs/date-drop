const email = window.__verifyEmail;
const codeInput = document.getElementById('codeInput');
const verifyBtn = document.getElementById('verifyBtn');
const resendBtn = document.getElementById('resendBtn');
const resendTimer = document.getElementById('resendTimer');
const statusMessage = document.getElementById('statusMessage');

let resendCountdown = null;

// ── Helpers ─────────────────────────────────────────────────

function setStatus(message, type = '') {
  statusMessage.textContent = message;
  statusMessage.className = 'status-message';
  if (type) statusMessage.classList.add(type);
}

function setButtonState(button, enabled) {
  button.disabled = !enabled;
  button.classList.toggle('active', enabled);
}

// ── Code input validation ───────────────────────────────────

function updateCodeState() {
  const valid = /^\d{6}$/.test(codeInput.value.trim());
  setButtonState(verifyBtn, valid);
}

codeInput.addEventListener('input', updateCodeState);

codeInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !verifyBtn.disabled) verifyBtn.click();
});

// ── Verify code ─────────────────────────────────────────────

verifyBtn.addEventListener('click', async () => {
  if (verifyBtn.disabled) return;
  const code = codeInput.value.trim();
  setButtonState(verifyBtn, false);
  setStatus('Verifying...');

  try {
    const res = await fetch('/api/verify-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code }),
    });
    const data = await res.json();

    if (!data.ok) {
      setStatus(data.message, 'error');
      setButtonState(verifyBtn, true);
      return;
    }

    setStatus('Verified! Redirecting...', 'success');
    if (data.has_profile) {
      window.location.href = '/home';
    } else {
      window.location.href = `/questions?email=${encodeURIComponent(email)}`;
    }
  } catch {
    setStatus('Network error. Please try again.', 'error');
    setButtonState(verifyBtn, true);
  }
});

// ── Resend cooldown ─────────────────────────────────────────

function startResendCooldown() {
  let remaining = 45;
  resendBtn.disabled = true;
  resendTimer.textContent = `(${remaining}s)`;

  clearResendCooldown();
  resendCountdown = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      clearResendCooldown();
      resendBtn.disabled = false;
      resendTimer.textContent = '';
    } else {
      resendTimer.textContent = `(${remaining}s)`;
    }
  }, 1000);
}

function clearResendCooldown() {
  if (resendCountdown) {
    clearInterval(resendCountdown);
    resendCountdown = null;
  }
}

resendBtn.addEventListener('click', async () => {
  if (resendBtn.disabled) return;
  setStatus('Resending code...');

  try {
    const res = await fetch('/api/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();

    if (!data.ok) {
      setStatus(data.message, 'error');
      return;
    }

    setStatus('New code sent!', 'success');
    startResendCooldown();
    codeInput.value = '';
    codeInput.focus();
  } catch {
    setStatus('Network error. Please try again.', 'error');
  }
});

// ── Init ────────────────────────────────────────────────────

startResendCooldown();
codeInput.focus();
updateCodeState();

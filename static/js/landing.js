/* global sb, syncSession, getAllowedDomains, isAllowedSchoolEmail */

const emailInput = document.getElementById('emailInput');
const sendCodeBtn = document.getElementById('sendCodeBtn');
const statusMessage = document.getElementById('statusMessage');

// ── UI state helpers ─────────────────────────────────────────

let verificationMode = false;

function setStatus(message, type = '') {
  statusMessage.textContent = message;
  statusMessage.className = 'status-message';
  if (type) statusMessage.classList.add(type);
}

function setButtonState(button, enabled) {
  button.disabled = !enabled;
  button.classList.toggle('active', enabled);
}

// ── Verification UI ──────────────────────────────────────────

function showCodeInput() {
  verificationMode = true;
  const form = document.getElementById('authForm');
  const hint = form.querySelector('.form-hint');

  // Add OTP input
  const codeInput = document.createElement('input');
  codeInput.type = 'text';
  codeInput.id = 'codeInput';
  codeInput.className = 'email-input';
  codeInput.placeholder = 'Enter 8-digit code';
  codeInput.maxLength = 8;
  codeInput.inputMode = 'numeric';
  codeInput.autocomplete = 'one-time-code';
  form.insertBefore(codeInput, sendCodeBtn);

  emailInput.readOnly = true;
  emailInput.style.opacity = '0.6';
  sendCodeBtn.textContent = 'Verify';
  if (hint) hint.textContent = 'Check your email for the 8-digit verification code.';

  codeInput.focus();

  codeInput.addEventListener('input', () => {
    const valid = codeInput.value.trim().length === 8;
    setButtonState(sendCodeBtn, valid);
  });

  codeInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !sendCodeBtn.disabled) sendCodeBtn.click();
  });

  setButtonState(sendCodeBtn, false);
}

// ── Main flow ────────────────────────────────────────────────

async function handleSendCode(email) {
  setButtonState(sendCodeBtn, false);
  setStatus('Sending verification code...');

  const { error } = await sb.auth.signInWithOtp({ email });

  if (error) {
    setStatus(error.message || 'Failed to send code.', 'error');
    setButtonState(sendCodeBtn, true);
    return;
  }

  setStatus('Verification code sent! Check your email.');
  showCodeInput();
}

async function handleVerifyCode(email, code) {
  setButtonState(sendCodeBtn, false);
  setStatus('Verifying...');

  const { data, error } = await sb.auth.verifyOtp({
    email,
    token: code,
    type: 'email',
  });

  if (error) {
    setStatus(error.message || 'Incorrect code. Please try again.', 'error');
    setButtonState(sendCodeBtn, true);
    return;
  }

  // Sync session to Flask backend (sets httpOnly cookie)
  await syncSession(data.session);

  // Check if the user already has a profile
  setStatus('Signed in! Checking profile...');
  try {
    const res = await fetch('/api/profile-status', { credentials: 'same-origin' });
    const result = await res.json();

    if (result.ok && result.has_profile) {
      window.location.href = '/home';
    } else {
      window.location.href = `/questions?email=${encodeURIComponent(email)}`;
    }
  } catch {
    window.location.href = `/questions?email=${encodeURIComponent(email)}`;
  }
}

// ── Event listeners ──────────────────────────────────────────

async function updateEmailState() {
  const domains = await getAllowedDomains();
  const valid = isAllowedSchoolEmail(emailInput.value, domains);
  setButtonState(sendCodeBtn, valid && !verificationMode);

  if (!emailInput.value.trim()) {
    setStatus('');
    return;
  }

  if (!valid) {
    setStatus('Please use an approved campus email.', 'error');
  } else if (!verificationMode) {
    setStatus('Looks good. Click Get started to continue.');
  }
}

emailInput.addEventListener('input', updateEmailState);

emailInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !sendCodeBtn.disabled) sendCodeBtn.click();
});

sendCodeBtn.addEventListener('click', async () => {
  if (sendCodeBtn.disabled) return;

  const email = emailInput.value.trim().toLowerCase();

  if (verificationMode) {
    const codeInput = document.getElementById('codeInput');
    const code = codeInput ? codeInput.value.trim() : '';
    if (code.length !== 8) return;
    await handleVerifyCode(email, code);
  } else {
    const domains = await getAllowedDomains();
    if (!isAllowedSchoolEmail(email, domains)) return;
    await handleSendCode(email);
  }
});

// ── Init ─────────────────────────────────────────────────────

updateEmailState();

// Auto-redirect if user already has a session with a completed profile
(async () => {
  const { data: { session } } = await sb.auth.getSession();
  if (session) {
    await syncSession(session);
    try {
      const res = await fetch('/api/profile-status', { credentials: 'same-origin' });
      const result = await res.json();
      if (result.ok && result.has_profile) {
        window.location.href = '/home';
      }
    } catch {
      // ignore
    }
  }
})();

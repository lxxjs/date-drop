/* global sb, syncSession, getAllowedDomains, isAllowedSchoolEmail, escapeHtml */

const inviteCode = window.__INVITE_CODE__;

const loadingState = document.getElementById('loadingState');
const validState = document.getElementById('validState');
const errorState = document.getElementById('errorState');

// ── Load invite data ─────────────────────────────────────────

(async () => {
  // If user is already logged in, redirect to /home
  const { data: { session } } = await sb.auth.getSession();
  if (session) {
    await syncSession(session);
    try {
      const res = await fetch('/api/profile-status', { credentials: 'same-origin' });
      const result = await res.json();
      if (result.ok && result.has_profile) {
        window.location.href = '/home';
        return;
      }
    } catch {
      // continue to show invite page
    }
  }

  // Fetch invite metadata
  try {
    const res = await fetch(`/api/invite/${encodeURIComponent(inviteCode)}`);
    const data = await res.json();

    if (!data.ok) {
      showError(data.message || 'This invite link is no longer valid.');
      return;
    }

    // Show the valid invite state
    document.getElementById('schoolName').textContent = data.school_name;
    document.getElementById('socialProof').textContent = data.social_proof;

    loadingState.hidden = true;
    validState.hidden = false;

    initAuthForm();
  } catch {
    showError('Could not load invite. Please try again.');
  }
})();

function showError(message) {
  loadingState.hidden = true;
  errorState.hidden = false;
  document.getElementById('errorMessage').textContent = message;
}

// ── Auth form (mirrors landing.js) ───────────────────────────

function initAuthForm() {
  const emailInput = document.getElementById('emailInput');
  const sendCodeBtn = document.getElementById('sendCodeBtn');
  const statusMessage = document.getElementById('statusMessage');
  let verificationMode = false;

  function setStatus(msg, type) {
    statusMessage.textContent = msg;
    statusMessage.className = 'status-message';
    if (type) statusMessage.classList.add(type);
  }

  function setButtonState(btn, enabled) {
    btn.disabled = !enabled;
  }

  function showCodeInput() {
    verificationMode = true;
    const form = document.getElementById('authForm');
    const hint = form.querySelector('.form-hint');

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
      setButtonState(sendCodeBtn, codeInput.value.trim().length === 8);
    });

    codeInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !sendCodeBtn.disabled) sendCodeBtn.click();
    });

    setButtonState(sendCodeBtn, false);
  }

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

    const { data, error } = await sb.auth.verifyOtp({ email, token: code, type: 'email' });
    if (error) {
      setStatus(error.message || 'Incorrect code.', 'error');
      setButtonState(sendCodeBtn, true);
      return;
    }

    await syncSession(data.session);

    // Store invite code in sessionStorage so it can be redeemed after profile creation
    sessionStorage.setItem('invite_code', inviteCode);

    setStatus('Signed in! Checking profile...');
    try {
      const res = await fetch('/api/profile-status', { credentials: 'same-origin' });
      const result = await res.json();
      if (result.ok && result.has_profile) {
        // Profile exists — redeem invite and go home
        await redeemInvite();
        window.location.href = '/home';
      } else {
        window.location.href = '/questions';
      }
    } catch {
      window.location.href = '/questions';
    }
  }

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
      setStatus('Looks good. Click Sign up to continue.');
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

  updateEmailState();
}

async function redeemInvite() {
  const code = sessionStorage.getItem('invite_code');
  if (!code) return;

  try {
    await fetch('/api/invite/redeem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ invite_code: code }),
    });
    sessionStorage.removeItem('invite_code');
  } catch {
    // Fire-and-forget — don't block the user
  }
}

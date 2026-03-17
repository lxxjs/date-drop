const allowedDomains = ['@stu.pku.edu.cn', '@mails.tsinghua.edu.cn'];

const emailInput = document.getElementById('emailInput');
const sendCodeBtn = document.getElementById('sendCodeBtn');
const statusMessage = document.getElementById('statusMessage');

function normalizeEmail(value) {
  return value.trim().toLowerCase();
}

function isAllowedSchoolEmail(value) {
  const email = normalizeEmail(value);
  return allowedDomains.some((domain) => email.endsWith(domain));
}

function setStatus(message, type = '') {
  statusMessage.textContent = message;
  statusMessage.className = 'status-message';
  if (type) {
    statusMessage.classList.add(type);
  }
}

function setButtonState(button, enabled) {
  button.disabled = !enabled;
  button.classList.toggle('active', enabled);
}

function updateEmailState() {
  const valid = isAllowedSchoolEmail(emailInput.value);
  setButtonState(sendCodeBtn, valid);
  if (!emailInput.value.trim()) {
    setStatus('');
    return;
  }

  if (!valid) {
    setStatus('Please use a PKU or Tsinghua campus email.', 'error');
  } else {
    setStatus('Looks good. Click Get started to continue.');
  }
}

emailInput.addEventListener('input', updateEmailState);

sendCodeBtn.addEventListener('click', () => {
  if (sendCodeBtn.disabled) return;

  const email = normalizeEmail(emailInput.value);
  setButtonState(sendCodeBtn, false);
  setStatus('Checking your profile...');

  fetch(`/api/profile-status?email=${encodeURIComponent(email)}`)
    .then((response) => response.json())
    .then((result) => {
      if (result.ok && result.has_profile) {
        setStatus('Welcome back. Redirecting you to home...');
        window.location.href = '/home';
        return;
      }

      window.location.href = `/questions?email=${encodeURIComponent(email)}`;
    })
    .catch(() => {
      setStatus('Could not check profile status. Continuing to questionnaire.', 'error');
      window.location.href = `/questions?email=${encodeURIComponent(email)}`;
    });
});

updateEmailState();

fetch('/api/profile-status')
  .then((response) => response.json())
  .then((result) => {
    if (result.ok && result.has_profile) {
      window.location.href = '/home';
    }
  })
  .catch(() => {});

const cupidForm = document.getElementById('cupidForm');
const shipBtn = document.getElementById('shipBtn');
const shipStatus = document.getElementById('shipStatus');
const firstEmailInput = document.getElementById('firstEmail');
const secondEmailInput = document.getElementById('secondEmail');

let shipsLeft = 4;

function normalizeEmail(value) {
  return String(value || '').trim().toLowerCase();
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizeEmail(value));
}

function refreshShipButton() {
  shipBtn.textContent = shipsLeft > 0 ? `Ship It! (${shipsLeft} left)` : 'No ships left';
  shipBtn.disabled = shipsLeft <= 0;
}

function setStatus(message, isError = false) {
  shipStatus.textContent = message;
  shipStatus.style.color = isError ? '#ffd9d9' : '#fff2d8';
}

cupidForm.addEventListener('submit', (event) => {
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

  shipsLeft -= 1;
  refreshShipButton();
  setStatus(`Shipped ${firstEmail} + ${secondEmail}. Good luck!`);
  cupidForm.reset();
});

refreshShipButton();

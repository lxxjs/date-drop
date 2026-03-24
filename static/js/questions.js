/* global escapeHtml */
/* ── data ───────────────────────────────────────────────────── */

const TRAITS = [
  'Adventurous', 'Ambitious', 'Caring', 'Confident', 'Creative',
  'Curious', 'Disciplined', 'Empathetic', 'Funny', 'Genuine',
  'Independent', 'Intellectual', 'Kind', 'Loyal', 'Motivated',
  'Open-minded', 'Optimistic', 'Passionate', 'Reliable', 'Spontaneous',
];

const SCALE_GROUP_ONE = [
  { name: 'children',       label: 'Having children is essential for a fulfilling life.',                   lo: 'Strongly disagree', hi: 'Strongly agree' },
  { name: 'religion_imp',   label: 'Religion or spirituality plays an important role in my life.',          lo: 'Not at all',        hi: 'Central to my life' },
  { name: 'career_fam',     label: 'I would prioritize family over career advancement.',                    lo: 'Career first',      hi: 'Family first' },
  { name: 'monogamy',       label: 'I believe in strict monogamy.',                                         lo: 'Open / flexible',   hi: 'Strictly monogamous' },
  { name: 'shared_values',  label: 'Shared values matter more than shared interests in a relationship.',    lo: 'Interests matter more', hi: 'Values matter more' },
  { name: 'conflict_style', label: 'I prefer to address conflicts immediately rather than giving space.',   lo: 'Need space first',  hi: 'Address it now' },
];

const SCALE_GROUP_TWO = [
  { name: 'social_energy',  label: 'I recharge by being around people (vs. alone time).',                  lo: 'Introvert',         hi: 'Extrovert' },
  { name: 'politics',       label: 'My political views lean…',                                              lo: 'Very liberal',      hi: 'Very conservative' },
  { name: 'ambition',       label: 'Professional ambition is very important to me.',                        lo: 'Life > work',       hi: 'Highly ambitious' },
  { name: 'tidiness',       label: 'I keep my living space very tidy.',                                     lo: 'Controlled chaos',  hi: 'Spotless' },
  { name: 'spontaneity',    label: 'I prefer spontaneous plans over scheduled ones.',                       lo: 'Love to plan',      hi: 'Totally spontaneous' },
  { name: 'physical',       label: 'Physical affection is very important to me in a relationship.',         lo: 'Not a priority',    hi: 'Very important' },
  { name: 'comm_freq',      label: 'I like to stay in close contact with a partner throughout the day.',    lo: 'Lots of space',     hi: 'Constant touch' },
];

const SCALE_GROUP_THREE = [
  { name: 'future_city',    label: 'I plan to stay in this city long-term.',                                lo: 'Likely to move',    hi: 'Staying here' },
  { name: 'pace',           label: 'I live life at a fast pace.',                                           lo: 'Slow & steady',     hi: 'Fast-paced' },
  { name: 'humor',          label: 'Humor and laughter are essential in a relationship.',                   lo: 'Nice but optional', hi: 'Absolutely essential' },
];

/* ── helpers ────────────────────────────────────────────────── */

const TOTAL_STEPS = 5;

function buildChipGrid(containerId, maxSelect) {
  const container = document.getElementById(containerId);
  if (!container) return;
  TRAITS.forEach((trait) => {
    const label = document.createElement('label');
    label.className = 'chip';
    label.innerHTML = `<input type="checkbox" name="${containerId}" value="${trait}" /><span>${trait}</span>`;
    container.appendChild(label);
  });

  container.addEventListener('change', () => {
    const checked = container.querySelectorAll('input:checked');
    if (checked.length >= maxSelect) {
      container.querySelectorAll('input:not(:checked)').forEach((cb) => { cb.disabled = true; });
    } else {
      container.querySelectorAll('input').forEach((cb) => { cb.disabled = false; });
    }
  });
}

function buildScaleGroup(containerId, questions) {
  const container = document.getElementById(containerId);
  if (!container) return;
  questions.forEach((q) => {
    const card = document.createElement('div');
    card.className = 'scale-card';
    card.innerHTML = `
      <h3>${q.label}</h3>
      <div class="scale-meta"><span>${q.lo}</span><span>${q.hi}</span></div>
      <div class="scale-control">
        <input type="range" name="${q.name}" min="1" max="7" value="4"
               oninput="this.nextElementSibling.textContent = this.value" />
        <span class="scale-value">4</span>
      </div>`;
    container.appendChild(card);
  });
}

/* ── quick match mode ──────────────────────────────────────── */

let quickMatchMode = false;

// Full mode: steps 1-5. Quick mode: steps 1, 2, 3 (skip 4 & 5).
// Step 3 has the 6 quick-match dimensions (SCALE_GROUP_ONE).
const FULL_STEPS = [1, 2, 3, 4, 5];
const QUICK_STEPS = [1, 2, 3];
let activeSteps = FULL_STEPS;

function getStepSequence() {
  return quickMatchMode ? QUICK_STEPS : FULL_STEPS;
}

function getTotalSteps() {
  return getStepSequence().length;
}

function getStepIndex(stepNumber) {
  return getStepSequence().indexOf(stepNumber);
}

const modeQuick = document.getElementById('modeQuick');
const modeFull = document.getElementById('modeFull');

if (modeQuick && modeFull) {
  modeQuick.addEventListener('change', () => {
    if (modeQuick.checked) {
      quickMatchMode = true;
      activeSteps = QUICK_STEPS;
      // Reset to step 1 if currently on a skipped step
      if (getStepIndex(currentStep) === -1) {
        currentStep = 1;
      }
      showStep(currentStep);
    }
  });

  modeFull.addEventListener('change', () => {
    if (modeFull.checked) {
      quickMatchMode = false;
      activeSteps = FULL_STEPS;
      showStep(currentStep);
    }
  });
}

/* ── state ──────────────────────────────────────────────────── */

let currentStep = 1;

function validateStep(stepNumber) {
  const step = document.querySelector(`.step[data-step="${stepNumber}"]`);
  if (!step) return true;

  const fields = step.querySelectorAll('input, select, textarea');
  for (const field of fields) {
    if (!field.checkValidity()) {
      field.reportValidity();
      return false;
    }
  }

  return true;
}

function showStep(n) {
  document.querySelectorAll('.step').forEach((s) => s.classList.remove('is-active'));
  const target = document.querySelector(`.step[data-step="${n}"]`);
  if (target) target.classList.add('is-active');

  const idx = getStepIndex(n);
  const total = getTotalSteps();
  const pct = Math.round(((idx + 1) / total) * 100);
  document.getElementById('progressLabel').textContent = `Step ${idx + 1} of ${total}`;
  document.getElementById('progressPercent').textContent = `${pct}%`;
  document.getElementById('progressFill').style.width = `${pct}%`;

  document.getElementById('prevBtn').style.visibility = idx === 0 ? 'hidden' : 'visible';

  const isLast = idx === total - 1;
  document.getElementById('nextBtn').hidden = isLast;
  document.getElementById('submitBtn').hidden = !isLast;

  // Hide the mode toggle once past step 1
  const toggle = document.querySelector('.match-mode-toggle');
  if (toggle) toggle.style.display = n > 1 ? 'none' : '';

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ── init ───────────────────────────────────────────────────── */

buildChipGrid('selfTraits', 5);
buildChipGrid('partnerTraits', 5);
buildScaleGroup('scaleGroupOne', SCALE_GROUP_ONE);
buildScaleGroup('scaleGroupTwo', SCALE_GROUP_TWO);
buildScaleGroup('scaleGroupThree', SCALE_GROUP_THREE);

const badge = document.getElementById('emailBadge');
(async () => {
  try {
    const res = await fetch('/api/profile-status', { credentials: 'same-origin' });
    const data = await res.json();
    if (data.ok && badge) badge.textContent = data.email;
  } catch {
    // badge stays empty if session is unavailable
  }
})();

showStep(1);

/* ── navigation ─────────────────────────────────────────────── */

document.getElementById('nextBtn').addEventListener('click', () => {
  if (!validateStep(currentStep)) {
    return;
  }

  const steps = getStepSequence();
  const idx = getStepIndex(currentStep);
  if (idx < steps.length - 1) {
    currentStep = steps[idx + 1];
    showStep(currentStep);
  }
});

document.getElementById('prevBtn').addEventListener('click', () => {
  const steps = getStepSequence();
  const idx = getStepIndex(currentStep);
  if (idx > 0) {
    currentStep = steps[idx - 1];
    showStep(currentStep);
  }
});

/* ── photo preview ──────────────────────────────────────────── */

const photoUpload = document.getElementById('photoUpload');
if (photoUpload) {
  photoUpload.addEventListener('change', () => {
    const file = photoUpload.files[0];
    if (!file) return;
    const preview = document.getElementById('photoPreview');
    const img = document.getElementById('photoPreviewImage');
    img.src = URL.createObjectURL(file);
    preview.hidden = false;
  });
}

/* ── submit ─────────────────────────────────────────────────── */

function collectFormAnswers(formElement) {
  const formData = new FormData(formElement);
  const answers = {};

  for (const [key, value] of formData.entries()) {
    if (Object.prototype.hasOwnProperty.call(answers, key)) {
      if (Array.isArray(answers[key])) {
        answers[key].push(value);
      } else {
        answers[key] = [answers[key], value];
      }
    } else {
      answers[key] = value;
    }
  }

  const photoFile = photoUpload && photoUpload.files ? photoUpload.files[0] : null;
  if (photoFile) {
    answers.photoFileName = photoFile.name;
  }

  return answers;
}

function showCompletePanel(message, isError = false) {
  const panel = document.getElementById('completePanel');
  panel.hidden = false;
  panel.innerHTML = `<h3>${isError ? 'Could not save profile' : 'Profile complete'}</h3><p>${escapeHtml(message)}</p>`;
}

document.getElementById('questionnaireForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  if (!validateStep(currentStep)) {
    return;
  }

  const submitBtn = document.getElementById('submitBtn');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Saving...';

  const answers = collectFormAnswers(e.currentTarget);

  try {
    // Upload photo first if one is selected
    const photoFile = photoUpload && photoUpload.files ? photoUpload.files[0] : null;
    if (photoFile) {
      const photoData = new FormData();
      photoData.append('photo', photoFile);
      const photoRes = await fetch('/api/profile/photo', {
        method: 'POST',
        credentials: 'same-origin',
        body: photoData,
      });
      const photoResult = await photoRes.json();
      if (!photoRes.ok || !photoResult.ok) {
        throw new Error(photoResult.message || 'Photo upload failed.');
      }
    }

    const response = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ answers, quick_match: quickMatchMode }),
    });

    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.message || 'Unable to save profile.');
    }

    showCompletePanel('Your profile is saved. Redirecting to your home page...');
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    window.setTimeout(() => {
      window.location.href = '/home';
    }, 900);
  } catch (error) {
    showCompletePanel(error.message || 'Something went wrong while saving your profile.', true);
    submitBtn.disabled = false;
    submitBtn.textContent = 'Finish profile';
  }
});

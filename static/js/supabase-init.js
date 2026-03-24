/* global supabase */

/**
 * Initialize the Supabase client.
 * SUPABASE_URL and SUPABASE_ANON_KEY are injected by Flask templates as global vars.
 */
const sb = supabase.createClient(
  window.__SUPABASE_URL__,
  window.__SUPABASE_ANON_KEY__,
);

/**
 * After a successful OTP verification, send the tokens to the Flask backend
 * so it can set secure httpOnly cookies for server-side auth.
 */
async function syncSession(session) {
  if (!session) return false;
  try {
    const res = await fetch('/api/auth/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        access_token: session.access_token,
        refresh_token: session.refresh_token,
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      console.error('Session sync failed:', res.status, body);
      return false;
    }
    return true;
  } catch (err) {
    console.error('Session sync error:', err);
    return false;
  }
}

/**
 * Fetch the list of allowed school email domains from the backend.
 */
let _allowedDomains = null;
async function getAllowedDomains() {
  if (_allowedDomains) return _allowedDomains;
  try {
    const res = await fetch('/api/allowed-schools');
    const data = await res.json();
    _allowedDomains = (data.schools || []).map((s) => s.domain);
  } catch {
    // Fallback to hardcoded if endpoint is unreachable
    _allowedDomains = ['@stu.pku.edu.cn', '@mails.tsinghua.edu.cn'];
  }
  return _allowedDomains;
}

function isAllowedSchoolEmail(email, domains) {
  const normalized = email.trim().toLowerCase();
  return domains.some((domain) => normalized.endsWith(domain));
}

/**
 * Escape HTML to prevent XSS when inserting user-controlled text into innerHTML.
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

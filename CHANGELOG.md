# Changelog

All notable changes to Date Drop will be documented in this file.

## [0.1.0.0] - 2026-03-23

### Added
- Invite link system — viral growth loop with 5-invite quota, 30-day expiry, invite redemption, and inviter reveal
- Campus landing page at `/invite/<code>` with school name and social proof counter
- Email notifications for new matches via Resend (fire-and-forget)
- Quick match mode — 6-dimension questionnaire for faster onboarding
- Admin stats endpoint (`GET /api/admin/stats`) — signup count, invite conversion, match acceptance, chat initiation rate
- Questionnaire analytics events (started/completed) with mode tracking
- Centralized Flask error handlers (400, 401, 403, 404, 500)
- Test suite foundation — 29 tests covering invites, notifications, admin stats, and page rendering
- `TODOS.md` for tracking deferred work

### Changed
- Admin key comparison upgraded to constant-time `hmac.compare_digest`
- `escapeHtml` utility moved to shared `supabase-init.js` (DRY)
- Chat message send restores input on failure instead of silently dropping

### Removed
- `static/js/verify.js` and `templates/check-email.html` — unused legacy OTP flow

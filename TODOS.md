# TODOS

## P2: WeChat Mini Program Migration
**What:** Rewrite the frontend as a WeChat Mini Program for native WeChat experience (share cards, service messages, zero-friction invites).
**Why:** Chinese university students live in WeChat. A web app requires opening a browser; a Mini Program lives inside the app they use 100+ times daily.
**Effort:** L (human: ~4-6 weeks) / with CC: ~M (4-6 hours)
**Trigger:** Validate product-market fit on web first. When the invite loop proves users want the product, migrate to the platform they actually live on.
**Depends on:** Successful web launch and 100+ active users.
**Added:** 2026-03-23 via /plan-ceo-review

## P3: Invite Link Expiry Cleanup
**What:** Scheduled task to clean up expired invite records (>30 days) from the `invites` table.
**Why:** Without cleanup, the invites table grows unbounded. Not a problem at launch (500 rows) but matters at 10,000+ users (50k rows).
**Effort:** S (human: ~2 hours / CC: ~10 min)
**Trigger:** When invite table exceeds 10k rows.
**Depends on:** Invite system being live with significant usage.
**Added:** 2026-03-23 via /plan-eng-review

## P3: Revenue Model Exploration
**What:** Research and define the revenue model — freemium, subscription, or commission-based.
**Why:** Date Drop needs a path to revenue. Most campus dating apps monetize via premium features (extra matches, profile boosts, seeing who viewed you).
**Effort:** S (research, no code)
**Trigger:** After pilot with 50+ users and user feedback on what features they value most.
**Depends on:** Successful pilot and user interviews.
**Added:** 2026-03-23 via /plan-ceo-review

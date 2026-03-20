-- Date Drop: Initial Supabase Schema
-- Run this in the Supabase SQL Editor after creating your project.

-- ── Allowed Schools ─────────────────────────────────────────
CREATE TABLE public.allowed_schools (
  id         SERIAL PRIMARY KEY,
  name       TEXT NOT NULL,
  domain     TEXT UNIQUE NOT NULL,
  short_name TEXT,
  added_at   TIMESTAMPTZ DEFAULT now()
);

INSERT INTO public.allowed_schools (name, domain, short_name) VALUES
  ('Peking University',   '@stu.pku.edu.cn',         'PKU'),
  ('Tsinghua University', '@mails.tsinghua.edu.cn',   'THU');

-- ── Profiles ────────────────────────────────────────────────
CREATE TABLE public.profiles (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id              UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  email                TEXT UNIQUE NOT NULL,
  school_id            INT REFERENCES public.allowed_schools(id),
  full_name            TEXT NOT NULL,
  gender               TEXT NOT NULL,
  major_one            TEXT NOT NULL,
  major_two            TEXT,
  race                 TEXT NOT NULL,
  preferred_race       TEXT,
  height_cm            SMALLINT NOT NULL,
  preferred_height_min SMALLINT DEFAULT 155,
  preferred_height_max SMALLINT DEFAULT 190,
  relationship_goal    TEXT NOT NULL,
  birth_date           DATE NOT NULL,
  preferred_age_min    SMALLINT DEFAULT 18,
  preferred_age_max    SMALLINT DEFAULT 26,
  grad_year            SMALLINT NOT NULL,
  grad_preference      TEXT NOT NULL,
  religion             TEXT,
  preferred_religion   TEXT,
  date_ideas           TEXT,
  self_traits          TEXT[] DEFAULT '{}',
  partner_traits       TEXT[] DEFAULT '{}',
  -- 16 scale questions (1-7), core matching dimensions
  s_children           SMALLINT NOT NULL,
  s_religion_imp       SMALLINT NOT NULL,
  s_career_fam         SMALLINT NOT NULL,
  s_monogamy           SMALLINT NOT NULL,
  s_shared_values      SMALLINT NOT NULL,
  s_conflict_style     SMALLINT NOT NULL,
  s_social_energy      SMALLINT NOT NULL,
  s_politics           SMALLINT NOT NULL,
  s_ambition           SMALLINT NOT NULL,
  s_tidiness           SMALLINT NOT NULL,
  s_spontaneity        SMALLINT NOT NULL,
  s_physical           SMALLINT NOT NULL,
  s_comm_freq          SMALLINT NOT NULL,
  s_future_city        SMALLINT NOT NULL,
  s_pace               SMALLINT NOT NULL,
  s_humor              SMALLINT NOT NULL,
  phone_number         TEXT,
  final_notes          TEXT,
  friends              TEXT,
  photo_url            TEXT,
  is_opted_in          BOOLEAN DEFAULT FALSE,
  created_at           TIMESTAMPTZ DEFAULT now(),
  updated_at           TIMESTAMPTZ DEFAULT now()
);

-- ── Matches ─────────────────────────────────────────────────
CREATE TABLE public.matches (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_a_id           UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  user_b_id           UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  compatibility_score REAL NOT NULL,
  match_reasons       JSONB DEFAULT '[]',
  match_round         TEXT NOT NULL,
  status              TEXT NOT NULL DEFAULT 'pending',
  created_at          TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_a_id, user_b_id, match_round)
);

-- ── Messages (chat) ─────────────────────────────────────────
CREATE TABLE public.messages (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id   UUID NOT NULL REFERENCES public.matches(id) ON DELETE CASCADE,
  sender_id  UUID NOT NULL REFERENCES public.profiles(id),
  content    TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_messages_match ON public.messages(match_id, created_at);

-- ── Cupid Nominations ───────────────────────────────────────
CREATE TABLE public.cupid_nominations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nominator_id    UUID NOT NULL REFERENCES public.profiles(id),
  nominee_a_email TEXT NOT NULL,
  nominee_b_email TEXT NOT NULL,
  match_round     TEXT NOT NULL,
  points_awarded  SMALLINT DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_cupid_nominator ON public.cupid_nominations(nominator_id, match_round);

-- ── Row Level Security ──────────────────────────────────────
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cupid_nominations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.allowed_schools ENABLE ROW LEVEL SECURITY;

-- Allow public read of allowed_schools (needed for frontend domain validation)
CREATE POLICY "Anyone can read allowed schools"
  ON public.allowed_schools FOR SELECT
  USING (true);

-- Profiles: users can read/update their own profile
CREATE POLICY "Users can read own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = user_id);

-- Matches: users can read their own matches
CREATE POLICY "Users can read own matches"
  ON public.matches FOR SELECT
  USING (
    user_a_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
    OR user_b_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
  );

-- Messages: users can read/write messages for their matches
CREATE POLICY "Users can read messages for their matches"
  ON public.messages FOR SELECT
  USING (
    match_id IN (
      SELECT id FROM public.matches
      WHERE user_a_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
         OR user_b_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
    )
  );

CREATE POLICY "Users can send messages in their matches"
  ON public.messages FOR INSERT
  WITH CHECK (
    sender_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
    AND match_id IN (
      SELECT id FROM public.matches
      WHERE user_a_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
         OR user_b_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
    )
  );

-- Cupid: users can read all nominations (for leaderboard) and insert their own
CREATE POLICY "Anyone can read cupid nominations"
  ON public.cupid_nominations FOR SELECT
  USING (true);

CREATE POLICY "Users can insert own nominations"
  ON public.cupid_nominations FOR INSERT
  WITH CHECK (
    nominator_id IN (SELECT id FROM public.profiles WHERE user_id = auth.uid())
  );

-- ── Enable Realtime on messages table ───────────────────────
-- Note: Also enable this in the Supabase Dashboard under
-- Database > Replication > enable for "messages" table
ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;

-- ── School email validation trigger ─────────────────────────
-- Rejects signups from non-allowed email domains
CREATE OR REPLACE FUNCTION public.validate_school_email()
RETURNS TRIGGER AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.allowed_schools
    WHERE NEW.email LIKE '%' || domain
  ) THEN
    RAISE EXCEPTION 'Only emails from approved schools are allowed.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER enforce_school_email
  BEFORE INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.validate_school_email();

-- ── Auto-update updated_at on profiles ──────────────────────
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

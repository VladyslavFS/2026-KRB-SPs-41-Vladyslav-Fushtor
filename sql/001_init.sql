CREATE TABLE IF NOT EXISTS public.app_heartbeat (
  id INTEGER PRIMARY KEY,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO public.app_heartbeat (id, updated_at)
VALUES (1, now())
ON CONFLICT (id) DO UPDATE SET updated_at = EXCLUDED.updated_at;

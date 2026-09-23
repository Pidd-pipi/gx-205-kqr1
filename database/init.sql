CREATE TABLE IF NOT EXISTS seed_notes (
  id SERIAL PRIMARY KEY,
  label VARCHAR(64) NOT NULL UNIQUE,
  content VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO seed_notes (label, content)
VALUES ('demo', '逻辑推理题库系统初始化脚本已执行')
ON CONFLICT (label) DO NOTHING;

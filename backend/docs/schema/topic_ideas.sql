-- VO Mate topic idea generation schema.
-- Run manually against PostgreSQL when enabling persistent topic generation.
-- This script is idempotent for new columns and does not require SQLAdmin auto-create.

create table if not exists topic_ideas (
  id varchar(64) primary key,
  workspace_id varchar(64) not null,
  title varchar(500) not null,
  topic varchar(255),
  angle text,
  category varchar(128),
  target_audience varchar(255),
  platforms jsonb not null default '[]'::jsonb,
  predicted_score double precision,
  seo_score double precision,
  audience_score double precision,
  difficulty_score double precision,
  risk text,
  recommend_reason text,
  evidence jsonb not null default '[]'::jsonb,
  suggested_titles jsonb not null default '[]'::jsonb,
  suggested_hooks jsonb not null default '[]'::jsonb,
  suggested_tags jsonb not null default '[]'::jsonb,
  next_actions jsonb not null default '[]'::jsonb,
  generation_id varchar(64),
  source_payload jsonb not null default '{}'::jsonb,
  status varchar(64) not null default 'idea',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table topic_ideas add column if not exists topic varchar(255);
alter table topic_ideas add column if not exists category varchar(128);
alter table topic_ideas add column if not exists target_audience varchar(255);
alter table topic_ideas add column if not exists platforms jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists recommend_reason text;
alter table topic_ideas add column if not exists evidence jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists suggested_titles jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists suggested_hooks jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists suggested_tags jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists next_actions jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists generation_id varchar(64);
alter table topic_ideas add column if not exists source_payload jsonb not null default '{}'::jsonb;

create index if not exists ix_topic_ideas_workspace_id on topic_ideas (workspace_id);
create index if not exists ix_topic_ideas_category on topic_ideas (category);
create index if not exists ix_topic_ideas_generation_id on topic_ideas (generation_id);

create table if not exists ai_generations (
  id varchar(64) primary key,
  workspace_id varchar(64) not null,
  workflow varchar(64) not null,
  provider varchar(64) not null default 'mock',
  model varchar(128),
  prompt_version varchar(32) not null default 'v0.1',
  input_payload jsonb not null default '{}'::jsonb,
  evidence_ids jsonb not null default '[]'::jsonb,
  output_payload jsonb,
  error text,
  status varchar(32) not null default 'succeeded',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_ai_generations_workspace_id on ai_generations (workspace_id);
create index if not exists ix_ai_generations_workflow on ai_generations (workflow);
create index if not exists ix_ai_generations_status on ai_generations (status);

-- Evidence lookup indexes for topic generation. These do not recreate the base
-- tables; they only speed up reads when the standard PostgreSQL layer exists.
create index if not exists ix_content_items_topic_evidence
  on content_items (workspace_id, platform, score desc, views desc, published_at desc);

create index if not exists ix_agent_memory_records_topic_evidence
  on agent_memory_records (workspace_id, account_id, platform, status, memory_type);

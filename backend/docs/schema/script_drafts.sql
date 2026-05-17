-- VO Mate script draft version schema.
-- Run manually against PostgreSQL when enabling persistent script workspace versions.
-- This script is idempotent for new columns and does not require SQLAdmin auto-create.

create table if not exists script_drafts (
  id varchar(64) primary key,
  workspace_id varchar(64) not null,
  topic_idea_id varchar(64),
  title varchar(500) not null,
  body text,
  platform varchar(32),
  status varchar(64) not null default 'draft',
  current_version_id varchar(64),
  adopted_version_id varchar(64),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table script_drafts add column if not exists current_version_id varchar(64);
alter table script_drafts add column if not exists adopted_version_id varchar(64);

create index if not exists ix_script_drafts_workspace_id on script_drafts (workspace_id);
create index if not exists ix_script_drafts_topic_idea_id on script_drafts (topic_idea_id);
create index if not exists ix_script_drafts_current_version_id on script_drafts (current_version_id);
create index if not exists ix_script_drafts_adopted_version_id on script_drafts (adopted_version_id);

create table if not exists script_draft_versions (
  id varchar(64) primary key,
  draft_id varchar(64) not null,
  version_no integer not null default 1,
  label varchar(255) not null,
  platform varchar(32),
  duration_seconds integer,
  body text not null default '',
  description text,
  tags jsonb not null default '[]'::jsonb,
  title_candidates jsonb not null default '[]'::jsonb,
  source_type varchar(64) not null default 'user_save',
  parent_version_id varchar(64),
  generation_id varchar(64),
  status varchar(64) not null default 'candidate',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_script_draft_versions_draft_id on script_draft_versions (draft_id);
create index if not exists ix_script_draft_versions_source_type on script_draft_versions (source_type);
create index if not exists ix_script_draft_versions_parent_version_id on script_draft_versions (parent_version_id);
create index if not exists ix_script_draft_versions_generation_id on script_draft_versions (generation_id);
create index if not exists ix_script_draft_versions_status on script_draft_versions (status);

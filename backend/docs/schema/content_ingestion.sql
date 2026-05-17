-- VO Mate content ingestion schema.
-- Run manually against PostgreSQL when enabling the Raw -> standard content ETL.
-- This script is idempotent and does not require SQLAdmin auto-create.

create table if not exists content_items (
  id varchar(64) primary key,
  workspace_id varchar(64) not null,
  platform_account_id varchar(64),
  platform varchar(32) not null,
  external_content_id varchar(255),
  title varchar(500) not null,
  description text,
  status varchar(64) not null default 'published',
  published_at timestamptz,
  duration_seconds integer,
  content_type varchar(64),
  cover_url text,
  video_url text,
  topic_cluster_id varchar(64),
  raw_collection varchar(128),
  raw_document_id varchar(255),
  views integer not null default 0,
  likes integer not null default 0,
  comments integer not null default 0,
  saves integer not null default 0,
  shares integer not null default 0,
  completion_rate double precision,
  followers_gained integer not null default 0,
  score double precision,
  has_asr boolean not null default false,
  reviewed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table content_items add column if not exists description text;
alter table content_items add column if not exists content_type varchar(64);
alter table content_items add column if not exists cover_url text;
alter table content_items add column if not exists video_url text;
alter table content_items add column if not exists topic_cluster_id varchar(64);
alter table content_items add column if not exists raw_collection varchar(128);
alter table content_items add column if not exists raw_document_id varchar(255);

create index if not exists ix_content_items_workspace_id on content_items (workspace_id);
create index if not exists ix_content_items_platform on content_items (platform);
create index if not exists ix_content_items_platform_account_id on content_items (platform_account_id);
create index if not exists ix_content_items_external_content_id on content_items (external_content_id);
create index if not exists ix_content_items_published_at on content_items (published_at);
create index if not exists ix_content_items_topic_cluster_id on content_items (topic_cluster_id);
create index if not exists ix_content_items_raw_document_id on content_items (raw_document_id);
create unique index if not exists ux_content_items_workspace_platform_external
  on content_items (workspace_id, platform, external_content_id)
  where external_content_id is not null;

create table if not exists content_lifetime_metrics (
  content_id varchar(64) primary key,
  play_count integer not null default 0,
  like_count integer not null default 0,
  comment_count integer not null default 0,
  share_count integer not null default 0,
  collect_count integer not null default 0,
  follow_count integer not null default 0,
  profile_visit_count integer not null default 0,
  avg_view_duration double precision,
  avg_view_percent double precision,
  finish_rate double precision,
  five_second_retention double precision,
  bounce_rate double precision,
  negative_feedback_count integer not null default 0,
  metric_score double precision,
  raw_document_id varchar(255),
  updated_at timestamptz not null default now()
);

alter table content_lifetime_metrics add column if not exists profile_visit_count integer not null default 0;
alter table content_lifetime_metrics add column if not exists avg_view_percent double precision;
alter table content_lifetime_metrics add column if not exists five_second_retention double precision;
alter table content_lifetime_metrics add column if not exists bounce_rate double precision;
alter table content_lifetime_metrics add column if not exists negative_feedback_count integer not null default 0;
alter table content_lifetime_metrics add column if not exists raw_document_id varchar(255);

create index if not exists ix_content_lifetime_metrics_raw_document_id
  on content_lifetime_metrics (raw_document_id);
create index if not exists ix_content_lifetime_metrics_score
  on content_lifetime_metrics (metric_score desc);

-- VO Mate content enrichment schema.
-- Run manually after content_ingestion.sql when enabling semantic evidence ETL.
-- This script is idempotent and does not require SQLAdmin auto-create.

create table if not exists content_text_assets (
  id serial primary key,
  content_id varchar(64) not null,
  asset_type varchar(64) not null,
  text text not null default '',
  language varchar(32),
  segments jsonb not null default '[]'::jsonb,
  raw_collection varchar(128),
  raw_document_id varchar(255),
  source varchar(128),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_content_text_assets_content_id on content_text_assets (content_id);
create index if not exists ix_content_text_assets_asset_type on content_text_assets (asset_type);
create index if not exists ix_content_text_assets_raw_document_id on content_text_assets (raw_document_id);
create index if not exists ix_content_text_assets_source on content_text_assets (source);
create unique index if not exists ux_content_text_assets_content_type_source
  on content_text_assets (content_id, asset_type, source);

create table if not exists content_tags (
  id serial primary key,
  content_id varchar(64) not null,
  tag varchar(255) not null,
  tag_type varchar(64) not null default 'topic',
  external_tag_id varchar(255),
  source varchar(128),
  position_start integer,
  position_end integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_content_tags_content_id on content_tags (content_id);
create index if not exists ix_content_tags_tag on content_tags (tag);
create index if not exists ix_content_tags_external_tag_id on content_tags (external_tag_id);
create index if not exists ix_content_tags_source on content_tags (source);
create unique index if not exists ux_content_tags_content_tag_source
  on content_tags (content_id, tag, source);

create table if not exists content_keywords (
  id serial primary key,
  content_id varchar(64) not null,
  keyword varchar(255) not null,
  keyword_type varchar(64) not null default 'search',
  score double precision,
  query_count_7d integer,
  source varchar(128),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_content_keywords_content_id on content_keywords (content_id);
create index if not exists ix_content_keywords_keyword on content_keywords (keyword);
create index if not exists ix_content_keywords_source on content_keywords (source);
create unique index if not exists ux_content_keywords_content_keyword_source
  on content_keywords (content_id, keyword, source);

create table if not exists content_traffic_sources (
  id serial primary key,
  content_id varchar(64) not null,
  source_name varchar(255) not null,
  source_type varchar(64) not null default 'traffic',
  ratio double precision,
  count integer,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_content_traffic_sources_content_id on content_traffic_sources (content_id);
create index if not exists ix_content_traffic_sources_source_name on content_traffic_sources (source_name);
create unique index if not exists ux_content_traffic_sources_content_source
  on content_traffic_sources (content_id, source_name, source_type);

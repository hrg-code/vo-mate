-- VO Mate topic idea generation dev seed.
-- This file is idempotent and intended for local/internal testing of
-- POST /api/v1/ai/topic-ideas with PostgreSQL-backed evidence.

create table if not exists workspaces (
  id varchar(64) primary key,
  name varchar(255) not null,
  description text,
  status varchar(32) not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists users (
  id varchar(64) primary key,
  email varchar(255) unique,
  name varchar(255) not null,
  role varchar(64) not null default 'member',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists workspace_members (
  id serial primary key,
  workspace_id varchar(64) not null,
  user_id varchar(64) not null,
  role varchar(64) not null default 'member',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_workspace_members_workspace_id on workspace_members (workspace_id);
create index if not exists ix_workspace_members_user_id on workspace_members (user_id);
create unique index if not exists ux_workspace_members_workspace_user
  on workspace_members (workspace_id, user_id);

create table if not exists platform_accounts (
  id varchar(64) primary key,
  workspace_id varchar(64) not null,
  platform varchar(32) not null,
  account_name varchar(255) not null,
  external_account_id varchar(255),
  status varchar(32) not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_platform_accounts_workspace_id on platform_accounts (workspace_id);
create index if not exists ix_platform_accounts_platform on platform_accounts (platform);

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

create index if not exists ix_content_lifetime_metrics_raw_document_id
  on content_lifetime_metrics (raw_document_id);
create index if not exists ix_content_lifetime_metrics_score
  on content_lifetime_metrics (metric_score desc);

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
create unique index if not exists ux_content_keywords_content_keyword_source
  on content_keywords (content_id, keyword, source);

create table if not exists agent_memory_records (
  id varchar(64) primary key,
  workspace_id varchar(64) not null,
  account_id varchar(128) not null,
  platform varchar(32) not null,
  memory_type varchar(64) not null,
  title varchar(500) not null,
  content text not null,
  summary text not null,
  metadata jsonb not null default '{}'::jsonb,
  source_type varchar(64) not null default 'manual',
  source_ids jsonb not null default '[]'::jsonb,
  confidence double precision not null default 0.5,
  evidence_count integer not null default 1,
  status varchar(32) not null default 'candidate',
  last_validated_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_agent_memory_records_workspace_id on agent_memory_records (workspace_id);
create index if not exists ix_agent_memory_records_account_id on agent_memory_records (account_id);
create index if not exists ix_agent_memory_records_platform on agent_memory_records (platform);
create index if not exists ix_agent_memory_records_memory_type on agent_memory_records (memory_type);
create index if not exists ix_agent_memory_records_status on agent_memory_records (status);
create index if not exists ix_agent_memory_records_topic_evidence
  on agent_memory_records (workspace_id, account_id, platform, status, memory_type);

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
alter table topic_ideas add column if not exists angle text;
alter table topic_ideas add column if not exists category varchar(128);
alter table topic_ideas add column if not exists target_audience varchar(255);
alter table topic_ideas add column if not exists platforms jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists predicted_score double precision;
alter table topic_ideas add column if not exists seo_score double precision;
alter table topic_ideas add column if not exists audience_score double precision;
alter table topic_ideas add column if not exists difficulty_score double precision;
alter table topic_ideas add column if not exists risk text;
alter table topic_ideas add column if not exists recommend_reason text;
alter table topic_ideas add column if not exists evidence jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists suggested_titles jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists suggested_hooks jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists suggested_tags jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists next_actions jsonb not null default '[]'::jsonb;
alter table topic_ideas add column if not exists generation_id varchar(64);
alter table topic_ideas add column if not exists source_payload jsonb not null default '{}'::jsonb;
alter table topic_ideas add column if not exists status varchar(64) not null default 'idea';
alter table topic_ideas add column if not exists created_at timestamptz not null default now();
alter table topic_ideas add column if not exists updated_at timestamptz not null default now();

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

insert into workspaces (id, name, description, status)
values (
  'ws_northstar',
  '北极星内容组',
  '内测账号：面向程序员职业成长、副业和 AI 工具效率主题的选题生成验证工作区。',
  'active'
)
on conflict (id) do update set
  name = excluded.name,
  description = excluded.description,
  status = excluded.status,
  updated_at = now();

insert into users (id, email, name, role, is_active)
values ('user_inner_test_owner', 'inner-test@example.local', '内测运营', 'owner', true)
on conflict (id) do update set
  email = excluded.email,
  name = excluded.name,
  role = excluded.role,
  is_active = excluded.is_active,
  updated_at = now();

insert into workspace_members (workspace_id, user_id, role)
values ('ws_northstar', 'user_inner_test_owner', 'owner')
on conflict (workspace_id, user_id) do update set
  role = excluded.role,
  updated_at = now();

insert into platform_accounts (
  id,
  workspace_id,
  platform,
  account_name,
  external_account_id,
  status
)
values (
  'douyin_demo',
  'ws_northstar',
  'douyin',
  '抖音 · 程序员老陈',
  'inner_test_douyin_demo',
  'active'
)
on conflict (id) do update set
  workspace_id = excluded.workspace_id,
  platform = excluded.platform,
  account_name = excluded.account_name,
  external_account_id = excluded.external_account_id,
  status = excluded.status,
  updated_at = now();

insert into content_items (
  id,
  workspace_id,
  platform_account_id,
  platform,
  external_content_id,
  title,
  description,
  status,
  published_at,
  duration_seconds,
  content_type,
  topic_cluster_id,
  raw_collection,
  raw_document_id,
  views,
  likes,
  comments,
  saves,
  shares,
  completion_rate,
  followers_gained,
  score,
  has_asr,
  reviewed
)
values
  (
    'ct_inner_pg_001',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'inner_douyin_001',
    '程序员副业接私活真实复盘：第一单到底亏在哪',
    '围绕程序员副业、接私活和报价失误做真实复盘，评论区集中追问如何避坑。',
    'published',
    '2026-04-28 20:30:00+08',
    76,
    'short_video',
    'cluster_programmer_career',
    'inner_test_seed',
    'raw_inner_douyin_001',
    186400,
    13820,
    924,
    6410,
    1480,
    0.46,
    1280,
    94,
    true,
    true
  ),
  (
    'ct_inner_pg_002',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'inner_douyin_002',
    '程序员职业成长不是换岗：先把这三个选择排个序',
    '职业成长方向内容，拆解大厂、外包、独立产品三种路径的短期成本。',
    'published',
    '2026-04-20 21:15:00+08',
    68,
    'short_video',
    'cluster_programmer_career',
    'inner_test_seed',
    'raw_inner_douyin_002',
    142900,
    9060,
    1120,
    4920,
    1210,
    0.43,
    930,
    90,
    true,
    true
  ),
  (
    'ct_inner_pg_003',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'inner_douyin_003',
    'AI 工具帮程序员省时间，但别先买课',
    '从 AI 编程工具的真实工作流切入，解释什么时候值得投入、什么时候只是换一种焦虑。',
    'published',
    '2026-04-12 19:45:00+08',
    61,
    'short_video',
    'cluster_ai_tools',
    'inner_test_seed',
    'raw_inner_douyin_003',
    118600,
    7340,
    688,
    3820,
    910,
    0.39,
    690,
    86,
    true,
    true
  ),
  (
    'ct_inner_pg_004',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'inner_douyin_004',
    '程序员简历改了十版，为什么还是没有面试',
    '职业转型与简历诊断内容，评论区出现大量具体简历问题。',
    'published',
    '2026-03-30 20:05:00+08',
    72,
    'short_video',
    'cluster_programmer_career',
    'inner_test_seed',
    'raw_inner_douyin_004',
    97300,
    5210,
    840,
    3500,
    620,
    0.36,
    510,
    80,
    true,
    true
  ),
  (
    'ct_inner_pg_005',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'inner_douyin_005',
    '别把独立产品做成自我感动：程序员变现前先问这四句',
    '独立产品和变现方向内容，表现中等但保存率高，可作为搜索承接样本。',
    'published',
    '2026-03-22 18:40:00+08',
    83,
    'short_video',
    'cluster_indie_product',
    'inner_test_seed',
    'raw_inner_douyin_005',
    75600,
    4120,
    396,
    2780,
    540,
    0.33,
    380,
    76,
    true,
    true
  ),
  (
    'ct_inner_pg_006',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'inner_douyin_006',
    '程序员焦虑期不要乱学，先做一张技能现金流表',
    '职业成长和学习路线内容，完播一般但收藏不错，适合作为避坑反例。',
    'published',
    '2026-03-10 21:00:00+08',
    88,
    'short_video',
    'cluster_programmer_career',
    'inner_test_seed',
    'raw_inner_douyin_006',
    43800,
    2100,
    260,
    1560,
    300,
    0.24,
    160,
    61,
    true,
    true
  )
on conflict (id) do update set
  workspace_id = excluded.workspace_id,
  platform_account_id = excluded.platform_account_id,
  platform = excluded.platform,
  external_content_id = excluded.external_content_id,
  title = excluded.title,
  description = excluded.description,
  status = excluded.status,
  published_at = excluded.published_at,
  duration_seconds = excluded.duration_seconds,
  content_type = excluded.content_type,
  topic_cluster_id = excluded.topic_cluster_id,
  raw_collection = excluded.raw_collection,
  raw_document_id = excluded.raw_document_id,
  views = excluded.views,
  likes = excluded.likes,
  comments = excluded.comments,
  saves = excluded.saves,
  shares = excluded.shares,
  completion_rate = excluded.completion_rate,
  followers_gained = excluded.followers_gained,
  score = excluded.score,
  has_asr = excluded.has_asr,
  reviewed = excluded.reviewed,
  updated_at = now();

insert into content_lifetime_metrics (
  content_id,
  play_count,
  like_count,
  comment_count,
  share_count,
  collect_count,
  follow_count,
  profile_visit_count,
  avg_view_duration,
  avg_view_percent,
  finish_rate,
  five_second_retention,
  bounce_rate,
  negative_feedback_count,
  metric_score,
  raw_document_id
)
values
  ('ct_inner_pg_001', 186400, 13820, 924, 1480, 6410, 1280, 8100, 34.8, 0.46, 0.46, 0.73, 0.21, 8, 94, 'raw_inner_douyin_001'),
  ('ct_inner_pg_002', 142900, 9060, 1120, 1210, 4920, 930, 6200, 29.2, 0.43, 0.43, 0.68, 0.24, 10, 90, 'raw_inner_douyin_002'),
  ('ct_inner_pg_003', 118600, 7340, 688, 910, 3820, 690, 4880, 23.8, 0.39, 0.39, 0.64, 0.28, 12, 86, 'raw_inner_douyin_003'),
  ('ct_inner_pg_004', 97300, 5210, 840, 620, 3500, 510, 3320, 25.9, 0.36, 0.36, 0.59, 0.31, 15, 80, 'raw_inner_douyin_004'),
  ('ct_inner_pg_005', 75600, 4120, 396, 540, 2780, 380, 2610, 27.4, 0.33, 0.33, 0.56, 0.34, 18, 76, 'raw_inner_douyin_005'),
  ('ct_inner_pg_006', 43800, 2100, 260, 300, 1560, 160, 1240, 21.1, 0.24, 0.24, 0.43, 0.42, 28, 61, 'raw_inner_douyin_006')
on conflict (content_id) do update set
  play_count = excluded.play_count,
  like_count = excluded.like_count,
  comment_count = excluded.comment_count,
  share_count = excluded.share_count,
  collect_count = excluded.collect_count,
  follow_count = excluded.follow_count,
  profile_visit_count = excluded.profile_visit_count,
  avg_view_duration = excluded.avg_view_duration,
  avg_view_percent = excluded.avg_view_percent,
  finish_rate = excluded.finish_rate,
  five_second_retention = excluded.five_second_retention,
  bounce_rate = excluded.bounce_rate,
  negative_feedback_count = excluded.negative_feedback_count,
  metric_score = excluded.metric_score,
  raw_document_id = excluded.raw_document_id,
  updated_at = now();

insert into content_text_assets (content_id, asset_type, text, language, segments, source)
values
  ('ct_inner_pg_001', 'asr', '我第一次接程序员副业私活，报价看起来赚了，最后亏在需求边界没有写清楚。今天只拆三个判断：客户是不是稳定、需求能不能验收、你的周末时间值多少钱。', 'zh-CN', '[]'::jsonb, 'inner_test_seed'),
  ('ct_inner_pg_002', 'asr', '程序员职业成长不要只问要不要跳槽，先把大厂、外包、独立产品三条路按现金流、学习密度和风险排序。', 'zh-CN', '[]'::jsonb, 'inner_test_seed'),
  ('ct_inner_pg_003', 'asr', 'AI 工具能省时间，但程序员不要先买课。你先把重复任务、代码审查和文档整理三个场景跑通，再决定要不要系统学习。', 'zh-CN', '[]'::jsonb, 'inner_test_seed'),
  ('ct_inner_pg_004', 'asr', '简历没有面试，不一定是项目少。很多程序员的问题是把职责写成流水账，没有写出业务结果和技术取舍。', 'zh-CN', '[]'::jsonb, 'inner_test_seed'),
  ('ct_inner_pg_005', 'asr', '独立产品不是先做一个完整系统。程序员变现前先验证谁会付费、为什么现在付、你能不能持续获客。', 'zh-CN', '[]'::jsonb, 'inner_test_seed'),
  ('ct_inner_pg_006', 'asr', '焦虑期不要把所有技术都学一遍。先列技能现金流表：现在能换钱的、三个月后能换机会的、只是让你感觉努力的。', 'zh-CN', '[]'::jsonb, 'inner_test_seed')
on conflict (content_id, asset_type, source) do update set
  text = excluded.text,
  language = excluded.language,
  segments = excluded.segments,
  updated_at = now();

insert into content_tags (content_id, tag, tag_type, source)
values
  ('ct_inner_pg_001', '程序员', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_001', '副业', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_001', '接私活', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_002', '程序员', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_002', '职业成长', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_002', '转型', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_003', 'AI', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_003', '程序员效率', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_004', '简历', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_004', '职业成长', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_005', '独立产品', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_005', '变现', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_006', '程序员', 'topic', 'inner_test_seed'),
  ('ct_inner_pg_006', '成长', 'topic', 'inner_test_seed')
on conflict (content_id, tag, source) do update set
  tag_type = excluded.tag_type,
  updated_at = now();

insert into content_keywords (content_id, keyword, keyword_type, score, query_count_7d, source)
values
  ('ct_inner_pg_001', '程序员副业', 'search', 0.96, 18000, 'inner_test_seed'),
  ('ct_inner_pg_001', '接私活报价', 'search', 0.91, 7200, 'inner_test_seed'),
  ('ct_inner_pg_002', '程序员职业成长', 'search', 0.95, 16800, 'inner_test_seed'),
  ('ct_inner_pg_002', '程序员转型', 'search', 0.86, 9300, 'inner_test_seed'),
  ('ct_inner_pg_003', 'AI 编程工具', 'search', 0.88, 15100, 'inner_test_seed'),
  ('ct_inner_pg_003', '程序员 AI', 'search', 0.84, 11600, 'inner_test_seed'),
  ('ct_inner_pg_004', '程序员简历', 'search', 0.9, 13200, 'inner_test_seed'),
  ('ct_inner_pg_004', '没有面试', 'search', 0.78, 6400, 'inner_test_seed'),
  ('ct_inner_pg_005', '独立产品变现', 'search', 0.83, 7600, 'inner_test_seed'),
  ('ct_inner_pg_005', '程序员变现', 'search', 0.82, 8200, 'inner_test_seed'),
  ('ct_inner_pg_006', '程序员焦虑', 'search', 0.76, 9800, 'inner_test_seed'),
  ('ct_inner_pg_006', '技能成长', 'search', 0.72, 5200, 'inner_test_seed')
on conflict (content_id, keyword, source) do update set
  keyword_type = excluded.keyword_type,
  score = excluded.score,
  query_count_7d = excluded.query_count_7d,
  updated_at = now();

insert into agent_memory_records (
  id,
  workspace_id,
  account_id,
  platform,
  memory_type,
  title,
  content,
  summary,
  metadata,
  source_type,
  source_ids,
  confidence,
  evidence_count,
  status,
  last_validated_at
)
values
  (
    'mem_inner_pg_001',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'success_pattern',
    '程序员职业成长内容的高表现结构',
    '高表现内容通常先给一个真实冲突场景，再给三条判断标准，最后落到评论区可追问的问题。程序员职业成长、程序员副业、接私活方向都适用。',
    '先用真实经历建立信任，再给可执行判断标准，完播和收藏更稳定。',
    '{"bestContentId":"ct_inner_pg_001","pattern":"case_then_criteria"}'::jsonb,
    'manual_seed',
    '["ct_inner_pg_001","ct_inner_pg_002"]'::jsonb,
    0.92,
    2,
    'active',
    '2026-05-10 10:00:00+08'
  ),
  (
    'mem_inner_pg_002',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'search_intent',
    '程序员职业成长的搜索承接词',
    '用户会搜索程序员职业成长、程序员副业、程序员转型、AI 编程工具、程序员简历。选题需要直接回答一个具体决策，而不是泛泛讲路线图。',
    '搜索意图集中在职业选择、副业变现、AI 工具效率和简历求职。',
    '{"keywords":["程序员职业成长","程序员副业","程序员简历","AI 编程工具"]}'::jsonb,
    'manual_seed',
    '["ct_inner_pg_002","ct_inner_pg_003","ct_inner_pg_004"]'::jsonb,
    0.88,
    3,
    'active',
    '2026-05-10 10:00:00+08'
  ),
  (
    'mem_inner_pg_003',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'failure_pattern',
    '程序员成长内容的低表现风险',
    '只讲焦虑、只喊长期主义、只列学习路线，容易让内容变成泛泛建议。需要补一个具体案例、数据指标或评论问题。',
    '避免抽象焦虑和空泛路线图，优先拍具体选择和真实复盘。',
    '{"avoid":["泛泛学习路线","焦虑标题","没有案例的建议"]}'::jsonb,
    'manual_seed',
    '["ct_inner_pg_006"]'::jsonb,
    0.81,
    1,
    'active',
    '2026-05-10 10:00:00+08'
  ),
  (
    'mem_inner_pg_004',
    'ws_northstar',
    'douyin_demo',
    'douyin',
    'persona_profile',
    '账号人设边界：程序员老陈',
    '账号语气偏理性复盘，不卖课，不制造裁员恐慌。适合用一线开发经历、报价表、简历片段、评论问题做素材。',
    '人设是理性、有经历、给判断标准的程序员内容策划。',
    '{"voice":"理性复盘","taboo":["卖课焦虑","裁员恐慌"]}'::jsonb,
    'manual_seed',
    '["ct_inner_pg_001"]'::jsonb,
    0.86,
    1,
    'active',
    '2026-05-10 10:00:00+08'
  )
on conflict (id) do update set
  workspace_id = excluded.workspace_id,
  account_id = excluded.account_id,
  platform = excluded.platform,
  memory_type = excluded.memory_type,
  title = excluded.title,
  content = excluded.content,
  summary = excluded.summary,
  metadata = excluded.metadata,
  source_type = excluded.source_type,
  source_ids = excluded.source_ids,
  confidence = excluded.confidence,
  evidence_count = excluded.evidence_count,
  status = excluded.status,
  last_validated_at = excluded.last_validated_at,
  updated_at = now();

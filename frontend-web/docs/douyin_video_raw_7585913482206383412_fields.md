# douyin_video_raw 字段说明：7585913482206383412

本文档基于 MongoDB `crawler_raw_db.douyin_video_raw` 中 `_id = "7585913482206383412"` 的实际文档生成，用来说明这条抖音作品原始数据中各字段的含义。

## 作品概览

- 作品 ID：`7585913482206383412`
- 标题：程序员可以干一辈子吗
- 发布时间：`1766233160`（2025-12-20 20:19:20）
- 视频时长：`60419` 毫秒，约 `60.42` 秒
- 播放量：`34599`；点赞：`132`；评论：`147`；收藏：`22`；分享：`19`
- 平均观看：`17.069455` 秒；完播率：`0.113454`；5 秒留存：`0.44837`

## 顶层模块

| 字段 | 含义 |
| --- | --- |
| `_id` | MongoDB 主键；这里直接使用抖音 aweme_id/视频 ID，便于按作品唯一定位。 |
| `base_info` | 业务侧整理出的基础信息摘要，适合列表页或详情页快速展示。 |
| `meta` | 采集与更新元数据，记录这条数据从哪里来、何时刷新过。 |
| `raw_list_data` | 抖音创作者后台列表接口返回的原始作品数据，字段最完整但也最平台化。 |
| `sec_uid` | 作者加密 UID，抖音公开接口常用的作者标识。 |
| `statistics` | 作品公开互动统计的整理版。 |
| `tags` | 从文案、话题和系统推荐中整理出的标签信息。 |
| `analysis` | 创作者后台分析数据，包括流量来源、搜索关键词、受众画像、偏好和评论热词。 |
| `creator_stats` | 创作者后台核心经营指标整理版，比公开 statistics 更偏运营分析。 |
| `play_info` | 播放地址相关信息整理版。 |

## 完整字段字典

| 字段路径 | 类型 | 示例/结构 | 字段含义 |
| --- | --- | --- | --- |
| `_id` | `str` | 7585913482206383412 | MongoDB 主键；这里直接使用抖音 aweme_id/视频 ID，便于按作品唯一定位。 |
| `base_info` | `object` | 8 个子字段 | 业务侧整理出的基础信息摘要，适合列表页或详情页快速展示。 |
| `base_info.title` | `str` | 程序员可以干一辈子吗 | 作品标题。 |
| `base_info.desc` | `str` | 程序员可以干一辈子吗 程序员能干一辈子吗？我觉得大部分普通人不行。 除非你是Top级的天选之子，否则我们都要面对被替代的那一天。  我是一个高中起点的野生程序员... | 作品完整文案/描述，通常包含标题、正文和话题。 |
| `base_info.create_time` | `int` | 1766233160 (2025-12-20 20:19:20) | 作品发布时间，Unix 秒级时间戳。 |
| `base_info.duration` | `int` | 60419 | 视频时长，毫秒。 |
| `base_info.cover` | `str` | https://p26-sign.douyinpic.com/tos-cn-i-dy/8fd80607a4b8481e93e96a083cdd9d5e~tplv... | 封面图 URL。 |
| `base_info.video_url` | `str` | https://creator.douyin.com/aweme/v1/play/?video_id=v0300fg10000d5397ofog65o589s6... | 视频播放地址 URL。 |
| `base_info.music_title` | `str` | @纯野生程序员老韩创作的原声 | 作品使用的音乐/原声标题。 |
| `base_info.ratio` | `str` | 720p | 视频清晰度或码率档位标识，例如 720p。 |
| `meta` | `object` | 12 个子字段 | 采集与更新元数据，记录这条数据从哪里来、何时刷新过。 |
| `meta.last_list_update` | `datetime` | 2026-03-18 01:03:16.143000 | 作品列表数据最近一次更新时间。 |
| `meta.task_id` | `str` | UPLOAD_VIDEOS_20260318_090316 | 采集任务 ID。 |
| `meta.trace_id` | `str` | 579bd1d0-51d5-4cac-ad66-8d235b1b153a | 本次采集链路追踪 ID，用于排查任务。 |
| `meta.source_url` | `str` | https://creator.douyin.com/janus/douyin/creator/pc/work_list?status=1&count=20&m... | 采集来源页面 URL。 |
| `meta.last_traffic_update` | `datetime` | 2026-03-18 01:05:58.960000 | 流量来源数据最近一次更新时间。 |
| `meta.data_source` | `str` | web_creator | 数据来源渠道，例如 web_creator 表示创作者后台网页。 |
| `meta.internal_stat_id` | `str` | 7585913482206383000 | 内部统计 ID；可能因大整数精度被存成近似尾数。 |
| `meta.last_detail_update` | `datetime` | 2026-03-18 01:07:06.178000 | 详情数据最近一次更新时间。 |
| `meta.last_keywords_update` | `datetime` | 2026-03-18 01:08:27.553000 | 搜索关键词数据最近一次更新时间。 |
| `meta.last_portrait_update` | `datetime` | 2026-03-18 01:09:40.047000 | 受众画像数据最近一次更新时间。 |
| `meta.last_other_update` | `datetime` | 2026-03-18 01:10:57.595000 | 其他分析数据最近一次更新时间。 |
| `meta.last_word_cloud_update` | `datetime` | 2026-03-18 01:27:39.851000 | 评论词云数据最近一次更新时间。 |
| `raw_list_data` | `object` | 59 个子字段 | 抖音创作者后台列表接口返回的原始作品数据，字段最完整但也最平台化。 |
| `raw_list_data.Cover` | `object` | 4 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.Cover.height` | `int` | 720 | 资源高度，单位像素。 |
| `raw_list_data.Cover.uri` | `str` | tos-cn-i-dy/8fd80607a4b8481e93e96a083cdd9d5e | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.Cover.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.Cover.width` | `int` | 540 | 资源宽度，单位像素。 |
| `raw_list_data.author` | `object` | 42 个子字段 | 作者对象或音乐作者名，含义取决于所在模块。 |
| `raw_list_data.author.avatar_larger` | `object` | 2 个子字段 | 大尺寸头像对象。 |
| `raw_list_data.author.avatar_larger.uri` | `str` | 1080x1080/aweme-avatar/tos-cn-avt-0015_8ad3a920561558f6e0f501a69de8696f | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.author.avatar_larger.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.author.avatar_medium` | `object` | 2 个子字段 | 中尺寸头像对象。 |
| `raw_list_data.author.avatar_medium.uri` | `str` | 720x720/aweme-avatar/tos-cn-avt-0015_8ad3a920561558f6e0f501a69de8696f | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.author.avatar_medium.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.author.avatar_thumb` | `object` | 2 个子字段 | 小尺寸头像对象。 |
| `raw_list_data.author.avatar_thumb.uri` | `str` | 100x100/aweme-avatar/tos-cn-avt-0015_8ad3a920561558f6e0f501a69de8696f | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.author.avatar_thumb.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.author.aweme_count` | `int` | 43 | 作者公开视频数量。 |
| `raw_list_data.author.birthday` | `str` | *** | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.card_entries` | `null` | None | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.custom_verify` | `str` |  | 自定义认证文案。 |
| `raw_list_data.author.enterprise_verify_reason` | `str` |  | 企业认证原因/说明。 |
| `raw_list_data.author.favoriting_count` | `int` | 49 | 作者喜欢/收藏数量。 |
| `raw_list_data.author.follow_status` | `int` | 0 | 当前账号对作者的关注状态编码。 |
| `raw_list_data.author.follower_count` | `int` | 1009 | 粉丝数。 |
| `raw_list_data.author.follower_status` | `int` | 0 | 作者对当前账号的关注关系编码。 |
| `raw_list_data.author.followers_detail` | `null` | None | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.following_count` | `int` | 12 | 关注数。 |
| `raw_list_data.author.geofencing` | `null` | None | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.has_orders` | `bool` | False | 作者是否有订单相关能力/记录。 |
| `raw_list_data.author.is_ad_fake` | `bool` | False | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.is_enterprise_vip` | `bool` | True | 是否企业认证账号。 |
| `raw_list_data.author.is_gov_media_vip` | `bool` | False | 是否政务/媒体认证。 |
| `raw_list_data.author.mix_info` | `null` | None | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.nickname` | `str` | 纯野生程序员老韩 | 作者昵称。 |
| `raw_list_data.author.original_musician` | `object` | 2 个子字段 | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.original_musician.music_count` | `int` | 0 | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.original_musician.music_used_count` | `int` | 0 | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.platform_sync_info` | `null` | None | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.policy_version` | `null` | None | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.rate` | `int` | 1 | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.region` | `str` | CN | 作者地区。 |
| `raw_list_data.author.sec_uid` | `str` | MS4wLjABAAAAecPgbxHjmy-XcTMGPTqFu-9jdBlpGRfREjVVfxceUSx22PbSOfI3rrjFO8mxKOnF | 作者加密 UID。 |
| `raw_list_data.author.secret` | `int` | 0 | 作者账号私密状态编码。 |
| `raw_list_data.author.short_id` | `str` | 72588020832 | 作者短 ID。 |
| `raw_list_data.author.signature` | `str` | 👨‍💻 15年纯野生代码老兵｜高中学历｜农村土著 🌽 现状： 没大厂光环，被裁5年，自由职业者五年. 🤖 正在做的事： 边啃玉米，边用AI寻找普通人的出路。 | 作者个人简介。 |
| `raw_list_data.author.status` | `int` | 1 | 状态编码或状态对象，含义取决于所在模块。 |
| `raw_list_data.author.story_open` | `bool` | False | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.total_favorited` | `str` | 2655 | 作者累计获赞数。 |
| `raw_list_data.author.type_label` | `array` | 0 项 | 作者资料字段，来自抖音原始列表接口。 |
| `raw_list_data.author.uid` | `str` | 7506093641015231545 | 作者 UID。 |
| `raw_list_data.author.unique_id` | `str` | 72588020832 | 作者抖音号/唯一 ID。 |
| `raw_list_data.author.user_canceled` | `bool` | False | 作者账号是否已注销。 |
| `raw_list_data.author.verification_type` | `int` | 1 | 认证类型编码。 |
| `raw_list_data.author.video_icon` | `object` | 2 个子字段 | 作者视频图标资源对象。 |
| `raw_list_data.author.video_icon.uri` | `str` |  | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.author.video_icon.url_list` | `array` | 0 项 | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.author.with_commerce_entry` | `bool` | False | 是否展示商业化入口。 |
| `raw_list_data.author.with_fusion_shop_entry` | `bool` | True | 是否展示融合店铺入口。 |
| `raw_list_data.author.with_shop_entry` | `bool` | False | 是否展示店铺入口。 |
| `raw_list_data.author_user_id` | `int` | 7506093641015231000 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.aweme_id` | `str` | 7585913482206383412 | 抖音作品 ID。 |
| `raw_list_data.aweme_type` | `int` | 4 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.caption` | `str` | 程序员能干一辈子吗？我觉得大部分普通人不行。 除非你是Top级的天选之子，否则我们都要面对被替代的那一天。  我是一个高中起点的野生程序员。为了对抗这种危机感，... | 作品正文文案，通常是不含部分平台拼接信息的正文。 |
| `raw_list_data.cha_list` | `array` | 1 项；首项类型 object | 作品关联的话题列表。 |
| `raw_list_data.cha_list[]` | `object` | 10 个子字段 | 作品关联的话题列表。 |
| `raw_list_data.cha_list[].cha_name` | `str` | 大龄程序员 | 话题名称。 |
| `raw_list_data.cha_list[].cid` | `str` | 1627546827474948 | 话题 ID。 |
| `raw_list_data.cha_list[].connect_music` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.cha_list[].cover_item` | `object` | 2 个子字段 | 话题封面资源。 |
| `raw_list_data.cha_list[].cover_item.uri` | `str` | image-cut-tos/3a217d941799e6ecf7ca482974ffc068.jpg | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.cha_list[].cover_item.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.cha_list[].desc` | `str` |  | 描述文本/文案。 |
| `raw_list_data.cha_list[].hash_tag_profile` | `str` | image-cut-tos/3a217d941799e6ecf7ca482974ffc068.jpg | 话题头像/封面资源标识。 |
| `raw_list_data.cha_list[].is_commerce` | `bool` | False | 话题是否商业化。 |
| `raw_list_data.cha_list[].type` | `int` | 1 | 平台枚举类型；在话题结构中 type=1 通常表示 hashtag。 |
| `raw_list_data.cha_list[].user_count` | `int` | 0 | 话题使用人数或音乐使用人数。 |
| `raw_list_data.cha_list[].view_count` | `int` | 0 | 话题播放/浏览量。 |
| `raw_list_data.chapter_bar_color` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.chapter_list` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.comment_list` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.common_labels` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.create_time` | `int` | 1766233160 (2025-12-20 20:19:20) | 发布时间，Unix 秒级时间戳。 |
| `raw_list_data.creator_item_setting` | `object` | 1 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.creator_item_setting.charge_comment_audit` | `bool` | False | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.danmaku_control` | `object` | 7 个子字段 | 弹幕能力控制。 |
| `raw_list_data.danmaku_control.activities` | `array` | 1 项；首项类型 object | 弹幕相关活动配置列表。 |
| `raw_list_data.danmaku_control.activities[]` | `object` | 2 个子字段 | 弹幕相关活动配置列表。 |
| `raw_list_data.danmaku_control.activities[].Id` | `int` | 1224 | 活动 ID。 |
| `raw_list_data.danmaku_control.activities[].Type` | `int` | 1 | 活动类型编码。 |
| `raw_list_data.danmaku_control.danmaku_cnt` | `int` | 0 | 弹幕数量。 |
| `raw_list_data.danmaku_control.enable_danmaku` | `bool` | True | 是否启用弹幕。 |
| `raw_list_data.danmaku_control.is_post_denied` | `bool` | False | 是否禁止发布弹幕。 |
| `raw_list_data.danmaku_control.post_denied_reason` | `str` |  | 禁止发布弹幕原因。 |
| `raw_list_data.danmaku_control.post_privilege_level` | `int` | 0 | 发布弹幕所需权限等级。 |
| `raw_list_data.danmaku_control.skip_danmaku` | `bool` | False | 是否跳过/不展示弹幕。 |
| `raw_list_data.desc` | `str` | 程序员可以干一辈子吗 程序员能干一辈子吗？我觉得大部分普通人不行。 除非你是Top级的天选之子，否则我们都要面对被替代的那一天。  我是一个高中起点的野生程序员... | 描述文本/文案。 |
| `raw_list_data.duration` | `int` | 60419 | 时长；视频字段多为毫秒，音乐字段多为秒。 |
| `raw_list_data.extra` | `str` | {"item_can_admire":0} | 平台额外 JSON 字符串，需二次解析。 |
| `raw_list_data.forward_id` | `str` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.geofencing` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.group_id` | `int` | 7585913482206383000 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.horizontal_cover` | `object` | 4 个子字段 | 横版封面资源。 |
| `raw_list_data.horizontal_cover.height` | `int` | 539 | 资源高度，单位像素。 |
| `raw_list_data.horizontal_cover.uri` | `str` | tos-cn-i-dy/5959b88a20c4443c940b68b4ff547a9d | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.horizontal_cover.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.horizontal_cover.width` | `int` | 720 | 资源宽度，单位像素。 |
| `raw_list_data.horizontal_cover_tsp` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.image_infos` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.images` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.img_bitrate` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.interaction_stickers` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_charge_series` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_live_replay` | `bool` | False | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_pic_word` | `bool` | False | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_pinned` | `bool` | True | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_preview` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_reward` | `bool` | False | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_slides` | `bool` | False | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.is_story` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.item_id` | `int` | 7585913482206383000 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.item_title` | `str` | 程序员可以干一辈子吗 | 作品标题。 |
| `raw_list_data.label_top_text` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.long_video` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.misc_info` | `str` | {"common_business_mob":"{}","is_teen_video":0} | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.music` | `object` | 25 个子字段 | 作品使用的音乐/原声信息。 |
| `raw_list_data.music.album` | `str` |  | 音乐专辑名。 |
| `raw_list_data.music.author` | `str` | 纯野生程序员老韩 | 作者对象或音乐作者名，含义取决于所在模块。 |
| `raw_list_data.music.collect_stat` | `int` | 0 | 音乐收藏状态/数量编码。 |
| `raw_list_data.music.cover_hd` | `object` | 2 个子字段 | 高清音乐封面。 |
| `raw_list_data.music.cover_hd.uri` | `str` | 1080x1080/aweme-avatar/tos-cn-avt-0015_8ad3a920561558f6e0f501a69de8696f | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.music.cover_hd.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.music.cover_large` | `object` | 2 个子字段 | 大尺寸音乐封面。 |
| `raw_list_data.music.cover_large.uri` | `str` | 1080x1080/aweme-avatar/tos-cn-avt-0015_8ad3a920561558f6e0f501a69de8696f | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.music.cover_large.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.music.cover_medium` | `object` | 2 个子字段 | 中尺寸音乐封面。 |
| `raw_list_data.music.cover_medium.uri` | `str` | 720x720/aweme-avatar/tos-cn-avt-0015_8ad3a920561558f6e0f501a69de8696f | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.music.cover_medium.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.music.cover_thumb` | `object` | 2 个子字段 | 小尺寸音乐封面。 |
| `raw_list_data.music.cover_thumb.uri` | `str` | 168x168/aweme-avatar/tos-cn-avt-0015_8ad3a920561558f6e0f501a69de8696f | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.music.cover_thumb.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.music.duration` | `int` | 60 | 时长；视频字段多为毫秒，音乐字段多为秒。 |
| `raw_list_data.music.end_time` | `int` | 0 | 音乐使用片段结束时间。 |
| `raw_list_data.music.extra` | `str` | {"aed_singing_score":0.01,"aggregate_exempt_conf":[],"beats":{},"cover_colors":n... | 平台额外 JSON 字符串，需二次解析。 |
| `raw_list_data.music.id` | `int` | 7585913551324335000 | 平台内部 ID。 |
| `raw_list_data.music.id_str` | `str` | 7585913551324334889 | 字符串形式 ID，避免大整数精度损失。 |
| `raw_list_data.music.is_original` | `bool` | False | 是否原创音乐/原声。 |
| `raw_list_data.music.is_pgc` | `bool` | False | 是否 PGC 音乐。 |
| `raw_list_data.music.mid` | `str` | 7585913551324334889 | 音乐 ID。 |
| `raw_list_data.music.offline_desc` | `str` |  | 音乐下线说明。 |
| `raw_list_data.music.owner_nickname` | `str` | 纯野生程序员老韩 | 音乐归属作者昵称。 |
| `raw_list_data.music.play_url` | `object` | 2 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.music.play_url.uri` | `str` | https://sf5-hl-ali-cdn-tos.douyinstatic.com/obj/ies-music/7585913664847514374.mp... | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.music.play_url.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.music.position` | `null` | None | 音乐片段位置数据。 |
| `raw_list_data.music.schema_url` | `str` |  | 平台内跳转 schema。 |
| `raw_list_data.music.source_platform` | `int` | 23 | 音乐来源平台编码。 |
| `raw_list_data.music.start_time` | `int` | 0 | 音乐使用片段开始时间。 |
| `raw_list_data.music.status` | `int` | 1 | 状态编码或状态对象，含义取决于所在模块。 |
| `raw_list_data.music.title` | `str` | @纯野生程序员老韩创作的原声 | 标题。 |
| `raw_list_data.music.user_count` | `int` | 0 | 话题使用人数或音乐使用人数。 |
| `raw_list_data.next_info` | `object` | 5 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.next_info.caption` | `str` | 程序员能干一辈子吗？我觉得大部分普通人不行。 除非你是Top级的天选之子，否则我们都要面对被替代的那一天。  我是一个高中起点的野生程序员。为了对抗这种危机感，... | 作品正文文案，通常是不含部分平台拼接信息的正文。 |
| `raw_list_data.next_info.desc` | `str` | 程序员可以干一辈子吗 程序员能干一辈子吗？我觉得大部分普通人不行。 除非你是Top级的天选之子，否则我们都要面对被替代的那一天。  我是一个高中起点的野生程序员... | 描述文本/文案。 |
| `raw_list_data.next_info.item_title` | `str` | 程序员可以干一辈子吗 | 作品标题。 |
| `raw_list_data.next_info.status` | `int` | -1 | 状态编码或状态对象，含义取决于所在模块。 |
| `raw_list_data.next_info.text_extra` | `array` | 4 项；首项类型 object | 文案中的结构化元素列表，例如话题、@ 用户等，并给出位置。 |
| `raw_list_data.next_info.text_extra[]` | `object` | 7 个子字段 | 文案中的结构化元素列表，例如话题、@ 用户等，并给出位置。 |
| `raw_list_data.next_info.text_extra[].caption_end` | `int` | 140 | 该元素在 caption 文本中的结束位置。 |
| `raw_list_data.next_info.text_extra[].caption_start` | `int` | 136 | 该元素在 caption 文本中的起始位置。 |
| `raw_list_data.next_info.text_extra[].end` | `int` | 151 | 该元素在 desc 文本中的结束位置。 |
| `raw_list_data.next_info.text_extra[].hashtag_id` | `int` | 1577677564319758 | 话题 ID。 |
| `raw_list_data.next_info.text_extra[].hashtag_name` | `str` | 程序员 | 话题名称。 |
| `raw_list_data.next_info.text_extra[].start` | `int` | 147 | 该元素在 desc 文本中的起始位置。 |
| `raw_list_data.next_info.text_extra[].type` | `int` | 1 | 平台枚举类型；在话题结构中 type=1 通常表示 hashtag。 |
| `raw_list_data.promotions` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.rate` | `int` | 12 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.recommend_chapter_info` | `object` | 5 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.recommend_chapter_info.chapter_abstract` | `str` |  | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.recommend_chapter_info.chapter_bar_color` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.recommend_chapter_info.chapter_recommend_source` | `int` | 2 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.recommend_chapter_info.push_scene` | `array` | 0 项 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.recommend_chapter_info.recommend_chapter_list` | `array` | 0 项 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.risk_infos` | `object` | 3 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.risk_infos.content` | `str` |  | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.risk_infos.type` | `int` | 0 | 平台枚举类型；在话题结构中 type=1 通常表示 hashtag。 |
| `raw_list_data.risk_infos.warn` | `bool` | False | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.series_paid_info` | `object` | 2 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.series_paid_info.item_price` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.series_paid_info.series_paid_tatus` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.share_info` | `object` | 4 个子字段 | 分享文案与分享链接相关信息。 |
| `raw_list_data.share_info.share_desc` | `str` | 在抖音，记录美好生活 | 分享描述。 |
| `raw_list_data.share_info.share_link_desc` | `str` | 7.43 03/10 k@c.AT anD:/ 复制打开抖音，看看【纯野生程序员老韩的作品】程序员可以干一辈子吗 程序员能干一辈子吗？我觉得大... %s | 复制口令分享文案。 |
| `raw_list_data.share_info.share_title` | `str` | 程序员可以干一辈子吗 程序员能干一辈子吗？我觉得大部分普通人不行。 除非你是Top级的天选之子，否则我们都要面对被替代的那一天。  我是一个高中起点的野生程序员... | 分享标题。 |
| `raw_list_data.share_info.share_weibo_desc` | `str` | #在抖音，记录美好生活#程序员可以干一辈子吗 程序员能干一辈子吗？我觉得大部分普通人不行。 除非你是Top级的天选之子，否则我们都要面对被替代的那一天。  我是... | 微博分享文案。 |
| `raw_list_data.share_url` | `str` | https://www.iesdouyin.com/share/video/7585913482206383412/?region=&mid=758591355... | 作品分享 URL。 |
| `raw_list_data.statistics` | `object` | 8 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.statistics.aweme_id` | `str` | 7585913482206383412 | 抖音作品 ID。 |
| `raw_list_data.statistics.collect_count` | `int` | 22 | 收藏数。 |
| `raw_list_data.statistics.comment_count` | `int` | 147 | 评论数。 |
| `raw_list_data.statistics.digg_count` | `int` | 132 | 点赞数。 |
| `raw_list_data.statistics.forward_count` | `int` | 0 | 转发数。 |
| `raw_list_data.statistics.live_watch_count` | `int` | 0 | 直播观看数；短视频通常为 0。 |
| `raw_list_data.statistics.play_count` | `int` | 34599 | 播放量。 |
| `raw_list_data.statistics.share_count` | `int` | 19 | 分享数。 |
| `raw_list_data.status` | `object` | 12 个子字段 | 状态编码或状态对象，含义取决于所在模块。 |
| `raw_list_data.status.allow_comment` | `bool` | True | 是否允许评论。 |
| `raw_list_data.status.allow_share` | `bool` | True | 是否允许分享。 |
| `raw_list_data.status.aweme_id` | `str` | 7585913482206383412 | 抖音作品 ID。 |
| `raw_list_data.status.in_reviewing` | `bool` | False | 是否审核中。 |
| `raw_list_data.status.is_delete` | `bool` | False | 是否已删除。 |
| `raw_list_data.status.is_private` | `bool` | False | 是否私密作品。 |
| `raw_list_data.status.is_prohibited` | `bool` | False | 是否被平台禁止展示/限制。 |
| `raw_list_data.status.private_status` | `int` | 0 | 私密状态编码。 |
| `raw_list_data.status.reviewed` | `bool` | False | 是否已审核完成。 |
| `raw_list_data.status.self_see` | `bool` | False | 是否仅自己可见。 |
| `raw_list_data.status.with_fusion_goods` | `bool` | False | 是否挂载融合商品。 |
| `raw_list_data.status.with_goods` | `bool` | False | 是否挂载商品。 |
| `raw_list_data.status_value` | `int` | 102 | 作品状态编码。 |
| `raw_list_data.sync_struct` | `object` | 2 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.sync_struct.canSync` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.sync_struct.reason` | `int` | 1 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.text_extra` | `array` | 4 项；首项类型 object | 文案中的结构化元素列表，例如话题、@ 用户等，并给出位置。 |
| `raw_list_data.text_extra[]` | `object` | 7 个子字段 | 文案中的结构化元素列表，例如话题、@ 用户等，并给出位置。 |
| `raw_list_data.text_extra[].caption_end` | `int` | 140 | 该元素在 caption 文本中的结束位置。 |
| `raw_list_data.text_extra[].caption_start` | `int` | 136 | 该元素在 caption 文本中的起始位置。 |
| `raw_list_data.text_extra[].end` | `int` | 151 | 该元素在 desc 文本中的结束位置。 |
| `raw_list_data.text_extra[].hashtag_id` | `int` | 1577677564319758 | 话题 ID。 |
| `raw_list_data.text_extra[].hashtag_name` | `str` | 程序员 | 话题名称。 |
| `raw_list_data.text_extra[].start` | `int` | 147 | 该元素在 desc 文本中的起始位置。 |
| `raw_list_data.text_extra[].type` | `int` | 1 | 平台枚举类型；在话题结构中 type=1 通常表示 hashtag。 |
| `raw_list_data.type` | `int` | 0 | 平台枚举类型；在话题结构中 type=1 通常表示 hashtag。 |
| `raw_list_data.video` | `object` | 14 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.video.big_thumbs` | `array` | 1 项；首项类型 object | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[]` | `object` | 12 个子字段 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].duration` | `float` | 60.4 | 时长；视频字段多为毫秒，音乐字段多为秒。 |
| `raw_list_data.video.big_thumbs[].fext` | `str` | jpg | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].img_num` | `int` | 60 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].img_url` | `str` | https://p11-sign.douyinpic.com/tos-cn-p-0015/ooKCfJG6L9IDGKNZB2foAEGDqgeQQMKeAlk... | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].img_urls` | `array` | 0 项 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].img_x_len` | `int` | 10 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].img_x_size` | `int` | 136 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].img_y_len` | `int` | 6 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].img_y_size` | `int` | 240 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].interval` | `int` | 1 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.big_thumbs[].uri` | `str` | tos-cn-p-0015/ooKCfJG6L9IDGKNZB2foAEGDqgeQQMKeAlkEyI | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.video.big_thumbs[].uris` | `array` | 0 项 | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.bit_rate` | `null` | None | 视频资源字段，描述播放、封面、分辨率和缩略图。 |
| `raw_list_data.video.cover` | `object` | 2 个子字段 | 封面资源对象或封面地址。 |
| `raw_list_data.video.cover.uri` | `str` | tos-cn-i-dy/8fd80607a4b8481e93e96a083cdd9d5e | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.video.cover.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.video.download_addr` | `object` | 2 个子字段 | 下载地址对象。 |
| `raw_list_data.video.download_addr.uri` | `str` | v0300fg10000d5397ofog65o589s64a0 | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.video.download_addr.url_list` | `array` | 1 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.video.duration` | `int` | 60419 | 时长；视频字段多为毫秒，音乐字段多为秒。 |
| `raw_list_data.video.dynamic_cover` | `object` | 2 个子字段 | 动态封面资源。 |
| `raw_list_data.video.dynamic_cover.uri` | `str` | tos-cn-i-dy/8fd80607a4b8481e93e96a083cdd9d5e | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.video.dynamic_cover.url_list` | `array` | 2 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.video.has_watermark` | `bool` | True | 视频资源是否带水印。 |
| `raw_list_data.video.height` | `int` | 1920 | 资源高度，单位像素。 |
| `raw_list_data.video.origin_cover` | `object` | 2 个子字段 | 原始封面资源。 |
| `raw_list_data.video.origin_cover.uri` | `str` | tos-cn-p-0015/osUe4oiBPGKnrGDEAhnwlugIBfA8iABEDBr00I | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.video.origin_cover.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.video.play_addr` | `object` | 2 个子字段 | 播放地址对象。 |
| `raw_list_data.video.play_addr.uri` | `str` | v0300fg10000d5397ofog65o589s64a0 | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.video.play_addr.url_list` | `array` | 1 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.video.play_addr_lowbr` | `object` | 2 个子字段 | 低码率播放地址对象。 |
| `raw_list_data.video.play_addr_lowbr.uri` | `str` | v0300fg10000d5397ofog65o589s64a0 | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `raw_list_data.video.play_addr_lowbr.url_list` | `array` | 1 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `raw_list_data.video.ratio` | `str` | 720p | 视频清晰度/规格标识。 |
| `raw_list_data.video.vid` | `str` | v0300fg10000d5397ofog65o589s64a0 | 视频资源 ID。 |
| `raw_list_data.video.width` | `int` | 1080 | 资源宽度，单位像素。 |
| `raw_list_data.video_control` | `object` | 7 个子字段 | 视频交互权限控制。 |
| `raw_list_data.video_control.allow_download` | `bool` | True | 是否允许下载。 |
| `raw_list_data.video_control.allow_duet` | `bool` | True | 是否允许合拍。 |
| `raw_list_data.video_control.allow_react` | `bool` | True | 是否允许抢镜/反应。 |
| `raw_list_data.video_control.draft_progress_bar` | `int` | 1 | 草稿/发布侧进度条显示配置。 |
| `raw_list_data.video_control.prevent_download_type` | `int` | 0 | 下载限制类型编码。 |
| `raw_list_data.video_control.share_type` | `int` | 1 | 分享权限类型编码。 |
| `raw_list_data.video_control.show_progress_bar` | `int` | 1 | 是否展示播放进度条。 |
| `raw_list_data.video_labels` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.video_text` | `null` | None | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.xigua_base_info` | `object` | 4 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.xigua_base_info.item_id` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.xigua_base_info.star_altar_order_id` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.xigua_base_info.star_altar_type` | `int` | 0 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `raw_list_data.xigua_base_info.status` | `int` | 0 | 状态编码或状态对象，含义取决于所在模块。 |
| `sec_uid` | `str` | MS4wLjABAAAAecPgbxHjmy-XcTMGPTqFu-9jdBlpGRfREjVVfxceUSx22PbSOfI3rrjFO8mxKOnF | 作者加密 UID，抖音公开接口常用的作者标识。 |
| `statistics` | `object` | 8 个子字段 | 作品公开互动统计的整理版。 |
| `statistics.aweme_id` | `str` | 7585913482206383412 | 抖音作品 ID。 |
| `statistics.collect_count` | `int` | 22 | 收藏数。 |
| `statistics.comment_count` | `int` | 147 | 评论数。 |
| `statistics.digg_count` | `int` | 132 | 点赞数。 |
| `statistics.forward_count` | `int` | 0 | 转发数。 |
| `statistics.live_watch_count` | `int` | 0 | 直播观看数；短视频通常为 0。 |
| `statistics.play_count` | `int` | 34599 | 播放量。 |
| `statistics.share_count` | `int` | 19 | 分享数。 |
| `tags` | `object` | 3 个子字段 | 从文案、话题和系统推荐中整理出的标签信息。 |
| `tags.user_hashtags` | `array` | 4 项；首项类型 str | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `tags.system_recommend` | `array` | 4 项；首项类型 object | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `tags.system_recommend[]` | `object` | 7 个子字段 | 数组中的单个元素结构。 |
| `tags.system_recommend[].caption_end` | `int` | 140 | 该元素在 caption 文本中的结束位置。 |
| `tags.system_recommend[].caption_start` | `int` | 136 | 该元素在 caption 文本中的起始位置。 |
| `tags.system_recommend[].end` | `int` | 151 | 该元素在 desc 文本中的结束位置。 |
| `tags.system_recommend[].hashtag_id` | `int` | 1577677564319758 | 话题 ID。 |
| `tags.system_recommend[].hashtag_name` | `str` | 程序员 | 话题名称。 |
| `tags.system_recommend[].start` | `int` | 147 | 该元素在 desc 文本中的起始位置。 |
| `tags.system_recommend[].type` | `int` | 1 | 平台枚举类型；在话题结构中 type=1 通常表示 hashtag。 |
| `tags.challenges` | `array` | 1 项；首项类型 str | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `analysis` | `object` | 5 个子字段 | 创作者后台分析数据，包括流量来源、搜索关键词、受众画像、偏好和评论热词。 |
| `analysis.traffic_source` | `object` | 1 个子字段 | 流量来源分析。 |
| `analysis.traffic_source.play_source` | `array` | 9 项；首项类型 object | 播放来源占比列表。 |
| `analysis.traffic_source.play_source[]` | `object` | 4 个子字段 | 播放来源占比列表。 |
| `analysis.traffic_source.play_source[].app_id` | `int` | 1128 | 来源所属应用 ID。 |
| `analysis.traffic_source.play_source[].history_difference` | `float` | 8.49762066621346e-05 | 与历史周期相比的差异值。 |
| `analysis.traffic_source.play_source[].key` | `str` | familiar | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.traffic_source.play_source[].value` | `float` | 8.49762066621346e-05 | 对应指标值，通常为比例或指数。 |
| `analysis.search_keywords` | `object` | 2 个子字段 | 搜索关键词分析。 |
| `analysis.search_keywords.inspire_search` | `array` | 7 项；首项类型 object | 可用于选题启发的搜索词及占比。 |
| `analysis.search_keywords.inspire_search[]` | `object` | 2 个子字段 | 可用于选题启发的搜索词及占比。 |
| `analysis.search_keywords.inspire_search[].keyword` | `str` | 程序员三条职业发展路线 | 关键词。 |
| `analysis.search_keywords.inspire_search[].percent` | `float` | 0.254 | 占比，通常 0-1。 |
| `analysis.search_keywords.show_from` | `array` | 5 项；首项类型 object | 实际带来展示/搜索曝光的关键词及占比。 |
| `analysis.search_keywords.show_from[]` | `object` | 2 个子字段 | 实际带来展示/搜索曝光的关键词及占比。 |
| `analysis.search_keywords.show_from[].keyword` | `str` | 程序员 | 关键词。 |
| `analysis.search_keywords.show_from[].percent` | `float` | 0.834 | 占比，通常 0-1。 |
| `analysis.audience_profile` | `object` | 7 个子字段 | 观看人群画像。 |
| `analysis.audience_profile.active` | `array` | 5 项；首项类型 object | 用户活跃度分布。 |
| `analysis.audience_profile.active[]` | `object` | 2 个子字段 | 用户活跃度分布。 |
| `analysis.audience_profile.active[].key` | `str` | 3 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.active[].value` | `float` | 0.07871448532836516 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.age` | `object` | 2 个子字段 | 年龄分布与 TGI。 |
| `analysis.audience_profile.age.ratio_list` | `array` | 6 项；首项类型 object | 占比分布列表。 |
| `analysis.audience_profile.age.ratio_list[]` | `object` | 2 个子字段 | 占比分布列表。 |
| `analysis.audience_profile.age.ratio_list[].key` | `str` | 50- | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.age.ratio_list[].value` | `float` | 0.03838705647176412 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.age.tgi_list` | `array` | 6 项；首项类型 object | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.age.tgi_list[]` | `object` | 2 个子字段 | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.age.tgi_list[].key` | `str` | 50- | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.age.tgi_list[].value` | `float` | 24.69269292264812 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.career` | `array` | 17 项；首项类型 object | 职业分布。 |
| `analysis.audience_profile.career[]` | `object` | 2 个子字段 | 职业分布。 |
| `analysis.audience_profile.career[].key` | `str` | restaurant | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.career[].value` | `float` | 0.01319129457783696 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.city_level` | `object` | 2 个子字段 | 城市线级分布。 |
| `analysis.audience_profile.city_level.ratio_list` | `array` | 8 项；首项类型 object | 占比分布列表。 |
| `analysis.audience_profile.city_level.ratio_list[]` | `object` | 2 个子字段 | 占比分布列表。 |
| `analysis.audience_profile.city_level.ratio_list[].key` | `str` | 三线 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.city_level.ratio_list[].value` | `float` | 0.08337780568199654 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.city_level.tgi_list` | `array` | 8 项；首项类型 object | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.city_level.tgi_list[]` | `object` | 2 个子字段 | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.city_level.tgi_list[].key` | `str` | 三线 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.city_level.tgi_list[].value` | `float` | 32.76047055694264 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.gender` | `object` | 2 个子字段 | 性别分布。 |
| `analysis.audience_profile.gender.ratio_list` | `array` | 2 项；首项类型 object | 占比分布列表。 |
| `analysis.audience_profile.gender.ratio_list[]` | `object` | 2 个子字段 | 占比分布列表。 |
| `analysis.audience_profile.gender.ratio_list[].key` | `str` | female | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.gender.ratio_list[].value` | `float` | 0.1294617740826405 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.gender.tgi_list` | `array` | 2 项；首项类型 object | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.gender.tgi_list[]` | `object` | 2 个子字段 | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.gender.tgi_list[].key` | `str` | female | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.gender.tgi_list[].value` | `float` | 29.292330354313812 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.new_user` | `array` | 2 项；首项类型 object | 新老用户分布。 |
| `analysis.audience_profile.new_user[]` | `object` | 2 个子字段 | 新老用户分布。 |
| `analysis.audience_profile.new_user[].key` | `str` | 老用户 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.new_user[].value` | `float` | 0.9970501474926253 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.province` | `object` | 2 个子字段 | 省份分布。 |
| `analysis.audience_profile.province.ratio_list` | `array` | 34 项；首项类型 object | 占比分布列表。 |
| `analysis.audience_profile.province.ratio_list[]` | `object` | 2 个子字段 | 占比分布列表。 |
| `analysis.audience_profile.province.ratio_list[].key` | `str` | 吉林 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.province.ratio_list[].value` | `float` | 0.004834405901742269 | 对应指标值，通常为比例或指数。 |
| `analysis.audience_profile.province.tgi_list` | `array` | 33 项；首项类型 object | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.province.tgi_list[]` | `object` | 2 个子字段 | TGI 指数列表，用于衡量相对整体人群的偏好强度。 |
| `analysis.audience_profile.province.tgi_list[].key` | `str` | 吉林 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.audience_profile.province.tgi_list[].value` | `float` | 47.48143392757728 | 对应指标值，通常为比例或指数。 |
| `analysis.other_data` | `object` | 4 个子字段 | 其他受众偏好与相似作者数据。 |
| `analysis.other_data.audience_prefer_similar_authors` | `array` | 7 项；首项类型 object | 受众偏好的相似作者列表。 |
| `analysis.other_data.audience_prefer_similar_authors[]` | `object` | 5 个子字段 | 受众偏好的相似作者列表。 |
| `analysis.other_data.audience_prefer_similar_authors[].avatar_larger` | `object` | 2 个子字段 | 大尺寸头像对象。 |
| `analysis.other_data.audience_prefer_similar_authors[].avatar_larger.uri` | `str` | 1080x1080/aweme-avatar/douyin-user-image-file_c26d15823dc4bacfb73faece3cefa1e5 | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `analysis.other_data.audience_prefer_similar_authors[].avatar_larger.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `analysis.other_data.audience_prefer_similar_authors[].follower_count` | `int` | 8615549 | 粉丝数。 |
| `analysis.other_data.audience_prefer_similar_authors[].nickname` | `str` | 小龙同学和赵老师 | 作者昵称。 |
| `analysis.other_data.audience_prefer_similar_authors[].sec_uid` | `str` | MS4wLjABAAAAmtCyWoKgBRalGHmU_AQjxzWiHczR6HL_tUvBqwyieO4LhhwXtTI-5VH5-IYuBVxD | 作者加密 UID。 |
| `analysis.other_data.audience_prefer_similar_authors[].uid` | `str` | 2714013751576094 | 作者 UID。 |
| `analysis.other_data.audience_prefer_topic` | `array` | 10 项；首项类型 object | 受众偏好的话题列表。 |
| `analysis.other_data.audience_prefer_topic[]` | `object` | 7 个子字段 | 受众偏好的话题列表。 |
| `analysis.other_data.audience_prefer_topic[].cha_id` | `str` | 1572512083183630 | 受众兴趣、相似作者和热门搜索等扩展分析字段。 |
| `analysis.other_data.audience_prefer_topic[].cha_name` | `str` | 星座 | 话题名称。 |
| `analysis.other_data.audience_prefer_topic[].cover_item` | `object` | 2 个子字段 | 话题封面资源。 |
| `analysis.other_data.audience_prefer_topic[].cover_item.uri` | `str` | fb3800066f8ce2c2fea9 | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `analysis.other_data.audience_prefer_topic[].cover_item.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |
| `analysis.other_data.audience_prefer_topic[].score_7d` | `int` | 20834388 | 近 7 日热度分数。 |
| `analysis.other_data.audience_prefer_topic[].score_7d_list` | `array` | 7 项；首项类型 object | 近 7 日每日热度分数列表。 |
| `analysis.other_data.audience_prefer_topic[].score_7d_list[]` | `object` | 2 个子字段 | 近 7 日每日热度分数列表。 |
| `analysis.other_data.audience_prefer_topic[].score_7d_list[].key` | `str` | 20260313 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.other_data.audience_prefer_topic[].score_7d_list[].value` | `int` | 2462077 | 对应指标值，通常为比例或指数。 |
| `analysis.other_data.audience_prefer_topic[].type` | `int` | 0 | 平台枚举类型；在话题结构中 type=1 通常表示 hashtag。 |
| `analysis.other_data.audience_prefer_topic[].vv_7d` | `int` | 734537820 | 近 7 日播放量/观看量。 |
| `analysis.other_data.audience_preference` | `object` | 3 个子字段 | 受众兴趣偏好汇总。 |
| `analysis.other_data.audience_preference.die_hard_fans_data` | `object` | 2 个子字段 | 铁粉兴趣偏好数据。 |
| `analysis.other_data.audience_preference.die_hard_fans_data.ratio_data` | `array` | 0 项 | 兴趣占比数据。 |
| `analysis.other_data.audience_preference.die_hard_fans_data.tgi_data` | `array` | 0 项 | 兴趣 TGI 数据。 |
| `analysis.other_data.audience_preference.fans_data` | `object` | 2 个子字段 | 粉丝兴趣偏好数据。 |
| `analysis.other_data.audience_preference.fans_data.ratio_data` | `array` | 0 项 | 兴趣占比数据。 |
| `analysis.other_data.audience_preference.fans_data.tgi_data` | `array` | 0 项 | 兴趣 TGI 数据。 |
| `analysis.other_data.audience_preference.total_data` | `object` | 2 个子字段 | 整体观看人群兴趣偏好数据。 |
| `analysis.other_data.audience_preference.total_data.ratio_data` | `array` | 1 项；首项类型 object | 兴趣占比数据。 |
| `analysis.other_data.audience_preference.total_data.ratio_data[]` | `object` | 3 个子字段 | 兴趣占比数据。 |
| `analysis.other_data.audience_preference.total_data.ratio_data[].key` | `str` | 电视剧 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.other_data.audience_preference.total_data.ratio_data[].second_tag_data` | `array` | 1 项；首项类型 object | 二级兴趣标签数据。 |
| `analysis.other_data.audience_preference.total_data.ratio_data[].second_tag_data[]` | `object` | 2 个子字段 | 二级兴趣标签数据。 |
| `analysis.other_data.audience_preference.total_data.ratio_data[].second_tag_data[].key` | `str` | 电视剧拆条 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.other_data.audience_preference.total_data.ratio_data[].second_tag_data[].value` | `int` | 1 | 对应指标值，通常为比例或指数。 |
| `analysis.other_data.audience_preference.total_data.ratio_data[].value` | `int` | 1 | 对应指标值，通常为比例或指数。 |
| `analysis.other_data.audience_preference.total_data.tgi_data` | `array` | 1 项；首项类型 object | 兴趣 TGI 数据。 |
| `analysis.other_data.audience_preference.total_data.tgi_data[]` | `object` | 2 个子字段 | 兴趣 TGI 数据。 |
| `analysis.other_data.audience_preference.total_data.tgi_data[].key` | `str` | 电视剧 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.other_data.audience_preference.total_data.tgi_data[].value` | `float` | 3691.5315580412293 | 对应指标值，通常为比例或指数。 |
| `analysis.other_data.audience_search_most_keywords` | `array` | 10 项；首项类型 object | 受众最近常搜关键词。 |
| `analysis.other_data.audience_search_most_keywords[]` | `object` | 3 个子字段 | 受众最近常搜关键词。 |
| `analysis.other_data.audience_search_most_keywords[].keywords` | `str` | 王者荣耀 | 搜索词。 |
| `analysis.other_data.audience_search_most_keywords[].query_7d_list` | `array` | 7 项；首项类型 object | 近 7 日每日搜索量列表。 |
| `analysis.other_data.audience_search_most_keywords[].query_7d_list[]` | `object` | 2 个子字段 | 近 7 日每日搜索量列表。 |
| `analysis.other_data.audience_search_most_keywords[].query_7d_list[].key` | `str` | 20260310 | 分类键名，例如来源、年龄段、城市级别等。 |
| `analysis.other_data.audience_search_most_keywords[].query_7d_list[].value` | `int` | 510073 | 对应指标值，通常为比例或指数。 |
| `analysis.other_data.audience_search_most_keywords[].query_cnt_7d` | `int` | 4298474 | 近 7 日搜索总量。 |
| `analysis.comment_hot_words` | `object` | 1 个子字段 | 评论热词分析。 |
| `analysis.comment_hot_words.word_cloud_list` | `array` | 100 项；首项类型 object | 评论词云词条列表。 |
| `analysis.comment_hot_words.word_cloud_list[]` | `object` | 3 个子字段 | 评论词云词条列表。 |
| `analysis.comment_hot_words.word_cloud_list[].rank` | `int` | 1 | 排名。 |
| `analysis.comment_hot_words.word_cloud_list[].score` | `str` | 10 | 热度分数。 |
| `analysis.comment_hot_words.word_cloud_list[].word` | `str` | 程序员 | 热词。 |
| `creator_stats` | `object` | 22 个子字段 | 创作者后台核心经营指标整理版，比公开 statistics 更偏运营分析。 |
| `creator_stats.play_count` | `int` | 34599 | 播放量。 |
| `creator_stats.digg_count` | `int` | 132 | 点赞数。 |
| `creator_stats.comment_count` | `int` | 147 | 评论数。 |
| `creator_stats.share_count` | `int` | 19 | 分享数。 |
| `creator_stats.collect_count` | `int` | 22 | 收藏数。 |
| `creator_stats.download_count` | `int` | 2 | 下载次数。 |
| `creator_stats.danmaku_count` | `int` | 0 | 弹幕数量。 |
| `creator_stats.dislike_count` | `int` | 10 | 不感兴趣/负反馈次数。 |
| `creator_stats.cover_show_count` | `int` | 5834 | 封面曝光次数。 |
| `creator_stats.avg_view_duration` | `float` | 17.069455 | 平均观看时长，单位秒。 |
| `creator_stats.avg_view_percent` | `float` | 0.282518 | 平均播放进度比例，0-1。 |
| `creator_stats.finish_rate` | `float` | 0.113454 | 完播率，0-1。 |
| `creator_stats.finish_rate_5s` | `float` | 0.44837 | 5 秒留存/看过 5 秒比例，0-1。 |
| `creator_stats.bounce_rate_2s` | `float` | 0.344223 | 2 秒跳出率，0-1。 |
| `creator_stats.follow_count` | `int` | 25 | 因该作品带来的新增关注数。 |
| `creator_stats.unfollow_count` | `int` | 1 | 因该作品相关周期内产生的取关数。 |
| `creator_stats.profile_visit` | `int` | 597 | 主页访问次数。 |
| `creator_stats.fan_view_ratio` | `float` | 0.002464 | 粉丝观看占比，0-1。 |
| `creator_stats.digg_rate` | `float` | 0.003815 | 点赞率，点赞数/播放量。 |
| `creator_stats.comment_rate` | `float` | 0.004249 | 评论率，评论数/播放量。 |
| `creator_stats.share_rate` | `float` | 0.000549 | 分享率，分享数/播放量。 |
| `creator_stats.collect_rate` | `float` | 0.000636 | 收藏率，收藏数/播放量。 |
| `play_info` | `object` | 1 个子字段 | 播放地址相关信息整理版。 |
| `play_info.url` | `object` | 2 个子字段 | 平台原始字段；需要结合所在模块和枚举值进一步解释。 |
| `play_info.url.uri` | `str` | v0300fg10000d5397ofog65o589s64a0 | 资源 URI 或平台内部资源标识，通常需要配合 url_list 才能直接访问。 |
| `play_info.url.url_list` | `array` | 4 项；首项类型 str | 可访问 URL 列表，平台通常提供多个 CDN 或不同规格地址。 |

## 使用提示

- `raw_list_data` 是平台原始返回，字段多、枚举多，适合保留追溯；日常分析优先使用整理后的 `base_info`、`statistics`、`creator_stats`、`tags`、`analysis`。
- 大整数 ID 建议统一按字符串使用，例如 `_id`、`aweme_id`、`id_str`、`mid`。部分 `Int64` 字段在展示时可能出现尾数精度问题。
- 比率类字段一般是 0-1 小数，例如 `finish_rate = 0.113454` 表示约 11.35%。
- `analysis.*.ratio_list` 表示人群占比，`analysis.*.tgi_list` 表示相对偏好指数；TGI 越高，说明该人群/兴趣相对整体更集中。

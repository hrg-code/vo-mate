# douyin_fans_summary 字段说明：第一条数据

本文档基于 MongoDB `crawler_raw_db.douyin_fans_summary` 的第一条实际文档生成，用来说明抖音创作者后台粉丝总览数据中各字段的含义。

## 数据概览

- 文档 ID / 账号 sec_uid：`MS4wLjABAAAAecPgbxHjmy-XcTMGPTqFu-9jdBlpGRfREjVVfxceUSx22PbSOfI3rrjFO8mxKOnF`
- 粉丝总数：`1012`
- 近 1 日净增粉丝：`0`；取关：`0`；主页带粉：`0`
- 近 7 日净增粉丝：`-2`；取关：`3`；主页带粉：`1`
- 采集时间：`2026-02-05 12:56:49.529000`

## 顶层模块

| 字段 | 含义 |
| --- | --- |
| `_id` | MongoDB 主键；本集合第一条数据中使用账号的 sec_uid 作为唯一标识。 |
| `aweme_id` | 作品 ID；粉丝总览是账号级数据，因此这里为空。 |
| `meta` | 采集元数据，记录更新时间、任务和来源。 |
| `payload` | 抖音创作者后台粉丝总览接口返回主体。 |
| `sec_uid` | 账号加密 UID，用于标识抖音创作者账号。 |

## 完整字段字典

| 字段路径 | 类型 | 示例/结构 | 字段含义 |
| --- | --- | --- | --- |
| `_id` | `str` | MS4wLjABAAAAecPgbxHjmy-XcTMGPTqFu-9jdBlpGRfREjVVfxceUSx22PbSOfI3rrjFO8mxKOnF | MongoDB 主键；本集合第一条数据中使用账号的 sec_uid 作为唯一标识。 |
| `aweme_id` | `null` | None | 作品 ID；粉丝总览是账号级数据，因此这里为空。 |
| `meta` | `object` | 4 个子字段 | 采集元数据，记录更新时间、任务和来源。 |
| `meta.last_update` | `datetime` | 2026-02-05 12:56:49.529000 | 该粉丝总览数据最近一次采集/更新时间。 |
| `meta.task_id` | `str` | UPLOAD_FANS_SUMMARY_20260205_205649 | 采集任务 ID。 |
| `meta.trace_id` | `str` | 744f6b6e-e3ba-4a03-a1bd-221ae9ce45b5 | 采集链路追踪 ID，用于排查任务日志。 |
| `meta.source_url` | `str` | https://creator.douyin.com/janus/douyin/creator/bff/data/fans/summary/v2 | 数据来源接口 URL。 |
| `payload` | `object` | 27 个子字段 | 抖音创作者后台粉丝总览接口返回主体。 |
| `payload.BaseResp` | `object` | 2 个子字段 | 接口基础响应状态。 |
| `payload.BaseResp.StatusCode` | `int` | 0 | 接口返回状态码，0 通常表示成功。 |
| `payload.BaseResp.StatusMessage` | `str` |  | 接口返回状态消息，成功时通常为空。 |
| `payload.active_levels` | `array` | 4 项；首项类型 object | 粉丝活跃等级分布。 |
| `payload.active_levels[]` | `object` | 2 个子字段 | 数组中的单个元素结构。 |
| `payload.active_levels[].count` | `int` | 21 | 数量。 |
| `payload.active_levels[].label` | `str` | 低活 | 分类标签名称。 |
| `payload.active_time_range` | `array` | 3 项；首项类型 object | 粉丝活跃时间段分布。 |
| `payload.active_time_range[]` | `object` | 2 个子字段 | 数组中的单个元素结构。 |
| `payload.active_time_range[].count` | `int` | 1 | 数量。 |
| `payload.active_time_range[].label` | `str` | 20-21 | 分类标签名称。 |
| `payload.age_distribution` | `array` | 5 项；首项类型 object | 粉丝年龄分布。 |
| `payload.age_distribution[]` | `object` | 2 个子字段 | 数组中的单个元素结构。 |
| `payload.age_distribution[].count` | `int` | 6 | 数量。 |
| `payload.age_distribution[].label` | `str` | <23 | 分类标签名称。 |
| `payload.city_distribution` | `array` | 28 项；首项类型 object | 粉丝地域/省份分布。 |
| `payload.city_distribution[]` | `object` | 2 个子字段 | 数组中的单个元素结构。 |
| `payload.city_distribution[].count` | `int` | 8 | 数量。 |
| `payload.city_distribution[].label` | `str` | 河南 | 分类标签名称。 |
| `payload.contribution_billboard_7` | `object` | 1 个子字段 | 近 7 日贡献榜数据。 |
| `payload.contribution_billboard_7.scores` | `array` | 1 项；首项类型 object | 榜单条目列表。 |
| `payload.contribution_billboard_7.scores[]` | `object` | 2 个子字段 | 榜单条目列表。 |
| `payload.contribution_billboard_7.scores[].score` | `int` | 4 | 榜单分数，用于衡量贡献或互动强度。 |
| `payload.contribution_billboard_7.scores[].user_info` | `object` | 40 个子字段 | 榜单用户资料。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_larger` | `object` | 2 个子字段 | 大尺寸头像对象。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_larger.uri` | `str` | 1080x1080/aweme-avatar/tos-cn-i-0813c000-ce_okCEnIOzwA1XEl17eifpZ0BCkAwvbiAWqA6U... | 资源 URI 或平台内部资源标识。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_larger.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_medium` | `object` | 2 个子字段 | 中尺寸头像对象。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_medium.uri` | `str` | 720x720/aweme-avatar/tos-cn-i-0813c000-ce_okCEnIOzwA1XEl17eifpZ0BCkAwvbiAWqA6UAD | 资源 URI 或平台内部资源标识。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_medium.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_thumb` | `object` | 2 个子字段 | 小尺寸头像对象。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_thumb.uri` | `str` | 100x100/aweme-avatar/tos-cn-i-0813c000-ce_okCEnIOzwA1XEl17eifpZ0BCkAwvbiAWqA6UAD | 资源 URI 或平台内部资源标识。 |
| `payload.contribution_billboard_7.scores[].user_info.avatar_thumb.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.contribution_billboard_7.scores[].user_info.aweme_count` | `int` | 2 | 用户公开视频数量。 |
| `payload.contribution_billboard_7.scores[].user_info.card_entries` | `null` | None | 用户卡片入口信息。 |
| `payload.contribution_billboard_7.scores[].user_info.custom_verify` | `str` |  | 用户自定义认证文案。 |
| `payload.contribution_billboard_7.scores[].user_info.enterprise_verify_reason` | `str` |  | 企业认证说明。 |
| `payload.contribution_billboard_7.scores[].user_info.favoriting_count` | `int` | 59477 | 用户喜欢/收藏数量。 |
| `payload.contribution_billboard_7.scores[].user_info.follow_status` | `int` | 0 | 当前账号对该用户的关注状态编码。 |
| `payload.contribution_billboard_7.scores[].user_info.follower_count` | `int` | 163 | 用户粉丝数。 |
| `payload.contribution_billboard_7.scores[].user_info.follower_status` | `int` | 1 | 该用户与当前账号的粉丝关系状态编码。 |
| `payload.contribution_billboard_7.scores[].user_info.followers_detail` | `null` | None | 粉丝详情扩展字段。 |
| `payload.contribution_billboard_7.scores[].user_info.following_count` | `int` | 1372 | 用户关注数。 |
| `payload.contribution_billboard_7.scores[].user_info.geofencing` | `null` | None | 地理围栏/地区限制信息。 |
| `payload.contribution_billboard_7.scores[].user_info.has_orders` | `bool` | False | 是否有订单相关能力或记录。 |
| `payload.contribution_billboard_7.scores[].user_info.is_ad_fake` | `bool` | False | 是否广告假量/异常标记。 |
| `payload.contribution_billboard_7.scores[].user_info.is_gov_media_vip` | `bool` | False | 是否政务/媒体认证。 |
| `payload.contribution_billboard_7.scores[].user_info.mix_info` | `null` | None | 合集信息。 |
| `payload.contribution_billboard_7.scores[].user_info.nickname` | `str` | 长夜有月 | 用户昵称。 |
| `payload.contribution_billboard_7.scores[].user_info.original_musician` | `object` | 2 个子字段 | 原创音乐人信息。 |
| `payload.contribution_billboard_7.scores[].user_info.original_musician.music_count` | `int` | 0 | 原创音乐数量。 |
| `payload.contribution_billboard_7.scores[].user_info.original_musician.music_used_count` | `int` | 0 | 原创音乐被使用次数。 |
| `payload.contribution_billboard_7.scores[].user_info.platform_sync_info` | `null` | None | 平台同步信息。 |
| `payload.contribution_billboard_7.scores[].user_info.policy_version` | `null` | None | 策略版本信息。 |
| `payload.contribution_billboard_7.scores[].user_info.rate` | `int` | 1 | 平台评级/状态编码。 |
| `payload.contribution_billboard_7.scores[].user_info.region` | `str` | CN | 用户地区。 |
| `payload.contribution_billboard_7.scores[].user_info.sec_uid` | `str` | MS4wLjABAAAAUP48Z83OJiaoZtxP4iqPcJQdUQzUm5ouy7ccsEBFzGw | 用户加密 UID。 |
| `payload.contribution_billboard_7.scores[].user_info.secret` | `int` | 0 | 账号私密状态编码。 |
| `payload.contribution_billboard_7.scores[].user_info.short_id` | `str` | 800753802 | 用户短 ID。 |
| `payload.contribution_billboard_7.scores[].user_info.signature` | `str` | 喜欢的不想说，不喜欢的，也不太想说。 | 用户个人简介。 |
| `payload.contribution_billboard_7.scores[].user_info.status` | `int` | 1 | 用户账号状态编码。 |
| `payload.contribution_billboard_7.scores[].user_info.story_open` | `bool` | False | 是否开启故事功能。 |
| `payload.contribution_billboard_7.scores[].user_info.total_favorited` | `str` | 242 | 用户累计获赞数。 |
| `payload.contribution_billboard_7.scores[].user_info.type_label` | `array` | 0 项 | 用户类型标签列表。 |
| `payload.contribution_billboard_7.scores[].user_info.uid` | `str` | 63807942982 | 用户 UID。 |
| `payload.contribution_billboard_7.scores[].user_info.unique_id` | `str` |  | 抖音号/唯一 ID。 |
| `payload.contribution_billboard_7.scores[].user_info.user_canceled` | `bool` | False | 用户是否已注销。 |
| `payload.contribution_billboard_7.scores[].user_info.verification_type` | `int` | 1 | 认证类型编码。 |
| `payload.contribution_billboard_7.scores[].user_info.video_icon` | `object` | 2 个子字段 | 视频图标资源。 |
| `payload.contribution_billboard_7.scores[].user_info.video_icon.uri` | `str` |  | 资源 URI 或平台内部资源标识。 |
| `payload.contribution_billboard_7.scores[].user_info.video_icon.url_list` | `array` | 0 项 | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.contribution_billboard_7.scores[].user_info.with_commerce_entry` | `bool` | False | 是否展示商业化入口。 |
| `payload.contribution_billboard_7.scores[].user_info.with_fusion_shop_entry` | `bool` | False | 是否展示融合店铺入口。 |
| `payload.contribution_billboard_7.scores[].user_info.with_shop_entry` | `bool` | False | 是否展示店铺入口。 |
| `payload.device_brand_distribution` | `array` | 13 项；首项类型 object | 粉丝设备品牌分布。 |
| `payload.device_brand_distribution[]` | `object` | 2 个子字段 | 数组中的单个元素结构。 |
| `payload.device_brand_distribution[].count` | `int` | 20 | 数量。 |
| `payload.device_brand_distribution[].label` | `str` | OPPO | 分类标签名称。 |
| `payload.extra` | `object` | 2 个子字段 | 接口额外信息。 |
| `payload.extra.logid` | `str` | 202602052056491E9D0137C2316462944E | 接口请求日志 ID。 |
| `payload.extra.now` | `int` | 1770296209000 (2026-02-05 20:56:49) | 接口返回时的服务器时间戳，毫秒。 |
| `payload.fans_client_data` | `object` | 7 个子字段 | 粉丝侧内容消费/互动数据。 |
| `payload.fans_client_data.comment_cnt` | `int` | 0 | 粉丝评论数。 |
| `payload.fans_client_data.comment_cnt_incr_rate` | `str` | -1 | 粉丝评论数较上一周期的增长率；字符串形式，-1 常表示无可比数据或下降边界值。 |
| `payload.fans_client_data.like_cnt` | `int` | 0 | 粉丝点赞数。 |
| `payload.fans_client_data.like_cnt_incr_rate` | `str` | -1 | 粉丝点赞数较上一周期的增长率。 |
| `payload.fans_client_data.share_cnt` | `int` | 0 | 粉丝分享数。 |
| `payload.fans_client_data.vv_cnt` | `int` | 4 | 粉丝播放/观看次数。 |
| `payload.fans_client_data.vv_cnt_incr_rate` | `str` | -0.636 | 粉丝播放/观看次数较上一周期的增长率。 |
| `payload.fans_cnt_sum` | `int` | 1012 | 当前账号粉丝总数。 |
| `payload.fans_data_1` | `object` | 4 个子字段 | 近 1 日粉丝增减数据。 |
| `payload.fans_data_1.cancel_fans` | `int` | 0 | 近 1 日取关人数。 |
| `payload.fans_data_1.cancel_fans_incr_rate` | `str` | -1 | 近 1 日取关人数较上一周期增长率。 |
| `payload.fans_data_1.home_view_fans` | `int` | 0 | 近 1 日通过主页访问带来的粉丝数。 |
| `payload.fans_data_1.net_fans` | `int` | 0 | 近 1 日净增粉丝数。 |
| `payload.fans_data_7` | `object` | 5 个子字段 | 近 7 日粉丝增减数据。 |
| `payload.fans_data_7.cancel_fans` | `int` | 3 | 近 7 日取关人数。 |
| `payload.fans_data_7.cancel_fans_incr_rate` | `str` | -0.400 | 近 7 日取关人数较上一周期增长率。 |
| `payload.fans_data_7.home_view_fans` | `int` | 1 | 近 7 日通过主页访问带来的粉丝数。 |
| `payload.fans_data_7.home_view_fans_incr_rate` | `str` | 0.000 | 近 7 日主页访问带粉较上一周期增长率。 |
| `payload.fans_data_7.net_fans` | `int` | -2 | 近 7 日净增粉丝数。 |
| `payload.fans_data_trend_1` | `object` | 3 个子字段 | 近 1 日趋势明细。 |
| `payload.fans_data_trend_1.cancel_fans_trend` | `array` | 1 项；首项类型 object | 取关粉丝趋势列表。 |
| `payload.fans_data_trend_1.cancel_fans_trend[]` | `object` | 4 个子字段 | 取关粉丝趋势列表。 |
| `payload.fans_data_trend_1.cancel_fans_trend[].douyin_value` | `int` | 0 | 抖音端对应指标值。 |
| `payload.fans_data_trend_1.cancel_fans_trend[].key` | `str` | 2026-02-04 | 趋势日期或分类键。 |
| `payload.fans_data_trend_1.cancel_fans_trend[].value` | `int` | 0 | 指标值。 |
| `payload.fans_data_trend_1.cancel_fans_trend[].xigua_value` | `int` | 0 | 西瓜端对应指标值。 |
| `payload.fans_data_trend_1.home_view_fans_trend` | `array` | 1 项；首项类型 object | 主页访问带粉趋势列表。 |
| `payload.fans_data_trend_1.home_view_fans_trend[]` | `object` | 2 个子字段 | 主页访问带粉趋势列表。 |
| `payload.fans_data_trend_1.home_view_fans_trend[].key` | `str` | 2026-02-04 | 趋势日期或分类键。 |
| `payload.fans_data_trend_1.home_view_fans_trend[].value` | `int` | 0 | 指标值。 |
| `payload.fans_data_trend_1.net_fans_trend` | `array` | 1 项；首项类型 object | 净增粉丝趋势列表。 |
| `payload.fans_data_trend_1.net_fans_trend[]` | `object` | 4 个子字段 | 净增粉丝趋势列表。 |
| `payload.fans_data_trend_1.net_fans_trend[].douyin_value` | `int` | 0 | 抖音端对应指标值。 |
| `payload.fans_data_trend_1.net_fans_trend[].key` | `str` | 2026-02-04 | 趋势日期或分类键。 |
| `payload.fans_data_trend_1.net_fans_trend[].value` | `int` | 0 | 指标值。 |
| `payload.fans_data_trend_1.net_fans_trend[].xigua_value` | `int` | 0 | 西瓜端对应指标值。 |
| `payload.fans_data_trend_7` | `object` | 3 个子字段 | 近 7 日趋势明细；样例里包含 30 个日期点，可能是接口固定返回窗口。 |
| `payload.fans_data_trend_7.cancel_fans_trend` | `array` | 30 项；首项类型 object | 取关粉丝趋势列表。 |
| `payload.fans_data_trend_7.cancel_fans_trend[]` | `object` | 4 个子字段 | 取关粉丝趋势列表。 |
| `payload.fans_data_trend_7.cancel_fans_trend[].douyin_value` | `int` | 0 | 抖音端对应指标值。 |
| `payload.fans_data_trend_7.cancel_fans_trend[].key` | `str` | 2026-02-04 | 趋势日期或分类键。 |
| `payload.fans_data_trend_7.cancel_fans_trend[].value` | `int` | 0 | 指标值。 |
| `payload.fans_data_trend_7.cancel_fans_trend[].xigua_value` | `int` | 0 | 西瓜端对应指标值。 |
| `payload.fans_data_trend_7.home_view_fans_trend` | `array` | 30 项；首项类型 object | 主页访问带粉趋势列表。 |
| `payload.fans_data_trend_7.home_view_fans_trend[]` | `object` | 2 个子字段 | 主页访问带粉趋势列表。 |
| `payload.fans_data_trend_7.home_view_fans_trend[].key` | `str` | 2026-02-04 | 趋势日期或分类键。 |
| `payload.fans_data_trend_7.home_view_fans_trend[].value` | `int` | 0 | 指标值。 |
| `payload.fans_data_trend_7.net_fans_trend` | `array` | 30 项；首项类型 object | 净增粉丝趋势列表。 |
| `payload.fans_data_trend_7.net_fans_trend[]` | `object` | 4 个子字段 | 净增粉丝趋势列表。 |
| `payload.fans_data_trend_7.net_fans_trend[].douyin_value` | `int` | 0 | 抖音端对应指标值。 |
| `payload.fans_data_trend_7.net_fans_trend[].key` | `str` | 2026-02-04 | 趋势日期或分类键。 |
| `payload.fans_data_trend_7.net_fans_trend[].value` | `int` | 0 | 指标值。 |
| `payload.fans_data_trend_7.net_fans_trend[].xigua_value` | `int` | 0 | 西瓜端对应指标值。 |
| `payload.fans_decreasing_analysis` | `array` | 0 项 | 掉粉分析数据；当前样例为空数组。 |
| `payload.fans_flow_contribution` | `null` | None | 粉丝流量贡献数据；当前样例为空。 |
| `payload.fans_interest_distribution` | `array` | 10 项；首项类型 object | 粉丝兴趣标签分布。 |
| `payload.fans_interest_distribution[]` | `object` | 2 个子字段 | 数组中的单个元素结构。 |
| `payload.fans_interest_distribution[].count` | `int` | 33 | 数量。 |
| `payload.fans_interest_distribution[].label` | `str` | 随拍 | 分类标签名称。 |
| `payload.fans_portrait` | `object` | 3 个子字段 | 新增/关注来源等粉丝画像补充信息。 |
| `payload.fans_portrait.from_label` | `array` | 1 项；首项类型 object | 粉丝来源标签列表。 |
| `payload.fans_portrait.from_label[]` | `object` | 3 个子字段 | 数组中的单个元素结构。 |
| `payload.fans_portrait.from_label[].count` | `int` | 1 | 数量。 |
| `payload.fans_portrait.from_label[].name` | `str` | 我的主页 | 来源名称。 |
| `payload.fans_portrait.from_label[].type` | `int` | 19 | 来源或分类类型编码。 |
| `payload.fans_portrait.like_item` | `null` | None | 粉丝喜欢作品信息；当前样例为空。 |
| `payload.fans_portrait.like_item_keyword` | `null` | None | 粉丝喜欢作品关键词；当前样例为空。 |
| `payload.follower_summary` | `array` | 2 项；首项类型 object | 按统计周期汇总的粉丝增量概览。 |
| `payload.follower_summary[]` | `object` | 3 个子字段 | 数组中的单个元素结构。 |
| `payload.follower_summary[].day` | `int` | 7 | 统计周期天数。 |
| `payload.follower_summary[].fans_cnt` | `int` | -2 | 该周期粉丝净增数量。 |
| `payload.follower_summary[].fans_cnt_inc` | `array` | 7 项；首项类型 object | 该周期每日粉丝增量列表。 |
| `payload.follower_summary[].fans_cnt_inc[]` | `object` | 3 个子字段 | 该周期每日粉丝增量列表。 |
| `payload.follower_summary[].fans_cnt_inc[].date` | `int` | 1770134400 (2026-02-04) | 日期时间戳，通常为 Unix 秒级时间戳。 |
| `payload.follower_summary[].fans_cnt_inc[].has_inc` | `bool` | True | 该日期是否有增量数据。 |
| `payload.follower_summary[].fans_cnt_inc[].inc` | `int` | 0 | 该日期粉丝增量。 |
| `payload.gender_distribution` | `array` | 2 项；首项类型 object | 粉丝性别分布。 |
| `payload.gender_distribution[]` | `object` | 2 个子字段 | 数组中的单个元素结构。 |
| `payload.gender_distribution[].count` | `int` | 45 | 数量。 |
| `payload.gender_distribution[].label` | `str` | female | 分类标签名称。 |
| `payload.has_fans_manage_permission` | `bool` | True | 当前登录账号是否有粉丝管理权限。 |
| `payload.has_publish_items` | `bool` | True | 账号是否发布过作品。 |
| `payload.interaction_billboard_30` | `object` | 1 个子字段 | 近 30 日互动榜数据。 |
| `payload.interaction_billboard_30.scores` | `array` | 20 项；首项类型 object | 榜单条目列表。 |
| `payload.interaction_billboard_30.scores[]` | `object` | 2 个子字段 | 榜单条目列表。 |
| `payload.interaction_billboard_30.scores[].score` | `int` | 6 | 榜单分数，用于衡量贡献或互动强度。 |
| `payload.interaction_billboard_30.scores[].user_info` | `object` | 40 个子字段 | 榜单用户资料。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_larger` | `object` | 2 个子字段 | 大尺寸头像对象。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_larger.uri` | `str` | 1080x1080/aweme-avatar/mosaic-legacy_3791_5035712059 | 资源 URI 或平台内部资源标识。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_larger.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_medium` | `object` | 2 个子字段 | 中尺寸头像对象。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_medium.uri` | `str` | 720x720/aweme-avatar/mosaic-legacy_3791_5035712059 | 资源 URI 或平台内部资源标识。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_medium.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_thumb` | `object` | 2 个子字段 | 小尺寸头像对象。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_thumb.uri` | `str` | 100x100/aweme-avatar/mosaic-legacy_3791_5035712059 | 资源 URI 或平台内部资源标识。 |
| `payload.interaction_billboard_30.scores[].user_info.avatar_thumb.url_list` | `array` | 3 项；首项类型 str | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.interaction_billboard_30.scores[].user_info.aweme_count` | `int` | 0 | 用户公开视频数量。 |
| `payload.interaction_billboard_30.scores[].user_info.card_entries` | `null` | None | 用户卡片入口信息。 |
| `payload.interaction_billboard_30.scores[].user_info.custom_verify` | `str` |  | 用户自定义认证文案。 |
| `payload.interaction_billboard_30.scores[].user_info.enterprise_verify_reason` | `str` |  | 企业认证说明。 |
| `payload.interaction_billboard_30.scores[].user_info.favoriting_count` | `int` | 93 | 用户喜欢/收藏数量。 |
| `payload.interaction_billboard_30.scores[].user_info.follow_status` | `int` | 0 | 当前账号对该用户的关注状态编码。 |
| `payload.interaction_billboard_30.scores[].user_info.follower_count` | `int` | 4 | 用户粉丝数。 |
| `payload.interaction_billboard_30.scores[].user_info.follower_status` | `int` | 1 | 该用户与当前账号的粉丝关系状态编码。 |
| `payload.interaction_billboard_30.scores[].user_info.followers_detail` | `null` | None | 粉丝详情扩展字段。 |
| `payload.interaction_billboard_30.scores[].user_info.following_count` | `int` | 11 | 用户关注数。 |
| `payload.interaction_billboard_30.scores[].user_info.geofencing` | `null` | None | 地理围栏/地区限制信息。 |
| `payload.interaction_billboard_30.scores[].user_info.has_orders` | `bool` | False | 是否有订单相关能力或记录。 |
| `payload.interaction_billboard_30.scores[].user_info.is_ad_fake` | `bool` | False | 是否广告假量/异常标记。 |
| `payload.interaction_billboard_30.scores[].user_info.is_gov_media_vip` | `bool` | False | 是否政务/媒体认证。 |
| `payload.interaction_billboard_30.scores[].user_info.mix_info` | `null` | None | 合集信息。 |
| `payload.interaction_billboard_30.scores[].user_info.nickname` | `str` | 大红人 | 用户昵称。 |
| `payload.interaction_billboard_30.scores[].user_info.original_musician` | `object` | 2 个子字段 | 原创音乐人信息。 |
| `payload.interaction_billboard_30.scores[].user_info.original_musician.music_count` | `int` | 0 | 原创音乐数量。 |
| `payload.interaction_billboard_30.scores[].user_info.original_musician.music_used_count` | `int` | 0 | 原创音乐被使用次数。 |
| `payload.interaction_billboard_30.scores[].user_info.platform_sync_info` | `null` | None | 平台同步信息。 |
| `payload.interaction_billboard_30.scores[].user_info.policy_version` | `null` | None | 策略版本信息。 |
| `payload.interaction_billboard_30.scores[].user_info.rate` | `int` | 1 | 平台评级/状态编码。 |
| `payload.interaction_billboard_30.scores[].user_info.region` | `str` | CN | 用户地区。 |
| `payload.interaction_billboard_30.scores[].user_info.sec_uid` | `str` | MS4wLjABAAAAF0sLg3-i3mqtnXzV8PNXLSOaFmUXt99M7b0crS-JDec | 用户加密 UID。 |
| `payload.interaction_billboard_30.scores[].user_info.secret` | `int` | 0 | 账号私密状态编码。 |
| `payload.interaction_billboard_30.scores[].user_info.short_id` | `str` | 3686498271 | 用户短 ID。 |
| `payload.interaction_billboard_30.scores[].user_info.signature` | `str` |  | 用户个人简介。 |
| `payload.interaction_billboard_30.scores[].user_info.status` | `int` | 1 | 用户账号状态编码。 |
| `payload.interaction_billboard_30.scores[].user_info.story_open` | `bool` | False | 是否开启故事功能。 |
| `payload.interaction_billboard_30.scores[].user_info.total_favorited` | `str` | 0 | 用户累计获赞数。 |
| `payload.interaction_billboard_30.scores[].user_info.type_label` | `array` | 0 项 | 用户类型标签列表。 |
| `payload.interaction_billboard_30.scores[].user_info.uid` | `str` | 553766038027640 | 用户 UID。 |
| `payload.interaction_billboard_30.scores[].user_info.unique_id` | `str` | dyv2rcusc91y | 抖音号/唯一 ID。 |
| `payload.interaction_billboard_30.scores[].user_info.user_canceled` | `bool` | False | 用户是否已注销。 |
| `payload.interaction_billboard_30.scores[].user_info.verification_type` | `int` | 1 | 认证类型编码。 |
| `payload.interaction_billboard_30.scores[].user_info.video_icon` | `object` | 2 个子字段 | 视频图标资源。 |
| `payload.interaction_billboard_30.scores[].user_info.video_icon.uri` | `str` |  | 资源 URI 或平台内部资源标识。 |
| `payload.interaction_billboard_30.scores[].user_info.video_icon.url_list` | `array` | 0 项 | 可访问 URL 列表，通常为多个 CDN 地址。 |
| `payload.interaction_billboard_30.scores[].user_info.with_commerce_entry` | `bool` | False | 是否展示商业化入口。 |
| `payload.interaction_billboard_30.scores[].user_info.with_fusion_shop_entry` | `bool` | False | 是否展示融合店铺入口。 |
| `payload.interaction_billboard_30.scores[].user_info.with_shop_entry` | `bool` | False | 是否展示店铺入口。 |
| `payload.interaction_billboard_7` | `object` | 1 个子字段 | 近 7 日互动榜数据；当前样例为空。 |
| `payload.interaction_billboard_7.scores` | `null` | None | 榜单条目列表。 |
| `payload.no_ads` | `int` | 0 | 广告相关标记，0 通常表示无特殊限制或默认状态。 |
| `payload.status_code` | `int` | 0 | 业务状态码，0 通常表示成功。 |
| `payload.status_msg` | `str` |  | 业务状态消息，成功时通常为空。 |
| `sec_uid` | `str` | MS4wLjABAAAAecPgbxHjmy-XcTMGPTqFu-9jdBlpGRfREjVVfxceUSx22PbSOfI3rrjFO8mxKOnF | 账号加密 UID，用于标识抖音创作者账号。 |

## 使用提示

- `payload.*_distribution` 通常是分类分布数组，`label` 是分类名，`count` 是该分类人数或计数。
- `fans_data_1` 和 `fans_data_7` 适合做短期涨粉/掉粉看板；`fans_data_trend_*` 适合画趋势线。
- `contribution_billboard_7`、`interaction_billboard_30` 里的 `user_info` 是榜单用户资料，包含头像、昵称、关注关系和账号状态等。
- 增长率字段当前以字符串保存，例如 `-0.636`；分析时可转成浮点数，`-1` 需要结合业务规则判断是无对比数据还是边界值。
- `sec_uid`、`uid`、`short_id` 等账号标识建议按字符串处理，避免跨语言处理时出现精度或格式问题。

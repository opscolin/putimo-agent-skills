---
name: weather
description: 高德地图天气查询 API 集成。使用时根据中文城市、县区名称查询天气信息。当用户请求查询天气、天气状况、天气预报、温度、湿度等天气相关信息时使用此技能。
---

# 天气查询技能

## 概述

使用高德地图天气 API 查询指定地区的实况天气和天气预报。

## 快速开始

使用 `weather_query.py` 脚本查询天气：

```bash
# 查询实况天气
python scripts/weather_query.py "北京"

# 查询天气预报（未来4天）
python scripts/weather_query.py "北京" all
```

## API 说明

### 1. 地区查询 API

获取地区编码（adcode）：

```
GET https://restapi.amap.com/v3/config/district
```

参数：
- `keywords`: 城市或县区名称（中文）
- `subdistrict`: 返回下级行政区级数
- `key`: API Key
- `output`: 返回格式（json）

### 2. 天气查询 API

查询天气信息：

```
GET https://restapi.amap.com/v3/weather/weatherInfo
```

参数：
- `city`: 城市名称或 adcode
- `extensions`: 返回类型（base=实况，all=预报）
- `key`: API Key
- `output`: 返回格式（json）

## 工作流程

1. 加载 API Key（首次使用时提示用户输入）
2. 尝试直接使用城市名查询天气
3. 如果失败，先查询地区编码，再用 adcode 查询天气
4. 格式化并显示结果

## 输出格式

### 实况天气
- 城市名称
- 温度
- 湿度
- 风向
- 风力
- 天气状况
- 更新时间

### 天气预报
- 城市名称
- 未来4天的预报
- 每日白天/夜间天气和温度
- 风向风力信息

## 资源

### scripts/weather_query.py

天气查询脚本，包含以下功能：
- API Key 管理（自动保存到 `~/.claude/skills/weather/api_key.txt`）
- 地区编码查询
- 实况天气查询
- 天气预报查询
- 结果格式化

#!/usr/bin/env python3
"""高德地图天气查询脚本"""

import sys
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

# API Key 存储路径
API_KEY_FILE = Path.home() / ".claude" / "skills" / "weather" / "api_key.txt"

API_URLS = {
    "district": "https://restapi.amap.com/v3/config/district",
    "weather": "https://restapi.amap.com/v3/weather/weatherInfo"
}


def load_api_key(api_key_arg=None):
    """加载 API Key，优先级：命令行参数 > 环境变量 > 存储文件"""
    # 1. 检查命令行参数
    if api_key_arg:
        return api_key_arg

    # 2. 检查环境变量
    env_key = os.environ.get("AMAP_API_KEY")
    if env_key:
        return env_key

    # 3. 检查存储文件
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()

    return None


def save_api_key(api_key):
    """保存 API Key 到文件"""
    if not api_key:
        return False
    API_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    API_KEY_FILE.write_text(api_key)
    return True


def query_district(api_key, keywords, subdistrict=1):
    """查询地区编码"""
    params = {
        "keywords": keywords,
        "subdistrict": str(subdistrict),
        "key": api_key,
        "output": "json"
    }

    url = f"{API_URLS['district']}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"error": str(e)}


def query_weather(api_key, city, extensions="base"):
    """查询天气信息

    Args:
        city: 城市名称或 adcode
        extensions: "base" (实况天气) 或 "all" (预报天气)
    """
    params = {
        "city": city,
        "extensions": extensions,
        "key": api_key,
        "output": "json"
    }

    url = f"{API_URLS['weather']}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"error": str(e)}


def format_weather_result(data, extensions="base"):
    """格式化天气结果"""
    if "error" in data:
        return f"查询失败: {data['error']}"

    if data.get("status") != "1":
        return f"API 返回错误: {data.get('info', '未知错误')}"

    lives = data.get("lives", [])
    forecasts = data.get("forecasts", [])

    result = []

    # 实况天气
    if lives:
        for live in lives:
            result.append(f"📍 {live.get('city', '未知城市')}")
            result.append(f"🌡️  温度: {live.get('temperature', '--')}℃")
            result.append(f"💧 湿度: {live.get('humidity', 'N/A')}%")
            result.append(f"🌬️  风向: {live.get('winddirection', 'N/A')}")
            result.append(f"💨 风力: {live.get('windpower', 'N/A')}")
            result.append(f"☁️  天气: {live.get('weather', 'N/A')}")
            result.append(f"⏰ 更新时间: {live.get('reporttime', 'N/A')}")

    # 预报天气
    if forecasts:
        for forecast in forecasts:
            result.append(f"\n📍 {forecast.get('city', '未知城市')} 天气预报")
            result.append(f"📅 更新时间: {forecast.get('reporttime', 'N/A')}")

            casts = forecast.get("casts", [])
            for cast in casts[:4]:  # 显示4天预报
                result.append(f"\n🗓️  {cast.get('date', 'N/A')} ({cast.get('week', 'N/A')})")
                result.append(f"   白天: {cast.get('dayweather', 'N/A')}, {cast.get('daytemp', '--')}℃")
                result.append(f"   夜间: {cast.get('nightweather', 'N/A')}, {cast.get('nighttemp', '--')}℃")
                result.append(f"   风向: {cast.get('daywind', 'N/A')}, 风力: {cast.get('daypower', 'N/A')}")

    return "\n".join(result) if result else "无天气数据"


def main():
    if len(sys.argv) < 2:
        print("用法: weather_query.py <城市名称> [base|all] [--api-key <KEY>]")
        print("  base - 实况天气 (默认)")
        print("  all  - 预报天气")
        print("  --api-key - 可选，指定高德地图 API Key (默认从环境变量 AMAP_API_KEY 或存储文件读取)")
        sys.exit(1)

    city = sys.argv[1]
    extensions = "base"
    api_key_arg = None

    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] in ["base", "all"]:
            extensions = sys.argv[i]
            i += 1
        elif sys.argv[i] == "--api-key" and i + 1 < len(sys.argv):
            api_key_arg = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # 加载 API Key
    api_key = load_api_key(api_key_arg)

    if not api_key:
        print("错误: 未找到高德地图 API Key")
        print("请通过以下方式之一提供 API Key:")
        print("  1. 使用 --api-key 参数")
        print("  2. 设置环境变量 AMAP_API_KEY")
        print("  3. 首次运行时，脚本会提示输入并保存")
        sys.exit(1)

    # 直接查询天气（高德 API 支持直接用城市名）
    data = query_weather(api_key, city, extensions)

    if data.get("status") == "1":
        # 查询成功
        print(format_weather_result(data, extensions))
    else:
        # 查询失败，尝试先获取 adcode
        print(f"使用城市名 '{city}' 查询失败，尝试获取地区编码...")
        district_data = query_district(api_key, city)

        if district_data.get("status") == "1":
            districts = district_data.get("districts", [])
            if districts and len(districts) > 0:
                adcode = districts[0].get("adcode")
                if adcode:
                    print(f"找到地区编码: {adcode}")
                    data = query_weather(api_key, adcode, extensions)
                    print(format_weather_result(data, extensions))
                else:
                    print("未找到地区编码")
            else:
                print("未找到匹配的地区")
        else:
            print(f"地区查询失败: {district_data.get('info', '未知错误')}")


if __name__ == "__main__":
    main()

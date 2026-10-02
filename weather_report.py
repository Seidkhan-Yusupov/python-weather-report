# 날씨 예보 프로그램 (Open-Meteo API)
# GitHub Repository:
# https://github.com/Seidkhan-Yusupov/python-weather-report.git
#
# 기능
# - 사용자가 지역을 입력하면 해당 지역의 위도/경도를 검색
# - 오늘부터 3일 동안 오전 6시 / 오후 3시 날씨 표시
# - 일일 최저 / 최고 기온 표시
# - 원하면 받아온 날씨 정보를 JSON 파일로 저장

import json
from datetime import datetime
from pathlib import Path

import requests


DEFAULT_CITY = "Cheonan"
FORECAST_DAYS = 3
TARGET_HOURS = (6, 15)


WEATHER_CODES = {
    0: "맑음",
    1: "대체로 맑음",
    2: "부분적으로 흐림",
    3: "흐림",
    45: "안개",
    48: "서리 안개",
    51: "약한 이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    56: "약한 어는 이슬비",
    57: "강한 어는 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    66: "약한 어는 비",
    67: "강한 어는 비",
    71: "약한 눈",
    73: "눈",
    75: "강한 눈",
    77: "싸락눈",
    80: "약한 소나기",
    81: "소나기",
    82: "강한 소나기",
    85: "약한 눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "우박을 동반한 뇌우",
    99: "강한 우박을 동반한 뇌우",
}


def get_location(city):
    """Open-Meteo Geocoding API로 지역의 위도/경도를 찾는다."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city,
        "count": 1,
        "language": "ko",
        "format": "json",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        return None

    result = results[0]
    return {
        "name": result.get("name", city),
        "country": result.get("country", ""),
        "admin1": result.get("admin1", ""),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }


def get_weather(latitude, longitude):
    """Open-Meteo Forecast API에서 3일간 날씨 정보를 가져온다."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
            ]
        ),
        "daily": "temperature_2m_max,temperature_2m_min",
        "forecast_days": FORECAST_DAYS,
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def day_label(index):
    if index == 0:
        return "오늘"
    if index == 1:
        return "내일"
    return "모레"


def weather_text(code):
    return WEATHER_CODES.get(code, f"날씨 코드 {code}")


def find_hourly_index(hourly_times, date_string, hour):
    target = f"{date_string}T{hour:02d}:00"
    try:
        return hourly_times.index(target)
    except ValueError:
        return None


def print_forecast(location, weather):
    hourly = weather["hourly"]
    daily = weather["daily"]

    print()
    print("=" * 58)
    print(
        f"🌤️  {location['name']} 날씨 예보 "
        f"(오전 6시 / 오후 3시 기준)"
    )
    print("=" * 58)

    for day_index, date_string in enumerate(daily["time"]):
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        short_date = date_obj.strftime("%m.%d.")

        print()
        print(f"🗓️ {day_label(day_index)} ({short_date})")
        print("-" * 50)

        for hour in TARGET_HOURS:
            idx = find_hourly_index(hourly["time"], date_string, hour)

            if idx is None:
                print(f"{hour:02d}:00 정보를 찾을 수 없습니다.")
                continue

            period = "오전" if hour < 12 else "오후"

            temperature = hourly["temperature_2m"][idx]
            humidity = hourly["relative_humidity_2m"][idx]
            rain_probability = hourly["precipitation_probability"][idx]
            weather_code = hourly["weather_code"][idx]
            wind_speed = hourly["wind_speed_10m"][idx]

            print(f"🌅 {period} {hour:02d}:00")
            print(f"   날씨: {weather_text(weather_code)}")
            print(f"   기온: {temperature:.0f} °C")
            print(f"   강수확률: {rain_probability:.0f}%")
            print(f"   습도: {humidity:.0f}%")
            print(f"   풍속: {wind_speed:.0f} km/h")
            print()

        min_temp = daily["temperature_2m_min"][day_index]
        max_temp = daily["temperature_2m_max"][day_index]

        print(
            f"🌡️ 일일 기온: 최저 {min_temp:.0f} °C / "
            f"최고 {max_temp:.0f} °C"
        )
        print()
        print("=" * 58)


def save_json(location, weather):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_city = location["name"].replace(" ", "_")
    filename = Path(f"weather_{safe_city}_{now}.json")

    output = {
        "location": location,
        "weather": weather,
    }

    with filename.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=4)

    print(f"✅ 저장 완료: {filename}")


def main():
    print("🌤️ 날씨 예보 프로그램 (Open-Meteo API)")
    print("오전 6시, 오후 3시 기준으로 3일간 날씨를 제공합니다.")
    print("-" * 58)

    city = input(
        f"날씨를 확인할 지역을 입력하세요 (기본값: {DEFAULT_CITY}): "
    ).strip()

    if not city:
        city = DEFAULT_CITY

    try:
        location = get_location(city)

        if location is None:
            print("❌ 해당 지역을 찾을 수 없습니다.")
            return

        print(
            f"\n📍 {location['name']} "
            f"(위도: {location['latitude']}, "
            f"경도: {location['longitude']})의 날씨 정보를 가져옵니다..."
        )

        weather = get_weather(
            location["latitude"],
            location["longitude"],
        )

        print_forecast(location, weather)

        answer = input(
            "\n날씨 정보를 JSON 파일로 저장하시겠습니까? (y/n): "
        ).strip().lower()

        if answer == "y":
            save_json(location, weather)
        else:
            print("저장하지 않고 프로그램을 종료합니다.")

    except requests.RequestException as error:
        print(f"❌ 인터넷 또는 API 연결 오류가 발생했습니다: {error}")
    except (KeyError, IndexError, TypeError, ValueError) as error:
        print(f"❌ 날씨 데이터를 처리하는 중 오류가 발생했습니다: {error}")


if __name__ == "__main__":
    main()

import os
from datetime import datetime
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "weather_log.csv")
API_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"



class WeatherError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.message = message
        self.status = status


@app.errorhandler(WeatherError)
def handle_weather_error(error):
    return jsonify(error=error.message), error.status


def get_suffix(n):
    if 10 <= n <= 20:
        return "th"
    elif n % 10 == 1:
        return "st"
    elif n % 10 == 2:
        return "nd"
    elif n % 10 == 3:
        return "rd"
    else:
        return "th"


def get_advice(feels_like, description, unit, is_daytime=True):
    feels_c = (feels_like - 32) * 5 / 9 if unit == "f" else feels_like
    tips = []

    if feels_c < 10:
        tips.append("It’s cold, so wear a warm coat.")
    elif feels_c < 18:
        tips.append("It’s cool, so bring a jacket.")
    elif feels_c < 26:
        tips.append("It’s mild, so light layers should do.")
    else:
        tips.append("It’s hot, so dress light and stay hydrated.")

    desc = description.lower()
    if "rain" in desc or "drizzle" in desc or "thunderstorm" in desc:
        tips.append("Take an umbrella, it might rain.")
    elif "snow" in desc:
        tips.append("Wear waterproof shoes.")
    elif "clear" in desc and feels_c >= 26 and is_daytime:
        tips.append("Sunglasses and sunscreen are a good idea today.")

    return " ".join(tips)


def theme_for(condition, description, is_day):
    if condition == "Clear":
        return "clear-day" if is_day else "clear-night"
    if condition == "Thunderstorm":
        return "storm"
    if condition in ("Rain", "Drizzle"):
        return "rain"
    if condition == "Snow":
        return "snow"
    if condition in ("Mist", "Fog", "Haze", "Smoke", "Dust", "Sand", "Ash"):
        return "fog"
    if condition == "Clouds":
        if "few" in description or "scattered" in description:
            return "partly-cloudy"
        return "clouds"
    return "clouds"


def call_api(url, city, unit):
    
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise WeatherError("The server has no API key. Set WEATHER_API_KEY and restart it.", 500)
 
    params = {"q": city, "appid": api_key, "units": "metric" if unit == "c" else "imperial"}
 
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            raise WeatherError(f"Couldn’t find weather for “{city}”. Check the spelling.", 404)
        if error.response is not None and error.response.status_code == 401:
            raise WeatherError("The weather service rejected the API key.", 502)
        raise WeatherError("The weather service had a problem. Try again later.", 502)
    except requests.exceptions.ConnectionError:
        raise WeatherError("The server has no internet connection.", 503)
    except requests.exceptions.Timeout:
        raise WeatherError("The weather service took too long to answer.", 504)
    except requests.exceptions.RequestException:
        raise WeatherError("Something went wrong reaching the weather service.", 502)
 
    return response.json()


def fetch_current(city, unit):
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise WeatherError("The server has no API key. Set WEATHER_API_KEY and restart it.", 500)

    params = {"q": city, "appid": api_key, "units": "metric" if unit == "c" else "imperial"}

    try:
        response = requests.get(API_URL, params=params, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            raise WeatherError(f"Couldn’t find weather for “{city}”. Check the spelling.", 404)
        if error.response is not None and error.response.status_code == 401:
            raise WeatherError("The weather service rejected the API key.", 502)
        raise WeatherError("The weather service had a problem. Try again later.", 502)
    except requests.exceptions.ConnectionError:
        raise WeatherError("The server has no internet connection.", 503)
    except requests.exceptions.Timeout:
        raise WeatherError("The weather service took too long to answer.", 504)
    except requests.exceptions.RequestException:
        raise WeatherError("Something went wrong reaching the weather service.", 502)

    data = response.json()
    is_day = data["sys"]["sunrise"] <= data["dt"] <= data["sys"]["sunset"]
    condition = data["weather"][0]["main"]
    description = data["weather"][0]["description"]
    feels_like = data["main"]["feels_like"]
    now = datetime.now()

    return {
        "city": data.get("name") or city.title(),
        "temp": data["main"]["temp"],
        "feels_like": feels_like,
        "humidity": data["main"]["humidity"],
        "description": description,
        "condition": condition,
        "is_day": is_day,
        "theme": theme_for(condition, description, is_day),
        "advice": get_advice(feels_like, description, unit, is_day),
        "date": f"{now.strftime('%A')}, {now.day}{get_suffix(now.day)} of {now.strftime('%B %Y')}",
        "time": now.strftime("%H:%M"),
        "unit": unit,
    }


def fetch_forecast(city, unit):
    data = call_api(FORECAST_URL, city, unit)
 
    days = []
    for report in data["list"]:
        date_text, time_text = report["dt_txt"].split(" ")
        if time_text != "12:00:00":
            continue
 
        day_date = datetime.strptime(date_text, "%Y-%m-%d")
        days.append({
            "weekday": day_date.strftime("%A"),
            "date": f"{day_date.day}{get_suffix(day_date.day)} {day_date.strftime('%B')}",
            "temp": report["main"]["temp"],
            "description": report["weather"][0]["description"],
            "icon": report["weather"][0]["icon"],
        })
 
    return {"city": data["city"]["name"], "days": days, "unit": unit}


def log_search(info):
    file_is_new = not os.path.exists(LOG_FILE)
    now = datetime.now()
    city = info["city"].replace(",", " ")

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        if file_is_new:
            file.write("date,time,city,temp,deg_unit,description,humidity\n")
        file.write(f"{now.strftime('%Y/%m/%d')},{info['time']},{city},{info['temp']},{info['unit']},{info['description']},{info['humidity']}\n")


def read_history(count=5):
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    rows = []
    for line in lines[1:][-count:]:
        parts = line.strip().split(",")
        if len(parts) != 7:
            continue
        date, time_text, city, temp, unit, description, humidity = parts
        rows.append({"date": date, "time": time_text, "city": city, "temp": float(temp),
                     "unit": unit, "description": description, "humidity": humidity})

    rows.reverse()
    return rows


def get_unit():
    return "f" if request.args.get("unit") == "f" else "c"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip().lower()
    if not city:
        return jsonify(error="Please enter a city name."), 400

    info = fetch_current(city, get_unit())
    if request.args.get("log") != "0":
        log_search(info)
    return jsonify(info)


@app.route("/api/compare")
def api_compare():
    a_name = request.args.get("a", "").strip().lower()
    b_name = request.args.get("b", "").strip().lower()
    if not a_name or not b_name:
        return jsonify(error="Please enter two city names."), 400
    if a_name == b_name:
        return jsonify(error="Please choose two different cities."), 400

    unit = get_unit()
    a = fetch_current(a_name, unit)
    b = fetch_current(b_name, unit)

    if a["temp"] == b["temp"]:
        warm = "Both cities have the same temperature."
    else:
        warmer, cooler = (a, b) if a["temp"] > b["temp"] else (b, a)
        warm = f"{warmer['city']} is warmer than {cooler['city']}."

    if a["humidity"] == b["humidity"]:
        humid = "Both cities are equally humid."
    else:
        humid = f"{(a if a['humidity'] > b['humidity'] else b)['city']} is more humid."

    return jsonify(a=a, b=b, verdict=f"{warm} {humid}")


@app.route("/api/forecast")
def api_forecast():
    city = request.args.get("city", "").strip().lower()
    if not city:
        return jsonify(error="Please enter a city name."), 400
    return jsonify(fetch_forecast(city, get_unit()))


@app.route("/api/history")
def api_history():
    return jsonify(read_history())


if __name__ == "__main__":
    app.run(debug=True)
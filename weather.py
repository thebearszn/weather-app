import os
import requests
import sys
from datetime import datetime


def get_suffix(n):
    # Finding the suffix for dates, i.e. 1st, 2nd, etc.
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


def get_advice(feels_like, description, deg_unit, is_daytime=True):
    # Turns the temperature into Celsius so one set of thresholds works for both units
    if deg_unit == "f":
        feels_c = (feels_like - 32) * 5 / 9
    else:
        feels_c = feels_like

    tips = []

    if feels_c < 10:
        tips.append("It's cold, so wear a warm coat.")
    elif feels_c < 18:
        tips.append("It's cool, so bring a jacket.")
    elif feels_c < 26:
        tips.append("It's mild, so light layers should do.")
    else:
        tips.append("It's hot, so dress light and stay hydrated.")

    desc = description.lower()
    if "rain" in desc or "drizzle" in desc or "thunderstorm" in desc:
        tips.append("Take an umbrella, it might rain.")
    elif "snow" in desc:
        tips.append("Wear waterproof shoes.")
    elif "clear" in desc and feels_c >= 26 and is_daytime:
        tips.append("Sunglasses and sunscreen are a good idea today.")

    return " ".join(tips)


def choose_unit(allow_back=False):
    # Keeps asking until the user gives a valid answer
    if allow_back:
        prompt = "Celsius or Fahrenheit? Enter 'C' or 'F' (or 'back'): "
    else:
        prompt = "Do you want the degrees in Celsius or Fahrenheit? Enter 'C' or 'F' (or 'exit'): "

    while True:
        answer = input(prompt).strip().lower()

        if answer == "back" and allow_back:
            return None
        if answer == "exit" and not allow_back:
            print("See you later. Goodbye!")
            sys.exit()
        if answer == "c":
            print("You have selected Celsius.")
            return "c"
        if answer == "f":
            print("You have selected Fahrenheit.")
            return "f"

        print("Please enter 'C' or 'F'.")


def ask_cities():
    user_text = input("Enter city name(s), separated by commas (or 'back'): ").strip().lower()

    if user_text == "back":
        return []

    cities = []
    for city in user_text.split(","):
        city = city.strip()
        if city:
            cities.append(city)

    if not cities:
        print("Please enter at least one city name.")

    return cities


def get_weather(deg_unit, city):
    API_KEY = os.getenv("WEATHER_API_KEY")
    if deg_unit == 'c':
        degree_unit = 'metric'
    else:
        degree_unit = 'imperial'

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units={degree_unit}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"Couldn't find weather for {city}. Please check your spelling.")
        return
    except requests.exceptions.ConnectionError:
        print("No internet connection. Please check your network settings.")
        return
    except requests.exceptions.Timeout:
        print("The request timed out. Please try again later.")
        return
    except requests.exceptions.RequestException as e:
        print(f"Something went wrong: {e}.")
        return

    data = response.json()

    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]

    #Check if it's day or night in the city using the time in the API
    is_daytime = data["sys"]["sunrise"] <= data["dt"] <= data["sys"]["sunset"]

    today = datetime.now()
    day = today.day
    suffix = get_suffix(day)
    weekday = today.strftime("%A")
    month_year = today.strftime("%B %Y")
    real_date = f"{weekday}, {day}{suffix} of {month_year}"
    now = datetime.now().strftime("%Y/%m/%d")

    today_time = datetime.now().strftime("%H:%M")

    filename = "weather_log.csv"
    file_is_new = not os.path.exists(filename)
    with open(filename, "a") as file:
        if file_is_new:
            file.write("date,time,city,temp,deg_unit,description,humidity\n")
        file.write(f"{now},{today_time},{city.title()},{temp},{deg_unit},{description},{humidity}\n")

    print(f"\nToday's date is {real_date} and the time is {today_time}.\nThe temperature in {city.title()} is {temp}°{deg_unit.capitalize()}, but it feels like {feels_like}°{deg_unit.capitalize()}.\nConditions are {description} and humidity is at {humidity}%. Have a great day!")
    print(f"Advice: {get_advice(feels_like, description, deg_unit, is_daytime)}\n")


def get_forecast(deg_unit, city):
    API_KEY = os.getenv("WEATHER_API_KEY")
    if deg_unit == 'c':
        degree_unit = 'metric'
    else:
        degree_unit = 'imperial'

    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units={degree_unit}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"Couldn't find a forecast for {city}.")
        return
    except requests.exceptions.ConnectionError:
        print("No internet connection. Please check your network settings.")
        return
    except requests.exceptions.Timeout:
        print("The request timed out. Please try again later.")
        return
    except requests.exceptions.RequestException as e:
        print(f"Something went wrong: {e}.")
        return

    data = response.json()

    print(f"\n5-day forecast for {city.title()} (midday readings):")

    for report in data["list"]:
        date_text, time_text = report["dt_txt"].split(" ")
        if time_text != "12:00:00":
            continue

        temp = report["main"]["temp"]
        description = report["weather"][0]["description"]

        forecast_date = datetime.strptime(date_text, "%Y-%m-%d")
        day = forecast_date.day
        nice_date = f"{forecast_date.strftime('%A')}, {day}{get_suffix(day)} {forecast_date.strftime('%B')}"

        print(f"  {nice_date}: {temp}°{deg_unit.capitalize()}, {description}")

    print()


def fetch_current(deg_unit, city):
    API_KEY = os.getenv("WEATHER_API_KEY")
    if deg_unit == 'c':
        degree_unit = 'metric'
    else:
        degree_unit = 'imperial'

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units={degree_unit}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"Couldn't find weather for {city}. Please check your spelling.")
        return None
    except requests.exceptions.ConnectionError:
        print("No internet connection. Please check your network settings.")
        return None
    except requests.exceptions.Timeout:
        print("The request timed out. Please try again later.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Something went wrong: {e}.")
        return None

    data = response.json()

    return {
        "city": city.title(),
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
    }


def compare_cities(deg_unit):
    print("Enter two cities to compare.")
    first = input("First city: ").strip().lower()
    second = input("Second city: ").strip().lower()

    if not first or not second:
        print("Please enter two city names.")
        return
    if first == second:
        print("Please choose two different cities.")
        return

    a = fetch_current(deg_unit, first)
    b = fetch_current(deg_unit, second)
    if a is None or b is None:
        return

    symbol = deg_unit.upper()
    temp_a = f"{a['temp']}°{symbol}"
    temp_b = f"{b['temp']}°{symbol}"
    hum_a = f"{a['humidity']}%"
    hum_b = f"{b['humidity']}%"

    print()
    print(f"{'':<14}{a['city']:<18}{b['city']:<18}")
    print(f"{'Temperature':<14}{temp_a:<18}{temp_b:<18}")
    print(f"{'Humidity':<14}{hum_a:<18}{hum_b:<18}")
    print(f"{'Conditions':<14}{a['description']:<18}{b['description']:<18}")
    print()

    if a["temp"] > b["temp"]:
        print(f"{a['city']} is warmer than {b['city']}.")
    elif b["temp"] > a["temp"]:
        print(f"{b['city']} is warmer than {a['city']}.")
    else:
        print("Both cities have the same temperature.")

    if a["humidity"] > b["humidity"]:
        print(f"{a['city']} is more humid.")
    elif b["humidity"] > a["humidity"]:
        print(f"{b['city']} is more humid.")
    else:
        print("Both cities have the same humidity.")
    print()


# History

def show_history(count=5):
    filename = "weather_log.csv"

    if not os.path.exists(filename):
        print("\nNo search history yet.\n")
        return

    with open(filename, "r") as file:
        lines = file.readlines()

    rows = lines[1:]  # skip the header line
    if not rows:
        print("\nNo search history yet.\n")
        return

    shown = rows[-count:]  # the last `count` rows
    print(f"\nLast {len(shown)} searches:")

    for line in shown:
        parts = line.strip().split(",")
        if len(parts) != 7:
            print("  " + line.strip())  # unexpected format, show it as it is
            continue
        date, time_text, city, temp, unit, description, humidity = parts
        print(f"  {date} {time_text} | {city}: {temp}°{unit.upper()}, {description}, humidity {humidity}%")
    print()


# Menu

def show_menu(deg_unit):
    if deg_unit == "c":
        unit_name = "Celsius"
    else:
        unit_name = "Fahrenheit"

    print(f"\n===== Weather Menu (units: {unit_name}) =====")
    print("1. Check current weather")
    print("2. Check 5-day forecast")
    print("3. Compare two cities")
    print("4. View search history")
    print("5. Change temperature unit")
    print("0. Exit")


# Main prog

deg_unit = choose_unit()

while True:
    show_menu(deg_unit)
    choice = input("Choose an option: ").strip().lower()

    if choice == "0" or choice == "exit":
        print("See you later. Goodbye!")
        break

    if choice == "1":
        for city in ask_cities():
            get_weather(deg_unit, city)
    elif choice == "2":
        for city in ask_cities():
            get_forecast(deg_unit, city)
    elif choice == "3":
        compare_cities(deg_unit)
    elif choice == "4":
        show_history()
    elif choice == "5":
        new_unit = choose_unit(allow_back=True)
        if new_unit:
            deg_unit = new_unit
    else:
        print("Please choose a number from the menu.")
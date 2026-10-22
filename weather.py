import os
import requests
import sys
from datetime import datetime

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

    # Finding the suffix for dates, i.e 1st, 2nd, etc.
    
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
        print(f"No internet connection. Please check your network settings.")
        return
    except requests.exceptions.Timeout:
        print(f"The request timed out. Please try again later.")
        return
    except requests.exceptions.RequestException as e:
        print(f"Something went wrong: {e}.")
        return

    data = response.json()

    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]

    today = datetime.now()
    day = today.day
    suffix = get_suffix(day)
    weekday = today.strftime("%A")
    month_year = today.strftime("%B %Y")
    real_date = f"{weekday}, {day}{suffix} of {month_year}"
    now = datetime.now().strftime("%Y/%m/%d")

    # Two used variables here. real_date for the user's output and now for the log.

    today_time = datetime.now().strftime("%H:%M")

    filename = "weather_log.csv"
    file_is_new = not os.path.exists(filename)
    with open(filename, "a") as file:
        if file_is_new:
            file.write("date,time,city,temp,deg_unit,description,humidity\n")
        file.write(f"{now},{today_time},{city.title()},{temp},{deg_unit},{description},{humidity}\n")


    print(f"\nToday's date is {real_date} and the time is {today_time}.\nThe temperature in {city.title()} is {temp}°{deg_unit.capitalize()}, but it feels like {feels_like}°{deg_unit.capitalize()}.\nConditions are {description} and humidity is at {humidity}%. Have a great day!\n")

deg_unit = input("Do you want the degrees in Celsius or Fahrenheit? Enter 'C' or 'F': ").strip().lower()

while True:
    if deg_unit == "exit":
        print ("See you later. Goodbye!")
        sys.exit()
    if deg_unit == "c":
        deg_unit_1 = "celsius"
        print(f"You have selected °{deg_unit_1.capitalize()}.")
        break
    elif deg_unit == "f":
        deg_unit_1 = "fahrenheit"
        print(f"You have selected °{deg_unit_1.capitalize()}.")
        break
    else:
        deg_unit= input ("Please enter a unit. 'C' or 'F': ").strip().lower()   

while True:
    user_text = input("Enter your city name: ").strip().lower() 
    if user_text == "exit":
        print ("See you later. Goodbye!")
        break

    cities = user_text.split(",")
    for city in cities:
        city = city.strip()
        if not city:
            continue

        
        get_weather(deg_unit, city)

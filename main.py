import requests
import json
import time
from datetime import datetime

API_KEY = "YOUR_API_KEY"  # вставь сюда ключ (например OpenWeather)
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
CACHE_FILE = "weather_cache.json"
CACHE_TTL = 300  # 5 минут


class Cache:
    def __init__(self, file):
        self.file = file
        self.data = self.load()

    def load(self):
        try:
            with open(self.file, "r") as f:
                return json.load(f)
        except:
            return {}

    def save(self):
        with open(self.file, "w") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key):
        if key in self.data:
            entry = self.data[key]
            if time.time() - entry["timestamp"] < CACHE_TTL:
                return entry["data"]
        return None

    def set(self, key, value):
        self.data[key] = {
            "timestamp": time.time(),
            "data": value
        }
        self.save()


class WeatherClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.cache = Cache(CACHE_FILE)

    def fetch_weather(self, city):
        cached = self.cache.get(city)
        if cached:
            return cached

        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }

        response = requests.get(BASE_URL, params=params)

        if response.status_code != 200:
            raise Exception("API error")

        data = response.json()
        self.cache.set(city, data)
        return data


class WeatherFormatter:
    @staticmethod
    def format(data):
        name = data["name"]
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        desc = data["weather"][0]["description"]
        wind = data["wind"]["speed"]

        return f"""
📍 City: {name}
🌡 Temperature: {temp}°C (feels like {feels}°C)
💧 Humidity: {humidity}%
🌬 Wind: {wind} m/s
☁️ Condition: {desc}
"""


class CLI:
    @staticmethod
    def run():
        print("=== Weather CLI ===")

        client = WeatherClient(API_KEY)

        while True:
            city = input("\nEnter city (or 'exit'): ")

            if city.lower() == "exit":
                print("Bye!")
                break

            try:
                data = client.fetch_weather(city)
                output = WeatherFormatter.format(data)
                print(output)

            except Exception as e:
                print("Error:", e)


if __name__ == "__main__":
    CLI.run()

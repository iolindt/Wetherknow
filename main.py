from api import fetch_weather
from client import build_weather
from formatter import display
from cache import save, load

data = fetch_weather()

weather = build_weather(data)

save(weather)

result = load()

display(result)

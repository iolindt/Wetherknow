# Weather API Client

A lightweight Python application that fetches weather information from an API.

## Overview

Weather API Client demonstrates how a weather application can retrieve forecast data, parse API responses, cache results, and display formatted weather reports.

The project is designed with modular architecture and can later be connected to a real weather service such as OpenWeatherMap.

## Features

- Weather API client
- Response parsing
- Local cache
- Console report
- Clean architecture

## Project Structure

```
.
├── main.py
├── api.py
├── client.py
├── weather.py
├── formatter.py
├── cache.py
├── config.py
└── sample_response.py
```

## Example Output

```
========== WEATHER =========

City: London

Temperature : 21°C
Humidity    : 54%
Condition   : Cloudy

Data source: API
```

## Future Improvements

- OpenWeatherMap API
- Requests library
- Forecast support
- JSON cache
- GUI


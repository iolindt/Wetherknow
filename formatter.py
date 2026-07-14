def display(weather):

    print("=" * 35)
    print("WEATHER")
    print("=" * 35)
    print()

    print(f"City: {weather.city}\n")

    print(
        f"Temperature : {weather.temperature}°C"
    )

    print(
        f"Humidity    : {weather.humidity}%"
    )

    print(
        f"Condition   : {weather.condition}"
    )

    print("\nData source: API")

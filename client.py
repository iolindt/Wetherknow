from weather import Weather


def build_weather(data):

    return Weather(

        data["city"],

        data["temperature"],

        data["humidity"],

        data["condition"]

    )

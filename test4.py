import httpx

from fastapi import FastAPI


app = FastAPI()
WEATHER_API_KEY = "2919217a5640e6245f6b12215421373d"
URL = "https://api.openweathermap.org/data/2.5/weather"


@app.get("/weather/{city}")
async def post_weather(city):
    async with httpx.AsyncClient() as client:
        params = {
						"q": city,
						"appid": WEATHER_API_KEY,
				}
        response = await client.get(URL, params=params)
    data = response.json()
    return {
        "city": data["name"],
				"temperature": data["main"]["temp"],
		}
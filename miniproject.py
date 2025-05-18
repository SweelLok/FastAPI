from fastapi import FastAPI, Query, HTTPException, Request
from bs4 import BeautifulSoup
import httpx
import requests


app = FastAPI()


@app.get("/parse/")
async def parse_page(url = Query(..., description="URL сторінки для парсингу")):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(str(url))

    except httpx.HTTPError as e:
        raise HTTPException(detail=f"Помилка при запиті: {e}")

    soup = BeautifulSoup(response.text, "lxml")

    def get_all_headers() -> list:
        headers = []
        for i in range(1, 7):
            header_tags = soup.find_all(f"h{i}")
            for header in header_tags:
                header_text = header.get_text(strip=True)
                headers.append(header_text)
        return headers
    headers = get_all_headers()

    return {"headers": headers}


@app.get("/get_links/")
async def get_links(request : Request, site : str=Query(...)):
    try:
        page = requests.get(site)
        soup = BeautifulSoup(page.text, "html.parser")
        data = soup.find_all('a')

    except httpx.HTTPError as e:
        raise HTTPException(detail=f"Error : {e}")
    extract_data = {}

    for id, tag in enumerate(data):
        extract_data[id] = {
            "text": tag.get_text(strip=True),
            "href": tag.get("href")
        }
    return extract_data
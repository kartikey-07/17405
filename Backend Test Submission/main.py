from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime, timedelta
from log import Log
import os

app = FastAPI()

url_store = {}
clicks_store = {}

with open("../credentials.txt") as f:
    creds = dict(line.strip().split(": ") for line in f.readlines())

client_id = creds.get("clientID")
client_secret = creds.get("clientSecret")

class ShortUrlRequest(BaseModel):
    url: HttpUrl
    validity: Optional[int] = 30
    shortcode: Optional[str]

class ShortUrlResponse(BaseModel):
    shortLink: str
    expiry: str

class StatsResponse(BaseModel):
    original_url: str
    created_at: str
    expiry: str
    total_clicks: int

@app.post("/shorturls", response_model=ShortUrlResponse, status_code=201)
def create_shorturl(req: ShortUrlRequest, request: Request):
    Log("backend", "info", "create_shorturl", f"Received: {req.dict()}")
    
    code = req.shortcode or generate_shortcode()
    if code in url_store:
        Log("backend", "warning", "create_shorturl", f"Shortcode '{code}' already exists")
        raise HTTPException(status_code=400, detail="Shortcode already exists")
    
    expiry_time = datetime.utcnow() + timedelta(minutes=req.validity)
    url_store[code] = {
        "original_url": req.url,
        "created_at": datetime.utcnow(),
        "expiry": expiry_time
    }
    clicks_store[code] = 0

    short_link = f"http://{request.client.host}:{request.url.port or 80}/{code}"
    Log("backend", "info", "create_shorturl", f"Created: {short_link} | Expires at {expiry_time.isoformat()}")
    
    return ShortUrlResponse(shortLink=short_link, expiry=expiry_time.isoformat())

@app.get("/shorturls/{code}", response_model=StatsResponse)
def get_stats(code: str):
    if code not in url_store:
        Log("backend", "error", "get_stats", f"Shortcode '{code}' not found")
        raise HTTPException(status_code=404, detail="Shortcode not found")

    data = url_store[code]
    total_clicks = clicks_store.get(code, 0)

    Log("backend", "info", "get_stats", f"Stats retrieved for '{code}'")

    return StatsResponse(
        original_url=data["original_url"],
        created_at=data["created_at"].isoformat(),
        expiry=data["expiry"].isoformat(),
        total_clicks=total_clicks
    )

@app.get("/{code}")
def redirect_shorturl(code: str):
    if code not in url_store:
        Log("backend", "error", "redirect_shorturl", f"Shortcode '{code}' not found")
        raise HTTPException(status_code=404, detail="Shortcode not found")
    
    data = url_store[code]
    if datetime.utcnow() > data["expiry"]:
        Log("backend", "warning", "redirect_shorturl", f"Shortcode '{code}' expired")
        raise HTTPException(status_code=410, detail="Short URL expired")
    
    clicks_store[code] = clicks_store.get(code, 0) + 1
    Log("backend", "info", "redirect_shorturl", f"Redirecting '{code}' to {data['original_url']}")

    return {"redirect_to": data["original_url"]}

def generate_shortcode(length=6):
    import random, string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

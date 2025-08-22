from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import pickle
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv, find_dotenv
import logging

app = FastAPI()

# Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Model yükleme
with open(os.path.join(BASE_DIR, "house_price_model.pkl"), "rb") as f:
    saved_data = pickle.load(f)
    model = saved_data["model"]
    scaler = saved_data["scaler"]

# .env dosyası
load_dotenv(find_dotenv())
# Gizli bilgiler için varsayılan yok; host/port için güvenli varsayılan
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST") or "localhost"
DB_PORT = int(os.getenv("DB_PORT") or "5432")

# Logger
logger = logging.getLogger("uvicorn.error")

# Basit middleware: tum istekleri logla
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("HTTP %s %s", request.method, request.url.path)
    response = await call_next(request)
    return response

# Sağlık kontrolü / ping
@app.get("/api/ping")
async def ping():
    print("/api/ping invoked")
    logger.info("/api/ping ok")
    return JSONResponse({"ok": True})

# Pydantic model
class HousedFeatures(BaseModel):
    Square_Footage: int
    Num_Bedrooms: int
    Num_Bathrooms: int
    Year_Built: int
    Lot_Size: float
    Garage_Size: int
    Neighborhood_Quality: int

# Ana sayfa
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Tahmin + DB insert
@app.post("/predict")
async def predict(features: HousedFeatures):
    print("/predict invoked")
    logger.info("/predict called with payload: %s", features.dict())
    input_data = pd.DataFrame([features.dict()])
    ordered_cols = [
        "Square_Footage",
        "Num_Bedrooms",
        "Num_Bathrooms",
        "Year_Built",
        "Lot_Size",
        "Garage_Size",
        "Neighborhood_Quality",
    ]
    input_data = input_data[ordered_cols]

    # Scale ve predict
    input_scaled = scaler.transform(input_data)
    prediction = model.predict(input_scaled)
    price = float(prediction[0])

    # DB insert (env eksikse atla)
    if not DB_NAME or not DB_USER or not DB_PASSWORD:
        logger.warning("DB config missing (name/user/password). Skipping insert.")
        return JSONResponse({"predicted_price": price})

    try:
        logger.info("DB connect => host=%s port=%s db=%s", DB_HOST, DB_PORT, DB_NAME)
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT current_database(), current_schema()")
        db_info = cur.fetchone()
        logger.info("Connected to: %s", db_info)
        sql = (
            'INSERT INTO "public"."tbl_house" '
            '("Square_Footage","Num_Bedrooms","Num_Bathrooms","Year_Built","Lot_Size","Garage_Size","Neighborhood_Quality","House_Price") '
            'VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING "House_Price"'
        )
        cur.execute(
            sql,
            (
                features.Square_Footage,
                features.Num_Bedrooms,
                features.Num_Bathrooms,
                features.Year_Built,
                features.Lot_Size,
                features.Garage_Size,
                features.Neighborhood_Quality,
                price,
            ),
        )
        returned = cur.fetchone()
        logger.info("Inserted row, House_Price: %s | rows affected: %s", returned[0], cur.rowcount)
        cur.close()
        conn.close()
    except Exception:
        logger.exception("DB insert error")

    return JSONResponse({"predicted_price": price})


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import requests
import json
import joblib
import numpy as np
import time
from datetime import timedelta, datetime
import os
import google.generativeai as genai

from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user
)
from database import get_db, init_db
from config import settings, logger

# --- 1. CONFIGURATION ---
if not settings.gemini_api_key or settings.gemini_api_key == "GEMINI_API_KEY":
    logger.warning("GEMINI_API_KEY not found in environment.")
else:
    genai.configure(api_key=settings.gemini_api_key)
    logger.info("GenAI Configured Successfully!")

llm_model = genai.GenerativeModel('gemini-2.5-flash')

# --- GLOBAL CACHE ---
weather_cache = {}

# --- 1. LOAD THE ML FORECASTER ---
try:
    forecaster = joblib.load("syngenta_enterprise_model.pkl")
    logger.info("Predictive ML Model Loaded Successfully!")
except FileNotFoundError:
    forecaster = None
    logger.warning("syngenta_enterprise_model.pkl not found. Running with dummy data.")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-Powered Agronomy and Sales Co-Pilot API for Syngenta Enterprise."
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Syngenta Co-Pilot API",
        "status": "online",
        "health_check": "/health",
        "docs": "/docs"
    }

# Initialize Database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Configure CORS
origins = [settings.frontend_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not settings.debug else ["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class VisitLog(BaseModel):
    visit_type: str
    visit_tehsil: str
    product_recommended: str

# --- EXCEPTION HANDLERS ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact support."},
    )

# --- HEALTH CHECK ---
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.version,
        "ml_model_loaded": forecaster is not None
    }

# --- AUTH ENDPOINTS ---

@app.post("/api/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    logger.info(f"User logged in: {user['username']}")
    return {"access_token": access_token, "token_type": "bearer", "user": {
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "rep_id": user["rep_id"]
    }}

@app.get("/api/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "rep_id": current_user["rep_id"]
    }

# --- GEOLOCATION HELPER ---
def get_coordinates(district_name):
    """Converts district names from the database into Lat/Lon for Open-Meteo"""
    coords = {
        "Patna": (25.5941, 85.1376),
        "Jalgaon": (21.0077, 75.5626),
        "Hisar": (29.1492, 75.7217),
        "Varanasi": (25.3176, 82.9739),
        "Bharatpur": (27.2152, 77.4932)
    }
    # Default coordinates (Pune) if district not found
    return coords.get(district_name, (18.5204, 73.8567)) 

# --- THE ML INFERENCE ENGINE ---
def analyze_future_threat(lat, lon, current_inventory):
    """Tries Live API -> Falls back to Mock Data -> Caches by Lat/Lon"""
    cache_key = f"{lat}_{lon}"
    
    if cache_key not in weather_cache:
        logger.info(f"Attempting live weather API for coordinates {lat}, {lon}...")
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_mean,precipitation_sum&hourly=relative_humidity_2m&timezone=auto"
        
        try:
            # Simple rate limiting protection
            time.sleep(0.5) 
            response = requests.get(url, timeout=5)
            response.raise_for_status() 
            data = response.json()
            
            pred_temp = sum(data['daily']['temperature_2m_mean']) / 7
            pred_rainfall = sum(data['daily']['precipitation_sum'])
            pred_humidity = sum(data['hourly']['relative_humidity_2m']) / len(data['hourly']['relative_humidity_2m'])
            pred_ndvi = 0.58 if pred_rainfall < 5 else 0.75 
            
            logger.info(f"API Success for {lat}, {lon}.")
            weather_cache[cache_key] = (pred_temp, pred_humidity, pred_rainfall, pred_ndvi)
            
        except (requests.exceptions.RequestException, KeyError) as e:
            logger.warning(f"Weather API Error ({type(e).__name__}). Using Mock Data.")
            pred_temp, pred_humidity, pred_rainfall, pred_ndvi = 28.5, 68.0, 12.0, 0.65
            weather_cache[cache_key] = (pred_temp, pred_humidity, pred_rainfall, pred_ndvi)
            
    pred_temp, pred_humidity, pred_rainfall, pred_ndvi = weather_cache[cache_key]
    
    if forecaster: 
        features = np.array([[pred_temp, pred_humidity, pred_rainfall, pred_ndvi, current_inventory]])
        risk_score = float(forecaster.predict(features)[0]) 
    else:
        risk_score = 45.0 

    if risk_score > 75:
        urgency, threat_text = "critical", f"{risk_score:.0f}% Risk of Disease Outbreak Next Week"
    elif risk_score > 40:
        urgency, threat_text = "medium", f"{risk_score:.0f}% Risk of Pathogen Development"
    else:
        urgency, threat_text = "low", f"Optimal conditions. Only {risk_score:.0f}% biological risk."

    return {
        "urgency": urgency,
        "threat": threat_text,
        "metrics": {
            "forecast_temp": round(pred_temp, 1),
            "forecast_rain": round(pred_rainfall, 1),
            "predicted_risk": round(risk_score, 1)
        }
    }

# --- PRODUCTION DATA FUSION ENDPOINT ---
@app.get("/api/locations")
def get_locations(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT DISTINCT district FROM retailers
        UNION
        SELECT DISTINCT district FROM growers
    """)
    districts = [row['district'] for row in cursor.fetchall() if row['district']]
    return sorted(districts)

@app.get("/api/tehsils")
def get_tehsils(district: str, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT DISTINCT tehsil FROM retailers WHERE district = ?
        UNION
        SELECT DISTINCT tehsil FROM growers WHERE district = ?
    """, (district, district))
    tehsils = [row['tehsil'] for row in cursor.fetchall() if row['tehsil']]
    return sorted(tehsils)

@app.get("/api/routes")
def get_dashboard_data(district: str = None, tehsil: str = None, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not district or district == "All Locations":
        return []

    cursor = db.cursor()
    
    rep_filter = ""
    params = []
    if current_user["role"] != "admin" and current_user["rep_id"]:
        rep_filter = " AND r.territory_id IN (SELECT territory_id FROM territories WHERE rep_id = ?)"
        params.append(current_user["rep_id"])

    retailer_query = f"""
        SELECT 
            r.retailer_id, r.state, r.district, r.tehsil,
            i.sku_name, i.sku_qty, i.week_end_date
        FROM retailers r
        JOIN inventory i ON r.retailer_id = i.retailer_id
        WHERE i.week_end_date = (SELECT MAX(week_end_date) FROM inventory)
        {rep_filter}
    """
    
    r_params = list(params)
    if district and district != "All Locations":
        retailer_query += " AND r.district = ?"
        r_params.append(district)
    if tehsil and tehsil != "All Tehsils":
        retailer_query += " AND r.tehsil = ?"
        r_params.append(tehsil)
        
    cursor.execute(retailer_query, r_params)
    retailer_rows = cursor.fetchall()

    grower_query = """
        SELECT 
            grower_id, state, district, tehsil, 
            product_name, grower_farm_size, product_scan,
            product_scan_datetime
        FROM growers
        WHERE 1=1
    """
    g_params = []
    if district and district != "All Locations":
        grower_query += " AND district = ?"
        g_params.append(district)
    if tehsil and tehsil != "All Tehsils":
        grower_query += " AND tehsil = ?"
        g_params.append(tehsil)
    
    cursor.execute(grower_query, g_params)
    grower_rows = cursor.fetchall()
    
    dashboard_alerts = []

    # 1. PROCESS RETAILERS
    retailers_map = {}
    for row in retailer_rows:
        r_id = row['retailer_id']
        if r_id not in retailers_map:
            retailers_map[r_id] = {
                "retailer_id": row['retailer_id'],
                "state": row['state'],
                "district": row['district'],
                "tehsil": row['tehsil'],
                "inventory_date": row['week_end_date'],
                "products_list": [],
                "lowest_qty": 999,
                "lowest_product": ""
            }
        retailers_map[r_id]["products_list"].append(f"{row['sku_qty']} units of {row['sku_name']}")
        if row['sku_qty'] < retailers_map[r_id]["lowest_qty"]:
            retailers_map[r_id]["lowest_qty"] = row['sku_qty']
            retailers_map[r_id]["lowest_product"] = row['sku_name']

    for r_id, info in retailers_map.items():
        inventory_qty = info["lowest_qty"]
        product_name = info["lowest_product"]
        all_inventory_string = " | ".join(info["products_list"])
        
        lat, lon = get_coordinates(info['district'])
        ml_analysis = analyze_future_threat(lat, lon, inventory_qty)
        
        final_urgency = "critical" if (inventory_qty < 50 or ml_analysis["urgency"] == "critical") else ml_analysis["urgency"]
        
        dashboard_alerts.append({
            "id": f"RET_{r_id}",
            "urgency": final_urgency,
            "type": "Retailer",
            "name": f"Retailer {r_id}",
            "location": f"{info['district']}, {info['state']}",
            "tehsil": info['tehsil'],
            "threat": ml_analysis["threat"], 
            "action": f"Restock {product_name}",
            "recommended_product": product_name,
            "riskValue": "High Priority",
            "details": {
                "threatData": ml_analysis["threat"],
                "inventoryData": f"Full Stock Snapshot: {all_inventory_string}",
                "inventoryDate": info["inventory_date"],
                "closeProb": "Algorithmic Reorder Recommended",
                "script": f"Our ML model flagged a {ml_analysis['metrics']['predicted_risk']}% risk of disease in {info['tehsil']} next week. Looking at your profile, your stock of {product_name} is critical at just {inventory_qty} units. Let's process a backup order immediately.",
                "metrics": ml_analysis["metrics"]
            }
        })

    # 2. PROCESS GROWERS
    for row in grower_rows:
        g_id = row['grower_id']
        farm_size = row['grower_farm_size'] or 0
        last_product = row['product_name'] or "General Crop Care"
        last_activity = row['product_scan_datetime'] or "No recent scans"
        
        lat, lon = get_coordinates(row['district'])
        ml_analysis = analyze_future_threat(lat, lon, 100)
        
        final_urgency = ml_analysis["urgency"]
        if farm_size > 5 and ml_analysis["metrics"]["predicted_risk"] > 50:
            final_urgency = "critical"
            
        dashboard_alerts.append({
            "id": f"GRW_{g_id}",
            "urgency": final_urgency,
            "type": "Grower",
            "name": f"Grower {g_id}",
            "location": f"{row['district']}, {row['state']}",
            "tehsil": row['tehsil'],
            "threat": ml_analysis["threat"], 
            "action": f"Pitch {last_product} Protection",
            "recommended_product": last_product,
            "riskValue": f"{farm_size} Acres",
            "details": {
                "threatData": ml_analysis["threat"],
                "inventoryData": f"Farm Size: {farm_size} acres | Key Crop Segment: {last_product}",
                "activityDate": last_activity,
                "closeProb": "High Conversion Potential" if farm_size > 5 else "Nurture Lead",
                "script": f"Namaste Grower {g_id}, our weather station in {row['tehsil']} is showing conditions ripe for disease. Since you have {farm_size} acres of crop, we recommend applying {last_product} preventive spray this weekend to ensure a healthy harvest.",
                "metrics": ml_analysis["metrics"]
            }
        })

    dashboard_alerts.sort(key=lambda x: 0 if x['urgency'] == 'critical' else (1 if x['urgency'] == 'high' else 2))
    return dashboard_alerts

@app.post("/api/visits")
async def log_visit(visit: VisitLog, db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = db.cursor()
    cursor.execute("SELECT territory_id FROM territories WHERE rep_id = ?", (current_user["rep_id"],))
    row = cursor.fetchone()
    territory_id = row['territory_id'] if row else "TER_UNKNOWN"
    visit_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        cursor.execute("""
            INSERT INTO visits (rep_id, visit_date, territory_id, visit_tehsil, visit_type, product_recommended)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            current_user["rep_id"],
            visit_date,
            territory_id,
            visit.visit_tehsil,
            visit.visit_type.lower() + " meeting",
            visit.product_recommended
        ))
        db.commit()
        logger.info(f"Visit logged by {current_user['username']} for {visit.visit_tehsil}")
        return {"message": "Visit logged successfully", "date": visit_date}
    except Exception as e:
        logger.error(f"Error logging visit: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log visit record.")

@app.post("/api/chat")
async def chat_with_ai(request: Request, current_user: dict = Depends(get_current_user)):
    body = await request.json()
    user_message, context = body.get("message"), body.get("context")
    
    prompt = f"""
    You are the 'Syngenta Co-Pilot AI', an expert in agronomy, disease forecasting, and sales strategy.
    CUSTOMER CONTEXT: {json.dumps(context, indent=2)}
    USER QUESTION: {user_message}
    
    INSTRUCTIONS:
    1. Explain the "Why" and "How" behind recommendations using biological/weather factors and ML logic.
    2. Use provided metrics to justify.
    3. Keep it professional, data-driven, and actionable.
    4. Format with clear sections/bullet points.
    """
    
    try:
        response = llm_model.generate_content(prompt)
        return {"reply": response.text.strip()}
    except Exception as e:
        logger.error(f"AI Chat Error: {str(e)}")
        return {"reply": "I'm sorry, I'm having trouble connecting to the brain right now."}



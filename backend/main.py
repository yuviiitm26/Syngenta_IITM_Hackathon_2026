from email.policy import strict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import requests
import json
import joblib
import numpy as np
import time

import os
import google.generativeai as genai

# --- 1. CONFIGURATION & ENV LOADING ---
# If python-dotenv is not installed, we load the .env file manually
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "GEMINI_API_KEY":
    print("⚠️ Warning: GEMINI_API_KEY not found in environment or .env file.")
else:
    genai.configure(api_key=api_key)
    print("✅ GenAI Configured Successfully!")

llm_model = genai.GenerativeModel('gemini-2.5-flash')

# --- GLOBAL CACHE ---
# This stores the weather so we don't ask the API twice for the same district
weather_cache = {}
# --- 1. LOAD THE ML FORECASTER ---
try:
    forecaster = joblib.load("syngenta_enterprise_model.pkl")
    print("✅ Predictive ML Model Loaded Successfully!")
except FileNotFoundError:
    forecaster = None
    print("⚠️ Warning: syngenta_forecaster.pkl not found. Running with dummy data.")

app = FastAPI(title="Syngenta Enterprise API")

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = [frontend_url, "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if os.getenv("FRONTEND_URL") else ["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect("syngenta_prod.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- 2. GEOLOCATION HELPER ---
def get_coordinates(district_name):
    """Converts district names from the database into Lat/Lon for Open-Meteo"""
    coords = {
        "Patna": (25.5941, 85.1376),
        "Jalgaon": (21.0077, 75.5626),
        "Hisar": (29.1492, 75.7217),
        "Varanasi": (25.3176, 82.9739),
        "Bharatpur": (27.2152, 77.4932)
    }
    return coords.get(district_name, (18.5204, 73.8567)) # Default to Pune

# --- 3. THE ML INFERENCE ENGINE ---
def analyze_future_threat(lat, lon, current_inventory):
    """Tries Live API -> Falls back to Mock Data -> Caches by Lat/Lon"""
    
    # Create a unique cache key based on the exact coordinates
    cache_key = f"{lat}_{lon}"
    
    # 1. CHECK CACHE FIRST 
    if cache_key not in weather_cache:
        print(f"☁️ Attempting live weather API for coordinates {lat}, {lon}...")
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_mean,precipitation_sum&hourly=relative_humidity_2m&timezone=auto"
        
        try:
            time.sleep(0.5) 
            response = requests.get(url, timeout=5)
            response.raise_for_status() 
            data = response.json()
            
            pred_temp = sum(data['daily']['temperature_2m_mean']) / 7
            pred_rainfall = sum(data['daily']['precipitation_sum'])
            pred_humidity = sum(data['hourly']['relative_humidity_2m']) / len(data['hourly']['relative_humidity_2m'])
            pred_ndvi = 0.58 if pred_rainfall < 5 else 0.75 
            
            print(f"✅ API Success for {lat}, {lon}.")
            # Save real data using the coordinate key
            weather_cache[cache_key] = (pred_temp, pred_humidity, pred_rainfall, pred_ndvi)
            
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"⚠️ API Limit Reached ({type(e).__name__}). Using Mock Data.")
            
            pred_temp = 28.5       
            pred_humidity = 68.0   
            pred_rainfall = 12.0   
            pred_ndvi = 0.65       
            
            # Save mock data using the coordinate key
            weather_cache[cache_key] = (pred_temp, pred_humidity, pred_rainfall, pred_ndvi)
            
    # 2. LOAD VARIABLES FROM CACHE
    pred_temp, pred_humidity, pred_rainfall, pred_ndvi = weather_cache[cache_key]
    
    # 3. ASK THE ML MODEL
    if forecaster: 
        features = np.array([[pred_temp, pred_humidity, pred_rainfall, pred_ndvi, current_inventory]])
        # Convert NumPy float to native Python float for FastAPI JSON serialization
        risk_score = float(forecaster.predict(features)[0]) 
    else:
        risk_score = 45.0 

    # 4. FORMAT FOR REACT
    if risk_score > 75:
        urgency = "critical"
        threat_text = f"{risk_score:.0f}% Risk of Disease Outbreak Next Week"
    elif risk_score > 40:
        urgency = "medium"
        threat_text = f"{risk_score:.0f}% Risk of Pathogen Development"
    else:
        urgency = "low"
        threat_text = f"Optimal conditions. Only {risk_score:.0f}% biological risk."

    return {
        "urgency": urgency,
        "threat": threat_text,
        "metrics": {
            "forecast_temp": round(pred_temp, 1),
            "forecast_rain": round(pred_rainfall, 1),
            "predicted_risk": round(risk_score, 1)
        }
    }

    

def generate_pitch_script(retailer_name, risk_score, product, inventory, local_growers="Rajesh (Wheat, 5 acres), Amit (Wheat, 12 acres)"):
    """Uses GenAI to generate a B2B sales pitch AND a B2C Grower WhatsApp template"""
    
    if risk_score < 40:
        return f"Inventory looks stable at {inventory} units. No immediate action required."

    prompt = f"""
    You are an expert Syngenta agronomy sales assistant. 
    Our ML model predicts a {risk_score}% chance of a severe fungal outbreak next week at {retailer_name}.
    They only have {inventory} units of {product} left.
    
    Task 1 (The Push): Write a short 2-sentence sales pitch for our rep to convince the retailer to restock {product}.
    
    Task 2 (The Pull): We know local growers {local_growers} buy from this retailer. Write a 2-sentence WhatsApp message (with emojis) that the retailer can forward to these farmers to warn them about the weather and tell them to come buy {product} today.
    
    Format the output cleanly with 'REP PITCH:' and 'WHATSAPP FOR GROWERS:'
    """
    
    try:
        response = llm_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "System alert: High disease risk. Recommend restocking immediately."
    
# --- 4. PRODUCTION DATA FUSION ENDPOINT ---
@app.get("/api/locations")
def get_locations():
    """Returns a unique list of districts from both retailers and growers for the frontend filter"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT district FROM retailers
        UNION
        SELECT DISTINCT district FROM growers
    """)
    districts = [row['district'] for row in cursor.fetchall() if row['district']]
    conn.close()
    return sorted(districts)

@app.get("/api/tehsils")
def get_tehsils(district: str):
    """Returns unique list of tehsils for a specific district from both retailers and growers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT tehsil FROM retailers WHERE district = ?
        UNION
        SELECT DISTINCT tehsil FROM growers WHERE district = ?
    """, (district, district))
    tehsils = [row['tehsil'] for row in cursor.fetchall() if row['tehsil']]
    conn.close()
    return sorted(tehsils)

@app.get("/api/routes")
def get_dashboard_data(district: str = None, tehsil: str = None):
    """Queries data warehouse, groups data, and runs ML inference for retailers and growers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # --- RETAILER DATA ---
    retailer_query = """
        SELECT 
            r.retailer_id, r.state, r.district, r.tehsil,
            i.sku_name, i.sku_qty, i.week_end_date
        FROM retailers r
        JOIN inventory i ON r.retailer_id = i.retailer_id
        WHERE i.week_end_date = (SELECT MAX(week_end_date) FROM inventory)
    """
    
    r_params = []
    if district and district != "All Locations":
        retailer_query += " AND r.district = ?"
        r_params.append(district)
    if tehsil and tehsil != "All Tehsils":
        retailer_query += " AND r.tehsil = ?"
        r_params.append(tehsil)
        
    cursor.execute(retailer_query, r_params)
    retailer_rows = cursor.fetchall()

    # --- GROWER DATA ---
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
    
    conn.close()
    
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
        
        if not district or district == "All Locations":
            dashboard_alerts.append({
                "id": f"RET_{r_id}",
                "urgency": "low",
                "type": "Retailer",
                "name": f"Retailer {r_id}",
                "location": f"{info['district']}, {info['state']}",
                "threat": "Select location for analysis", 
                "action": f"Restock {product_name}",
                "riskValue": "Pending Analysis",
                "details": {
                    "threatData": "Analysis pending location selection",
                    "inventoryData": f"Full Stock Snapshot: {all_inventory_string}",
                    "inventoryDate": info["inventory_date"],
                    "closeProb": "---",
                    "script": "Please select a specific district to trigger the predictive threat analysis.",
                    "metrics": {"predicted_risk": 0}
                }
            })
            continue

        lat, lon = get_coordinates(info['district'])
        ml_analysis = analyze_future_threat(lat, lon, inventory_qty)
        
        final_urgency = "critical" if (inventory_qty < 50 or ml_analysis["urgency"] == "critical") else ml_analysis["urgency"]
        
        dashboard_alerts.append({
            "id": f"RET_{r_id}",
            "urgency": final_urgency,
            "type": "Retailer",
            "name": f"Retailer {r_id}",
            "location": f"{info['district']}, {info['state']}",
            "threat": ml_analysis["threat"], 
            "action": f"Restock {product_name}",
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
        scanned = row['product_scan']
        last_product = row['product_name'] or "General Crop Care"
        last_activity = row['product_scan_datetime'] or "No recent scans"
        
        if not district or district == "All Locations":
            dashboard_alerts.append({
                "id": f"GRW_{g_id}",
                "urgency": "low",
                "type": "Grower",
                "name": f"Grower {g_id}",
                "location": f"{row['district']}, {row['state']}",
                "threat": "Select location for analysis", 
                "action": f"Recommend {last_product}",
                "riskValue": f"{farm_size} Acres",
                "details": {
                    "threatData": "Analysis pending location selection",
                    "inventoryData": f"Farm Size: {farm_size} acres | Last Scanned: {last_product}",
                    "activityDate": last_activity,
                    "closeProb": "---",
                    "script": "Please select a specific district to trigger the predictive threat analysis.",
                    "metrics": {"predicted_risk": 0}
                }
            })
            continue

        lat, lon = get_coordinates(row['district'])
        # For growers, inventory level doesn't apply the same way, using a neutral 100 for threat analysis
        ml_analysis = analyze_future_threat(lat, lon, 100)
        
        # High urgency if farm is large and threat is medium+ OR if they haven't scanned recently and threat is high
        final_urgency = ml_analysis["urgency"]
        if farm_size > 5 and ml_analysis["metrics"]["predicted_risk"] > 50:
            final_urgency = "critical"
            
        dashboard_alerts.append({
            "id": f"GRW_{g_id}",
            "urgency": final_urgency,
            "type": "Grower",
            "name": f"Grower {g_id}",
            "location": f"{row['district']}, {row['state']}",
            "threat": ml_analysis["threat"], 
            "action": f"Pitch {last_product} Protection",
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

    # Sort critical alerts to the top
    dashboard_alerts.sort(key=lambda x: 0 if x['urgency'] == 'critical' else (1 if x['urgency'] == 'high' else 2))
    
    return dashboard_alerts

@app.post("/api/chat")
async def chat_with_ai(request: Request):
    """Conversational AI to explain predictions and recommendations"""
    body = await request.json()
    user_message = body.get("message")
    context = body.get("context") # Retailer or Grower specific data
    
    prompt = f"""
    You are the 'Syngenta Co-Pilot AI', an expert in agronomy, disease forecasting, and sales strategy.
    
    CUSTOMER CONTEXT:
    {json.dumps(context, indent=2)}
    
    USER QUESTION:
    {user_message}
    
    INSTRUCTIONS:
    1. Explain the "Why" (the biological/weather factors) and the "How" (the ML prediction logic) behind the recommendations.
    2. Use the provided metrics (temperature, rainfall, risk score) to justify your answer.
    3. Keep it professional, data-driven, and actionable.
    4. If the user asks about something not in the context, politely steer them back to the agronomic threat analysis.
    5. Format your response with clear sections or bullet points for readability.
    """
    
    try:
        response = llm_model.generate_content(prompt)
        return {"reply": response.text.strip()}
    except Exception as e:
        return {"reply": f"I'm sorry, I'm having trouble connecting to the brain: {str(e)}"}

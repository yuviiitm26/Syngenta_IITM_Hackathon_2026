import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

print("=========================================")
print("🧬 INITIATING ENTERPRISE FUSION MODEL...")
print("=========================================")

# 1. GENERATE SYNTHETIC HISTORICAL DATA (Combining External + Internal)
np.random.seed(42)
num_samples = 10000

# -- EXTERNAL FEATURES (Environmental) --
pred_temp = np.random.uniform(15.0, 40.0, num_samples)     
pred_humidity = np.random.uniform(40.0, 95.0, num_samples) 
pred_rainfall = np.random.uniform(0.0, 50.0, num_samples)  
pred_ndvi = np.random.uniform(0.3, 0.9, num_samples)       

# -- INTERNAL FEATURES (CRM & Supply Chain) --
# Simulating the data from your 'retailer_inventory_weekly.csv' (Ranges from 0 to 500 units)
current_inventory = np.random.randint(0, 500, num_samples)

# 2. DEFINE THE BUSINESS GROUND TRUTH (Action Priority Score)
def calculate_business_urgency(row):
    urgency = 0 
    
    # PART A: Agronomic Threat (The Weather/NDVI Factor)
    agronomic_risk = 0
    if 22 <= row['pred_temp'] <= 30: agronomic_risk += 30
    if row['pred_humidity'] > 75: agronomic_risk += 25
    if row['pred_rainfall'] > 15: agronomic_risk += 15
    if row['pred_ndvi'] < 0.60: agronomic_risk += 20
    
    # PART B: Business Vulnerability (The Internal Data Factor)
    # If the agronomic risk is high, but they have plenty of inventory, urgency drops!
    if agronomic_risk > 60:
        if row['current_inventory'] < 50:
            urgency = 95 # CRITICAL: High Risk + Out of Stock
        elif row['current_inventory'] < 150:
            urgency = 75 # MEDIUM: High Risk + Low Stock
        else:
            urgency = 30 # LOW: High Risk, but they are fully stocked. No sales opportunity.
    else:
        # If there is no disease risk, urgency is purely based on routine restocking
        if row['current_inventory'] < 50:
            urgency = 40 # Routine restock
        else:
            urgency = 10 # All good
            
    # Add minor ML noise
    urgency += np.random.uniform(-5, 5)
    return max(0, min(100, urgency))

print("Fusing environmental data with internal inventory levels...")
df = pd.DataFrame({
    'pred_temp': pred_temp,
    'pred_humidity': pred_humidity,
    'pred_rainfall': pred_rainfall,
    'pred_ndvi': pred_ndvi,
    'current_inventory': current_inventory # <-- The New Internal Feature
})

df['action_priority_score'] = df.apply(calculate_business_urgency, axis=1)

# 3. PREPARE & TRAIN XGBOOST
# Notice we are now passing 5 features into the model!
X = df[['pred_temp', 'pred_humidity', 'pred_rainfall', 'pred_ndvi', 'current_inventory']]
y = df['action_priority_score']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training Enterprise XGBoost Regressor...")
model = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    eval_metric='mae'
)

model.fit(X_train, y_train)

# 4. EVALUATE & EXPORT
predictions = model.predict(X_test)
mae = mean_absolute_error(y_test, predictions)

print("\n📊 ENTERPRISE MODEL METRICS:")
print(f"Mean Absolute Error: Off by roughly {mae:.2f} points on the urgency scale.")

model_filename = 'syngenta_enterprise_model.pkl'
joblib.dump(model, model_filename)
print("=========================================")
print(f"✅ SUCCESS: Enterprise Model saved as '{model_filename}'")
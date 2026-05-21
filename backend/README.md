# Syngenta Co-Pilot: Enterprise Backend

The Syngenta Co-Pilot Backend is a high-performance FastAPI service that powers predictive disease forecasting, data fusion for field sales, and GenAI-driven sales intelligence.

## 🚀 Key Features


- **Predictive ML Intelligence**: Forecasts fungal disease risks using a trained Scikit-learn model based on live weather data (temperature, humidity, precipitation) and NDVI proxies.
- **GenAI Sales Copilot**: Leverages Google Gemini to generate context-aware B2B sales pitches for retailers and B2C WhatsApp templates for growers.
- **Production Data Fusion**: Harmonizes data across Retailer Inventories, Grower Profiles, and Field Visit Logs via an optimized SQLite Data Warehouse.
- **Real-time Weather Integration**: Connects with Open-Meteo API for hyper-local weather forecasting based on territory coordinates.
- **Interactive AI Chat**: Provides a RAG-lite conversational interface for reps to drill down into risk metrics and agronomic justifications.

## 🛠 Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: SQLite3
- **Machine Learning**: Scikit-learn, Joblib, NumPy, Pandas
- **Generative AI**: Google Gemini Pro (`google-generativeai`)
- **API Client**: Requests

## 📂 Project Structure

- `main.py`: The core FastAPI application containing all production endpoints.
- `auth.py`: Authentication logic and JWT handling.
- `database.py`: Centralized database connection and initialization logic.
- `data_setup.py`: ETL script that builds the SQLite data warehouse from raw CSVs.
- `train_model.py`: Training script for the disease outbreak prediction model.
- `syngenta_enterprise_model.pkl`: The serialized ML forecaster.
- `syngenta_prod.db`: The live production database (auto-initialized).
- `.env`: Environment configuration (API keys).

## ⚙️ Setup & Installation

### 1. Environment Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
JWT_SECRET_KEY=your_secret_key_here (optional)
```

### 3. Initialize the Data Warehouse
Load the hackathon datasets into the SQLite database:
```bash
python data_setup.py
```

### 4. Run the API Server
```bash
uvicorn main:app --reload
```
The server will start at `http://localhost:8000`. Note: The `users` table is automatically initialized on startup with default users.

## 📡 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/login` | `POST` | User login to get JWT token. |
| `/api/me` | `GET` | Get current user profile. |
| `/api/locations` | `GET` | Returns list of unique districts for filtering. |
| `/api/tehsils` | `GET` | Returns tehsils for a specific district. |
| `/api/routes` | `GET` | The "Brain" endpoint - performs data fusion & ML inference. |
| `/api/chat` | `POST` | Context-aware AI assistant for risk explanation. |

## 🔑 Default Users

- **Admin**: `admin` / `syngenta2026`
- **Sales Rep**: `rep1` / `syngenta2026`

---
© 2026 Syngenta IITM Hackathon

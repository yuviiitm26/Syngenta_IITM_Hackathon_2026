# Syngenta Co-Pilot: Enterprise Predictive Sales Dashboard

Syngenta Co-Pilot is an advanced AI-driven platform built for the Syngenta IITM Hackathon 2026. It empowers field representatives with predictive disease forecasting, real-time inventory insights, and GenAI-powered sales strategies to optimize regional impact and grower engagement.

## 🌟 Project Overview

This project bridges the gap between raw agronomic data and actionable sales intelligence. By fusing local weather forecasts with historical retailer inventory and grower activity, the system identifies high-risk territories and provides field reps with "Next Best Action" recommendations.

## 🏗 System Architecture

The project is divided into two main components:

- **[Backend (FastAPI)](./backend/README.md)**: Handles data warehouse management, ML inference for disease risk, and GenAI orchestration for sales intelligence.
- **[Frontend (React)](./frontend/README.md)**: A modern, high-fidelity dashboard for route prioritization, profile deep-dives, and AI-assisted visit logging.

## ⚡️ Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Or install dependencies listed in backend/README.md
python data_setup.py
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Core Innovations

1.  **Outbreak Forecaster**: Uses a Scikit-learn model to predict fungal disease risks by analyzing live 7-day weather forecasts.
2.  **Contextual AI Pitching**: Automatically drafts B2B and B2C communication based on the specific threat level and inventory criticalities.
3.  **Unified Data Fusion**: Integrates fragmented CSV data into a high-performance SQLite warehouse, enabling real-time district/tehsil level insights.
4.  **Temporal Context**: Displays "Stock as of" and "Last Activity" dates across all profiles to ensure reps work with the latest information.

---
© 2026 Syngenta IITM Hackathon

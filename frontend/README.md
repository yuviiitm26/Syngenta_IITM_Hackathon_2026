# Syngenta Co-Pilot: Field Sales Interface

A modern, high-fidelity React dashboard designed for Syngenta field representatives. This application fuses predictive agronomic data with sales CRM metrics to prioritize daily routes and drive smarter retailer/grower engagements.

## ✨ Features

- **Dynamic Territory Routing**: Prioritize visits based on real-time disease risk and inventory stockouts.
- **Data Fusion Dashboard**: Seamlessly combines biological threat analysis, financial context, and inventory snapshots.
- **Regional Alert System**: Live banner for urgent regional weather warnings (e.g., heavy rainfall or pest hatch alerts).
- **Multi-level Filtering**: Drills down by District and Tehsil to manage specific territories.
- **AI Next Best Action**: Instant recommendations on whether to "Pitch Protection" or "Log Reorder".
- **Intelligent Sales Scripting**: Auto-generated scripts for rep pitches and grower WhatsApp messages.
- **Interactive Metric Explanation**: Built-in AI chat slide-over to explain the "Why" behind risk predictions.

## 🛠 Tech Stack

- **Framework**: React 19 (Vite)
- **Styling**: TailwindCSS 4 (Vanilla CSS architecture)
- **Icons**: Lucide React
- **State Management**: React Hooks (useState, useEffect)
- **Networking**: Fetch API with real-time backend synchronization

## 📂 Project Structure


- `src/App.jsx`: The primary dashboard component and orchestration layer.
- `src/App.css`: Custom modern styling and Tailwind extensions.
- `public/`: Assets including SVG icons and brand assets.

## ⚙️ Setup & Installation

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

### 3. Connection Config
The frontend expects the backend to be running at `http://localhost:8000`. Ensure the FastAPI server is live to enable data fetching and AI chat features.

---
© 2026 Syngenta IITM Hackathon

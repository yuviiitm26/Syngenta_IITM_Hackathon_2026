# --- MASTER SERVER RUNNER ---
if __name__ == "__main__":
    import uvicorn
    import os
    
    print("=========================================")
    print("🚀 Booting Syngenta Cloud Intelligence...")
    print("=========================================")
    
    # Optional Hackathon Flex: Auto-run your database scripts before the server starts!
    # If you want the DB to rebuild fresh every time you start the app, uncomment these:
    # os.system("python build_data_warehouse.py")
    # os.system("python create_view.py")
    
    print("🟢 Server Live on http://localhost:8000")
    
    # This launches the FastAPI server programmatically
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
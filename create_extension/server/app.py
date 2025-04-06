from fastapi import FastAPI, Request, HTTPException
import uvicorn
import os
import json
from datetime import datetime

app = FastAPI()

DATA_DIR = "tab_data"
os.makedirs(DATA_DIR, exist_ok=True)

def store_tab_data(data):
    try:
        # Create a timestamp and add it to the data
        timestamp = datetime.now().isoformat()
        data['timestamp'] = timestamp
        
        # Determine filename based on whether multiple tabs are sent
        if 'tabsData' in data:
            filename = f"tabs_{timestamp.replace(':', '-')}.json"
        else:
            tab_data = data.get('tabData', {})
            url_part = tab_data.get('url', 'unknown').replace('://', '_').replace('/', '_')
            if len(url_part) > 50:
                url_part = url_part[:50]
            filename = f"tab_{timestamp.replace(':', '-')}_{url_part}.json"
        
        filepath = os.path.join(DATA_DIR, filename)
        
        # Save the full tab data to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Update the latest.json file for easy retrieval
        latest = {
            'timestamp': timestamp,
            'filename': filename,
            'dataType': 'tabsData' if 'tabsData' in data else 'tabData'
        }
        with open(os.path.join(DATA_DIR, 'latest.json'), 'w', encoding='utf-8') as f:
            json.dump(latest, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print("Error storing tab data:", e)
        return False

@app.post("/active_tab")
async def receive_tab_data(request: Request):
    # Verify Content-Type header
    if "application/json" not in request.headers.get("Content-Type", ""):
        raise HTTPException(status_code=400, detail="Content-Type must be application/json")
    try:
        data = await request.json()
    except Exception as e:
        print("JSON parsing error:", e)
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Debug: log the incoming payload
    print("Received data:", data)
    
    if not data or ('tabData' not in data and 'tabsData' not in data):
        print("Invalid data format:", data)
        raise HTTPException(status_code=400, detail="Invalid data format")
    
    success = store_tab_data(data)
    if success:
        return {"success": True, "message": "Tab data received successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to store tab data")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)

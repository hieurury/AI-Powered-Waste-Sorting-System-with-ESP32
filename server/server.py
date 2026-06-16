import os
import time
import asyncio
import requests
import logging
from datetime import datetime
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from pymongo import MongoClient

# Flask Web Server
from flask import Flask, send_from_directory, request, jsonify

# Terminal UI libraries
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Windows Geolocation library
import winsdk.windows.devices.geolocation as wdg

# --- SYSTEM CONFIGURATION ---
WEB_PORT = int(os.getenv("WEB_PORT", 5000))

# Dynamic paths based on the location of server.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")
MODEL_PATH = os.path.join(BASE_DIR, "model.h5") # Updated model name

# --- MONGODB CONFIGURATION ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/waste_management")
DB_NAME = os.getenv("DB_NAME", "WasteManagementDB")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "WasteRecords")

console = Console()
os.makedirs(IMAGE_DIR, exist_ok=True)

CLASS_NAMES = {
    0: "METAL", 
    1: "PAPER", 
    2: "PLASTIC"
}

# --- FLASK WEB SERVER SETUP ---
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/images/<path:filename>')
def serve_image(filename):
    """API Endpoint to serve static images to Web/App"""
    return send_from_directory(IMAGE_DIR, filename)

@app.route('/upload', methods=['POST'])
def upload_image():
    """API Endpoint to receive Image from ESP32 via Wi-Fi"""
    global stats
    
    # 1. Receive binary data from ESP32
    image_data = request.data
    if not image_data:
        return jsonify({"status": "error", "message": "No image data received"}), 400

    draw_ui(f"Receiving image via Wi-Fi ({len(image_data)} bytes)...")

    # 2. Save the image file
    filename_only = datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
    relative_db_path = f"images/{filename_only}" 
    abs_filepath = os.path.join(IMAGE_DIR, filename_only)
    
    with open(abs_filepath, "wb") as f:
        f.write(image_data)
    
    draw_ui("Analyzing AI and fetching GPS Location...")
    
    # 3. Analyze with AI & Get Location
    result, conf = predict_image(abs_filepath)
    current_location = get_dynamic_location()
    
    # 4. Save to Database
    timestamp = datetime.now()
    if collection is not None:
        record = {
            "waste_type": result,
            "confidence": conf,
            "timestamp": timestamp,
            "location": current_location,
            "image_path": relative_db_path
        }
        collection.insert_one(record)
    
    # 5. Update statistics and UI
    stats[result] += 1
    
    result_color = "yellow" if result == "METAL" else ("green" if result == "PAPER" else "blue")
    result_panel = Panel.fit(
        f"Result: [bold {result_color}]{result}[/]\nConfidence: {conf:.2f}%\nLocation: {current_location}\nStatus: Saved to Database!",
        title="CLASSIFICATION RESULT", border_style=result_color
    )
    
    draw_ui("Waiting for the next object via Wi-Fi...", result_panel=result_panel)
    
    # Return response to ESP32 indicating success
    return jsonify({"status": "success", "result": result, "confidence": float(conf)}), 200


# --- FUNCTION: GET DYNAMIC WINDOWS LOCATION ---
async def get_windows_location_async():
    try:
        access_status = await wdg.Geolocator.request_access_async()
        if access_status == wdg.GeolocationAccessStatus.ALLOWED:
            locator = wdg.Geolocator()
            pos = await locator.get_geoposition_async()
            lat = pos.coordinate.point.position.latitude
            lon = pos.coordinate.point.position.longitude
            return lat, lon
        else:
            return None
    except Exception:
        return None

def get_dynamic_location():
    """Fetch coordinates and translate to city name"""
    coords = asyncio.run(get_windows_location_async())
    if coords:
        lat, lon = coords
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            headers = {'User-Agent': 'WasteClassificationIoT/1.0'}
            res = requests.get(url, headers=headers, timeout=5).json()
            if 'address' in res:
                addr = res['address']
                city = addr.get('city', addr.get('state', addr.get('county', 'Unknown')))
                return f"{city} (Lat: {lat:.4f}, Lon: {lon:.4f})"
            return f"Lat: {lat:.4f}, Lon: {lon:.4f}"
        except:
            return f"Lat: {lat:.4f}, Lon: {lon:.4f}"
    return "Unknown (Please enable Location permissions on Windows)"


# --- FUNCTION: CLEAR SCREEN ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# --- HELPER FUNCTIONS ---
def predict_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0
    predictions = model.predict(img_array, verbose=0)
    class_index = np.argmax(predictions[0])
    confidence = float(np.max(predictions[0]) * 100)
    return CLASS_NAMES[class_index], confidence

def draw_ui(status_message, result_panel=None):
    clear_screen()
    console.print(Panel.fit("[bold cyan]SMART IoT WASTE CLASSIFICATION SYSTEM[/]", border_style="cyan"))
    
    console.print(f"> [bold magenta]Image Server URL:[/] [link]http://localhost:{WEB_PORT}/[/link]<filename>\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Waste Type", justify="center")
    table.add_column("Collected Count", justify="center")
    
    table.add_row("[yellow]METAL[/]", f"[bold]{stats['METAL']}[/]")
    table.add_row("[green]PAPER[/]", f"[bold]{stats['PAPER']}[/]")
    table.add_row("[blue]PLASTIC[/]", f"[bold]{stats['PLASTIC']}[/]")
    
    console.print(table)
    
    if result_panel:
        console.print(result_panel)
        
    console.print(f"\n[blink bold green]{status_message}[/]")


# --- INITIALIZATION LOGIC & ENTRY POINT ---
if __name__ == "__main__":
    clear_screen()
    console.print("[bold yellow]Connecting to MongoDB...[/]")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        client.admin.command('ping') 
        console.print("[bold green]-> Successfully connected to MongoDB![/]")
    except Exception as e:
        console.print(f"[bold red]-> MongoDB connection error: {e}[/]")
        console.print("[bold yellow]Note: System will run but data won't be saved to DB.[/]")
        collection = None

    stats = {"METAL": 0, "PAPER": 0, "PLASTIC": 0}
    if collection is not None:
        for key in stats.keys():
            stats[key] = collection.count_documents({"waste_type": key})

    console.print("\n[bold yellow]Loading AI model...[/]")
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        console.print("[bold green]-> AI model loaded successfully![/]\n")
    except Exception as e:
        console.print(f"[bold red]-> ERROR loading AI: {e}[/]")
        exit()

    draw_ui("Waiting for the next object via Wi-Fi...")
    
    # Start the Flask Web Server in the main thread
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)
import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CarAssistantGateway")

# Konfiguracja ze zmiennych środowiskowych
MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
TORQUE_USER_EMAIL = os.getenv("TORQUE_USER_EMAIL", "")

# Aktualny stan telemetrii
current_state: Dict[str, Any] = {
    "rpm": 0.0,
    "speed": 0.0,
    "coolant_temp": 0.0,
    "fuel_level": 0.0,
    "battery_voltage": 0.0,
    "engine_load": 0.0,
    "ignition": False,
    "latitude": None,
    "longitude": None,
    "session": None,
    "timestamp": 0
}

# WebSockets Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Wyślij aktualny stan po podłączeniu
        await websocket.send_json(current_state)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
mqtt_client = None

# Obsługa MQTT
def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Połączono z brokerem MQTT")
        publish_discovery()
    else:
        logger.error(f"Błąd połączenia z MQTT, kod: {rc}")

def init_mqtt():
    global mqtt_client
    try:
        mqtt_client = mqtt.Client(client_id="car_assistant_gateway")
        if MQTT_USER and MQTT_PASSWORD:
            mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.connect_async(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"Nie udało się zainicjować MQTT: {e}")

def get_device_info():
    return {
        "identifiers": ["car_assistant_torque_pro"],
        "name": "Samochód (Torque Pro)",
        "manufacturer": "No Stress IT",
        "model": "OBD2 Live Gateway"
    }

def publish_discovery():
    if not mqtt_client:
        return
    
    device = get_device_info()
    base_topic = "homeassistant"
    
    sensors = [
        {"id": "rpm", "type": "sensor", "name": "Engine RPM", "unit": "RPM", "val_tpl": "{{ value_json.rpm }}", "icon": "mdi:engine"},
        {"id": "speed", "type": "sensor", "name": "Vehicle Speed", "unit": "km/h", "val_tpl": "{{ value_json.speed }}", "icon": "mdi:speedometer"},
        {"id": "coolant_temp", "type": "sensor", "name": "Coolant Temperature", "unit": "°C", "val_tpl": "{{ value_json.coolant_temp }}", "icon": "mdi:coolant-temperature", "dev_class": "temperature"},
        {"id": "fuel_level", "type": "sensor", "name": "Fuel Level", "unit": "%", "val_tpl": "{{ value_json.fuel_level }}", "icon": "mdi:gas-station"},
        {"id": "battery_voltage", "type": "sensor", "name": "Battery Voltage", "unit": "V", "val_tpl": "{{ value_json.battery_voltage }}", "icon": "mdi:car-battery", "dev_class": "voltage"},
        {"id": "engine_load", "type": "sensor", "name": "Engine Load", "unit": "%", "val_tpl": "{{ value_json.engine_load }}", "icon": "mdi:gauge"},
    ]
    
    for s in sensors:
        topic = f"{base_topic}/{s['type']}/car_assistant_{s['id']}/config"
        payload = {
            "name": s["name"],
            "unique_id": f"car_assistant_{s['id']}",
            "state_topic": "car/telemetry/state",
            "value_template": s["val_tpl"],
            "unit_of_measurement": s["unit"],
            "icon": s["icon"],
            "device": device
        }
        if "dev_class" in s:
            payload["device_class"] = s["dev_class"]
        mqtt_client.publish(topic, json.dumps(payload), retain=True)

    # Ignition (Binary Sensor)
    ig_topic = f"{base_topic}/binary_sensor/car_assistant_ignition/config"
    ig_payload = {
        "name": "Ignition Status",
        "unique_id": "car_assistant_ignition",
        "state_topic": "car/telemetry/state",
        "value_template": '{{ "ON" if value_json.ignition else "OFF" }}',
        "payload_on": "ON",
        "payload_off": "OFF",
        "device_class": "running",
        "icon": "mdi:key-wireless",
        "device": device
    }
    mqtt_client.publish(ig_topic, json.dumps(ig_payload), retain=True)
    
    # GPS Tracker
    gps_topic = f"{base_topic}/device_tracker/car_assistant_gps/config"
    gps_payload = {
        "name": "Car Location",
        "unique_id": "car_assistant_gps",
        "state_topic": "car/telemetry/state",
        "json_attributes_topic": "car/telemetry/state",
        "icon": "mdi:car",
        "device": device
    }
    mqtt_client.publish(gps_topic, json.dumps(gps_payload), retain=True)

def publish_state():
    if mqtt_client:
        mqtt_client.publish("car/telemetry/state", json.dumps(current_state))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_mqtt()
    yield
    # Shutdown
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

app = FastAPI(title="Car Assistant Gateway", lifespan=lifespan)
_jinja_loader = FileSystemLoader("app/templates")
_jinja_env = Environment(loader=_jinja_loader, auto_reload=False)
def _render(name, context):
    return _jinja_env.get_template(name).render(**context)

@app.get("/")
async def get_dashboard(request: Request):
    html = _render("index.html", {"request": request})
    return HTMLResponse(content=html)

def safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

@app.get("/api/torque")
@app.get("/torque")
async def torque_endpoint(request: Request):
    query_params = request.query_params
    eml = query_params.get("eml", "")
    
    if TORQUE_USER_EMAIL and eml != TORQUE_USER_EMAIL:
        logger.warning(f"Odmowa dostępu dla email: {eml}")
        # Nadal musimy zwrócić OK! lub zignorować dane
        return Response(content="OK!", media_type="text/plain", status_code=200)

    # Odczyt parametrów z fallbackiem do aliasów
    rpm_str = query_params.get("k0c") or query_params.get("kc")
    speed_str = query_params.get("k0d") or query_params.get("kd")
    coolant_str = query_params.get("k05") or query_params.get("k5")
    fuel_str = query_params.get("k2f") or query_params.get("kff1201")
    battery_str = query_params.get("kff1005") or query_params.get("k42") or query_params.get("kff1237")
    load_str = query_params.get("k04") or query_params.get("k4")
    
    rpm = safe_float(rpm_str) if rpm_str is not None else current_state["rpm"]
    speed = safe_float(speed_str) if speed_str is not None else current_state["speed"]
    battery = safe_float(battery_str) if battery_str is not None else current_state["battery_voltage"]
    
    # Logika zapłonu: silnik pracuje (RPM>0) lub napięcie wysokie (>13.0V = ładowanie/uruchomiony)
    ignition = True if (rpm > 0 or battery > 13.0) else False

    # Aktualizacja stanu
    current_state.update({
        "rpm": rpm,
        "speed": speed,
        "coolant_temp": safe_float(coolant_str) if coolant_str is not None else current_state["coolant_temp"],
        "fuel_level": safe_float(fuel_str) if fuel_str is not None else current_state["fuel_level"],
        "battery_voltage": battery,
        "engine_load": safe_float(load_str) if load_str is not None else current_state["engine_load"],
        "ignition": ignition,
        "session": query_params.get("session", current_state["session"]),
        "timestamp": int(query_params.get("time", 0))
    })
    
    lat = query_params.get("lat")
    lon = query_params.get("lon")
    if lat and lon:
        current_state["latitude"] = safe_float(lat)
        current_state["longitude"] = safe_float(lon)

    # Asynchroniczne zadania: MQTT i WebSockets
    publish_state()
    asyncio.create_task(manager.broadcast(current_state))

    # Zawsze zwracaj tekst OK! z kodem 200
    return Response(content="OK!", media_type="text/plain", status_code=200)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/status")
async def get_status():
    return current_state

# Car Assistant - Torque Pro Telemetry Gateway

**Car Assistant Gateway** is a production-ready Python microservice (built with FastAPI) designed to bridge the **Torque Pro** mobile app (reading OBD-II telemetry via adapters like vLinker) with the **Home Assistant** ecosystem and a dedicated web dashboard.

The project ingests real-time vehicle telemetry, streams it without latency via WebSockets to a modern dark-mode browser interface, and automatically registers and updates vehicle entities in your Smart Home setup using **MQTT Auto-Discovery**.

---

## 🚀 Key Features

* 📡 **Torque Pro Web Endpoint**: Seamlessly receives and maps web log uploads sent from the Torque app (fully compliant with the protocol specifications, returning plain-text `OK!`).
* ⚡ **Real-Time WebSockets**: Instant data streaming to the local web dashboard within milliseconds of OBD-II capture—zero page refreshes required.
* 🏠 **Home Assistant MQTT Discovery**: Out-of-the-box MQTT integration. Upon startup, the service self-registers the device in Home Assistant (*"Car (Torque Pro)"*) and creates entities such as Speed, RPM, Fuel Level, Battery Voltage, and Ignition status.
* 🎨 **Premium Dark Dashboard**: Sleek, automotive-inspired dark-mode UI with smooth CSS gauges (`conic-gradient`) mimicking digital instrument clusters in modern cars.
* 🐳 **Docker-Ready**: Fully containerized for instant deployment on Proxmox LXC/VMs, VPS servers, or Raspberry Pi.

---

## 🏗️ Architecture & Tech Stack

* **Backend:** Python 3.11, FastAPI, Uvicorn
* **IoT Protocol:** Eclipse Mosquitto, Paho-MQTT
* **Frontend:** HTML5, Vanilla JavaScript, CSS3 (zero external heavy UI dependencies like React or Vue)
* **Containerization:** Docker & Docker Compose
* **Reverse Proxy:** Pre-configured Nginx template (Reverse Proxy + SSL/TLS support)

---

## 📦 Project Structure

```text
├── app/
│   ├── main.py              # Main FastAPI, MQTT, and WebSocket logic
│   └── templates/
│       └── index.html       # Dark-mode dashboard (Jinja2)
├── docker-compose.yml       # Environment setup (App + optional Mosquitto MQTT broker)
├── Dockerfile               # Docker image definition
├── nginx_car.conf           # Sample Nginx virtual host configuration
├── requirements.txt         # Python dependencies
├── test_emulator.py         # Car driving telemetry simulator for local testing
└── README.md                # Documentation

```

---

## ⚙️ Deployment & Configuration (Proxmox / Linux)

Getting the service up and running takes just a few commands.

### Prerequisites:

* A container runtime environment: **Docker** and **Docker Compose** installed.
* *(Optional)* An existing MQTT broker (though a ready-to-use `mosquitto` container is included in `docker-compose.yml`).

### Step 1: Clone the repository

```bash
git clone https://github.com/YourUsername/car-assistant.git
cd car-assistant

```

### Step 2: Launch with Docker Compose

```bash
docker compose up -d --build

```

The application will build and start listening on port `8000`.

### Step 3: Configure Torque Pro on your mobile device

In the Torque Pro application, navigate to:
`Settings -> Data Logging & Upload -> Webserver Settings`

* Enter the endpoint URL: `[https://your-domain.com/api/torque](https://your-domain.com/api/torque)` (if using a Reverse Proxy) or your local server IP (if on LAN).
* Set your preferred upload interval (e.g., every 1 second).

---

## 🧪 Testing with the Emulator

No need to sit in your car to test the dashboard!

The repository includes a built-in driving simulator that generates smooth telemetry curves (gear shifting, acceleration, coolant warm-up, etc.).

To launch the emulator (requires local Python environment):

```bash
pip install requests
python test_emulator.py --url http://localhost:8000/api/torque

```

Once started, open `http://localhost:8000/` in your browser—the dashboard will immediately spring to life as gauges react to the simulated telemetry.

---

## 🌐 Nginx Configuration (Reverse Proxy)

Running the application behind Nginx is recommended—particularly for SSL/HTTPS termination, which is required by many modern browsers and mobile devices for secure script execution and geolocation features.

A sample Nginx configuration with proper WebSocket upgrade headers is provided in `nginx_car.conf`. Make sure to update IP addresses, target ports, SSL certificate paths, and your domain name (e.g., `car.example.com`).

---

## 👨‍💻 Environment Variables (ENV)

Customize the microservice behavior via `docker-compose.yml` or an `.env` file:

* `MQTT_HOST`: Hostname or IP of the MQTT broker (defaults to `127.0.0.1` or service container name).
* `MQTT_PORT`: MQTT broker port (`1883`).
* `MQTT_USER` / `MQTT_PASSWORD`: MQTT authentication credentials (leave blank if authentication is disabled).
* `TORQUE_USER_EMAIL`: Torque account email for payload verification *(optional; validates incoming request headers/payload against this value)*.

---

## ⚖️ License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute it as needed.

# Car Assistant - Torque Pro Telemetry Gateway

**Car Assistant Gateway** to produkcyjny mikroserwis w języku Python (oparty o FastAPI), który służy jako pomost między aplikacją mobilną **Torque Pro** (odczytującą dane z OBD-II np. przez vLinker) a ekosystemem **Home Assistant** oraz dedykowanym dashboardem WWW.

Projekt pozwala na odbieranie telemetrii pojazdu na żywo, rozsyłanie jej bez opóźnień za pośrednictwem WebSockets do nowoczesnego interfejsu przeglądarkowego w ciemnym motywie (Dark Mode) oraz automatyczne dodawanie i aktualizowanie encji samochodu w systemie Smart Home poprzez protokół **MQTT Auto-Discovery**.

---

## 🚀 Główne możliwości i funkcje

- 📡 **Endpoint dla Torque Pro**: Bezpośredni odbiór i mapowanie logów webowych wysyłanych z aplikacji Torque (w tym zgodność z wymaganym protokołem, zwracanie czystego tekstu `OK!`).
- ⚡ **WebSockets na Żywo**: Odświeżanie danych na lokalnym dashboardzie WWW ułamki sekund po ich zrzuceniu z OBD-II bez przeładowania strony.
- 🏠 **Home Assistant MQTT Discovery**: Gotowa konfiguracja MQTT. Serwer po uruchomieniu samodzielnie zgłasza urządzenie w Home Assistant ("Samochód (Torque Pro)") dodając encje takie jak Prędkość, Obroty, Poziom paliwa, Napięcie akumulatora i status Zapłonu.
- 🎨 **Dashboard Premium**: Interfejs w stylistyce dark-mode z płynnymi zegarami CSS (conic-gradient), przypominający cyfrowe zegary w nowoczesnych autach.
- 🐳 **Docker-Ready**: Pełna gotowość do natychmiastowego wdrażania na maszynach Proxmox, serwerach VPS czy Raspberry Pi.

---

## 🏗️ Architektura / Technologie

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **Protokół IoT:** Eclipse Mosquitto, Paho-MQTT
- **Frontend:** HTML5, Vanilla JavaScript, CSS3 (Brak zewnętrznych zależności graficznych typu React/Vue)
- **Konteneryzacja:** Docker & Docker Compose
- **Proxy:** Przykładowa konfiguracja dla Nginx (Reverse Proxy + obsługa szyfrowania SSL)

---

## 📦 Struktura Projektu

```text
├── app/
│   ├── main.py              # Główna logika FastAPI, MQTT i WebSockets
│   └── templates/
│       └── index.html       # Dashboard w ciemnym motywie (Jinja2)
├── docker-compose.yml       # Konfiguracja środowiska (Aplikacja + opcjonalny broker MQTT)
├── Dockerfile               # Obraz Docker dla aplikacji
├── nginx_car.conf           # Przykładowa konfiguracja vhosta (Nginx)
├── requirements.txt         # Zależności Python
├── test_emulator.py         # Skrypt symulujący ruch auta do celów testowych
└── README.md                # Ten plik
```

---

## ⚙️ Wdrażanie i Konfiguracja (Proxmox / Linux)

Uruchomienie projektu ogranicza się do zaledwie kilku komend. 

### Wymagania:
- Środowisko obsługujące kontenery: zainstalowany **Docker** oraz **Docker Compose**.
- (Opcjonalnie) Skonfigurowany własny broker MQTT, chociaż `docker-compose.yml` zawiera serwer `mosquitto` gotowy do użycia.

### Krok 1: Sklonuj repozytorium
```bash
git clone https://github.com/TwojaNazwa/car-assistant.git
cd car-assistant
```

### Krok 2: Uruchom środowisko Docker
```bash
docker compose up -d --build
```
Aplikacja zostanie zbudowana i uruchomiona na porcie `8000`.

### Krok 3: (Konfiguracja Torque Pro na urządzeniu w aucie)
W aplikacji Torque Pro wejdź w:
`Ustawienia -> Wgrywanie danych na serwer WWW` 
- Wpisz adres URL endpointu: `https://twojadomena.pl/api/torque` (jeśli używasz Reverse Proxy) lub IP serwera (jeśli w LAN).
- Zaznacz odpowiednie interwały wysyłania (np. co 1 sekundę).

---

## 🧪 Testowanie za pomocą Emulatora
Nie musisz siedzieć w samochodzie, żeby przetestować dashboard! 
Aplikacja zawiera symulator generujący płynne krzywe jazdy (zmiana biegów, przyspieszanie, nagrzewanie płynu, itp.).

Aby uruchomić emulator (wymaga Pythona lokalnie):
```bash
pip install requests
python test_emulator.py --url http://localhost:8000/api/torque
```
Natychmiast po jego uruchomieniu wejdź na adres `http://localhost:8000/` – dashboard ożyje i zegary zaczną reagować na symulowane dane.

---

## 🌐 Konfiguracja Nginx (Reverse Proxy)
Zaleca się umieszczenie aplikacji za Nginx-em, zwłaszcza ze względów bezpieczeństwa (certyfikat SSL HTTPS), co jest wymagane przez wiele nowoczesnych urządzeń i przeglądarek do uruchamiania skryptów oraz geolokalizacji.

Gotowa, przykładowa konfiguracja Nginx uwzględniająca przekazywanie pakietów nagłówków WebSockets znajduje się w pliku `nginx_car.conf`. Pamiętaj aby zmienić w niej adresy IP, docelowe porty, certyfikaty SSL i domenę (np. `car.nostressit.co.uk`).

---

## 👨‍💻 Zmienne Środowiskowe (ENV)
Kontroluj aplikację za pomocą pliku `docker-compose.yml`:
- `MQTT_HOST`: Adres IP lub nazwa brokera (domyślnie 127.0.0.1 lub nazwa kontenera)
- `MQTT_PORT`: Port brokera MQTT (1883)
- `MQTT_USER` / `MQTT_PASSWORD`: Dane logowania do MQTT (zostaw puste, by ominąć autoryzację)
- `TORQUE_USER_EMAIL`: E-mail uwierzytelniający z Torque (Opcjonalnie, pozostawienie wartości domyślnej weryfikuje nadchodzące żądania względem tej zmiennej)

---

## ⚖️ Licencja
Ten projekt jest wydany na licencji MIT. Możesz z niego swobodnie korzystać i go modyfikować.

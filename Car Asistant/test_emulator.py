import time
import requests
import random
import argparse
import math

def simulate_telemetry(url: str, email: str, interval: float):
    print(f"Rozpoczynam symulację telemetrii Torque Pro do: {url}")
    print(f"Używam adresu email: {email}")
    print(f"Interwał wysyłania: {interval} sekundy\n")

    session_id = f"sim_{int(time.time())}"
    
    # Stan początkowy
    rpm = 800.0
    speed = 0.0
    coolant = 20.0
    fuel = 85.0
    battery = 12.3 # zapłon wyłączony -> napięcie akumulatora
    load = 0.0
    lat = 51.5074
    lon = -0.1278
    
    t = 0.0
    
    # Fazy symulacji: 0-10s: postój (silnik wyłączony), 10-20s: rozruch i bieg jałowy, 20s+: jazda
    
    while True:
        current_time_ms = int(time.time() * 1000)
        
        if t < 10:
            # Postój
            rpm = 0.0
            speed = 0.0
            battery = 12.4 + random.uniform(-0.1, 0.1)
            load = 0.0
        elif t < 20:
            # Bieg jałowy
            rpm = 850.0 + random.uniform(-20, 20)
            speed = 0.0
            battery = 14.1 + random.uniform(-0.1, 0.1)
            load = 25.0 + random.uniform(-2, 2)
            coolant += 0.5
        else:
            # Jazda
            # Przyspieszanie i hamowanie symulowane falą sinusoidalną
            cycle = (t - 20) / 10.0
            speed_target = max(0, math.sin(cycle) * 60 + 40)
            speed += (speed_target - speed) * 0.2
            
            # Zmiana obrotów proporcjonalnie do zmiany prędkości i samej prędkości (uproszczona skrzynia biegów)
            gear = max(1, int(speed / 20) + 1)
            rpm = (speed / gear) * 80 + 1000 + random.uniform(-50, 50)
            if speed < 5:
                rpm = 850.0 + random.uniform(-20, 20)
                
            battery = 14.2 + random.uniform(-0.1, 0.1)
            load = min(100.0, max(0.0, (speed_target - speed) * 5 + 40 + random.uniform(-5, 5)))
            
            if coolant < 90.0:
                coolant += 0.2
            else:
                coolant = 90.0 + random.uniform(-1, 1)
                
            fuel -= 0.01
            
            # Ruch GPS
            lat += 0.00001 * speed / 50
            lon -= 0.00001 * speed / 50

        # Torque Pro konwencja hex PID:
        # k0c = RPM, k0d = Speed, k05 = Coolant, k2f = Fuel, kff1005 = GPS lat (często po prostu "lat"), kff1006 = lon
        # Będziemy używać kluczy z zapytania dla prostoty
        params = {
            "eml": email,
            "session": session_id,
            "time": current_time_ms,
            "k0c": f"{rpm:.1f}",
            "k0d": f"{speed:.1f}",
            "k05": f"{coolant:.1f}",
            "k2f": f"{fuel:.1f}",
            "kff1005": f"{battery:.1f}", # Napięcie akumulatora
            "k04": f"{load:.1f}",
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "v": "1"
        }
        
        try:
            print(f"Wysyłam pakiet: RPM={rpm:.0f}, Speed={speed:.0f} km/h, Temp={coolant:.0f}°C")
            response = requests.get(url, params=params, timeout=5)
            print(f"Odpowiedź serwera: HTTP {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Błąd wysyłania: {e}")
            
        t += interval
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emulator telemetrii Torque Pro")
    parser.add_argument("--url", default="http://localhost:8000/api/torque", help="Adres endpointu Torque")
    parser.add_argument("--email", default="lukasz@nostressit.co.uk", help="Adres email autoryzacji")
    parser.add_argument("--interval", type=float, default=2.0, help="Interwał wysyłania (sekundy)")
    
    args = parser.parse_args()
    simulate_telemetry(args.url, args.email, args.interval)

import requests
import json

def test_auroravision():
    # Credenziali
    username = "tomacarburanti"
    password = "Riccardo@01"
    entity_id = "14354021"  # Utilizziamo il primo ID come test
    
    # URL di login e API
    login_url = "https://www.auroravision.net/ums/v1/login?setCookie=true"
    data_url = "https://easyview.auroravision.net/easyview/services/gmi/summary/PlantEnergy.json"
    
    # Crea una sessione per mantenere i cookie
    session = requests.Session()
    
    # Headers per sembrare un browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
    }
    session.headers.update(headers)
    
    # Login
    print("Tentativo login AuroraVision...")
    try:
        login_response = session.get(
            login_url,
            auth=requests.auth.HTTPBasicAuth(username, password),
            timeout=30
        )
        
        if login_response.status_code != 200:
            print(f"Errore login: {login_response.status_code}")
            return None
            
        print("Login riuscito")
        
        # Richiesta dati
        params = {
            "eids": entity_id,
            "tz": "Europe/Rome",
            "nDays": 0,
            "v": "2.1.52"
        }
        
        data_response = session.get(data_url, params=params, timeout=30)
        
        if data_response.status_code == 200:
            # Stampa risultato formattato
            json_data = data_response.json()
            print(json.dumps(json_data, indent=2))
            return json_data
        else:
            print(f"Errore richiesta dati: {data_response.status_code}")
            return None
            
    except Exception as e:
        print(f"Errore: {e}")
        return None

if __name__ == "__main__":
    test_auroravision()
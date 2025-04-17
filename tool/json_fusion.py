import requests
import json
from fusion_solar_py.client import FusionSolarClient

def test_fusionsolar():
    # Credenziali
    username = "tomarocco@libero.it"
    password = "logistica2024"
    subdomain = "uni005eu5"
    captcha_model_path = "captcha_huawei.onnx"  # Assicurati che il file sia presente
    
    print("Inizializzazione client FusionSolar...")
    try:
        # Inizializza il client
        client = FusionSolarClient(
            username, 
            password,
            captcha_model_path=captcha_model_path,
            huawei_subdomain=subdomain
        )
        
        # Ottieni lo stato di potenza
        print("Richiesta stato di potenza...")
        power_status = client.get_power_status()
        
        # Esaminiamo quali attributi sono effettivamente disponibili
        print("Attributi disponibili nell'oggetto PowerStatus:")
        power_attrs = [attr for attr in dir(power_status) if not attr.startswith('_')]
        print(power_attrs)
        
        # Creiamo un dizionario con gli attributi disponibili
        power_dict = {}
        for attr in power_attrs:
            if attr != "as_dict":  # Escludiamo metodi
                try:
                    power_dict[attr] = getattr(power_status, attr)
                except Exception as e:
                    power_dict[attr] = f"Errore: {e}"
        
        print(json.dumps(power_dict, indent=2, default=str))
        
        # Se vuoi anche dati più dettagliati sugli impianti
        print("\nRichiesta lista impianti...")
        plants = client.get_plant_list()
        
        if plants:
            # Esaminiamo quali attributi sono disponibili per un impianto
            print("Attributi disponibili nell'oggetto Plant:")
            if len(plants) > 0:
                plant_attrs = [attr for attr in dir(plants[0]) if not attr.startswith('_')]
                print(plant_attrs)
            
            plants_data = []
            for plant in plants:
                plant_dict = {}
                for attr in plant_attrs:
                    if attr != "as_dict":  # Escludiamo metodi
                        try:
                            plant_dict[attr] = getattr(plant, attr)
                        except Exception as e:
                            plant_dict[attr] = f"Errore: {e}"
                plants_data.append(plant_dict)
            
            print(json.dumps(plants_data, indent=2, default=str))
        
        return {"power_status": power_dict, "plants": plants_data if plants else []}
        
    except Exception as e:
        print(f"Errore: {e}")
        return None

if __name__ == "__main__":
    test_fusionsolar()
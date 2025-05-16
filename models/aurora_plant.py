import logging
from datetime import datetime
from models.plant import Plant

logger = logging.getLogger(__name__)

class AuroraVisionPlant(Plant):
    """
    Classe per rappresentare un impianto AuroraVision.
    Utilizza l'API PlantEnergy.json per ottenere dati in tempo reale.
    """
    
    def __init__(self, name, entity_id, session_manager):
        """
        Inizializza un impianto AuroraVision.
        
        Args:
            name (str): Nome dell'impianto
            entity_id (str): ID dell'entità AuroraVision
            session_manager: Gestore della sessione condivisa
        """
        super().__init__(name, entity_id, "AuroraVision")
        self.session_manager = session_manager
        self.base_url = "https://easyview.auroravision.net/easyview/services/gmi/summary/PlantEnergy.json"
        self.request_timeout = 30  # Timeout in secondi
    
    def check_connection(self):
        """
        Verifica la connessione e aggiorna lo stato dell'impianto.
        
        Returns:
            bool: True se l'aggiornamento ha avuto successo, False altrimenti
        """
        try:
            # Ottieni una sessione valida dal session manager
            session = self.session_manager.get_session()
            if not session:
                return self.update_status(0.0, 0.0, False, "Sessione non disponibile")
            
            # Costruisci l'URL della richiesta
            params = {
                "eids": self.id,
                "tz": "Europe/Rome",
                "nDays": 0,
                "v": "2.1.52"
            }
            
            # Esegui la richiesta
            response = session.get(self.base_url, params=params, timeout=self.request_timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "SUCCESS":
                    current_power = 0.0
                    energy_today = 0.0
                    
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    # Estrai la potenza attuale
                    for field in data.get("fields", []):
                        # Per l'energia giornaliera
                        if field.get("label") == "today" and field.get("field") == "GenerationEnergy":
                            energy_today = float(field.get("value", 0))
                        
                        # Per la potenza istantanea, verifica che la data sia di oggi
                        if field.get("type") == "instant" and field.get("field") == "GenerationPower":
                            # Estrai la data dal campo startLabel
                            start_label = field.get("startLabel", "")
                            if start_label and today in start_label:
                                # La data è di oggi, possiamo usare il valore
                                current_power = float(field.get("value", 0))
                            else:
                                # La data non è di oggi, imposta a zero
                                current_power = 0.0
                                logger.info(f"Impianto {self.name}: valore 'instant' non aggiornato a oggi. Impostato a zero.")
                    
                    # Aggiorna lo stato dell'impianto
                    return self.update_status(current_power, energy_today, True)
                else:
                    logger.warning(f"Risposta API non valida per {self.name}: {data.get('status')}")
                    return self.update_status(0.0, 0.0, False, f"Risposta API non valida: {data.get('status')}")
            elif response.status_code in [401, 403]:
                # Sessione scaduta, invalidala
                self.session_manager.invalidate_session()
                logger.warning(f"Sessione scaduta per {self.name}, tentativo di riconnessione al prossimo ciclo")
                return self.update_status(0.0, 0.0, False, f"Sessione scaduta. Riconnessione al prossimo ciclo.")
            else:
                logger.error(f"Errore HTTP {response.status_code} per {self.name}")
                return self.update_status(0.0, 0.0, False, f"Errore HTTP: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Errore durante l'aggiornamento di {self.name}: {str(e)}")
            return self.update_status(0.0, 0.0, False, f"Errore: {str(e)}")
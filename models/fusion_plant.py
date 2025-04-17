"""
Implementazione della classe Plant per gli impianti FusionSolar.
"""
import logging
from datetime import datetime
from models.plant import Plant

# Verifica se la libreria FusionSolar è disponibile
try:
    from fusion_solar_py.client import FusionSolarClient
    FUSION_SOLAR_AVAILABLE = True
except ImportError:
    FUSION_SOLAR_AVAILABLE = False
    logging.warning("Libreria fusion_solar_py non disponibile. Il supporto per FusionSolar è disabilitato.")

logger = logging.getLogger(__name__)

class FusionSolarPlant(Plant):
    """
    Classe per rappresentare un impianto FusionSolar.
    Utilizza il client FusionSolar per ottenere dati in tempo reale.
    """
    
    def __init__(self, name, plant_id, client_manager):
        """
        Inizializza un impianto FusionSolar.
        
        Args:
            name (str): Nome dell'impianto
            plant_id (str): ID dell'impianto (può essere arbitrario)
            client_manager: Gestore del client FusionSolar
        """
        super().__init__(name, plant_id, "FusionSolar")
        self.client_manager = client_manager
        self.available = FUSION_SOLAR_AVAILABLE
    
    def check_connection(self):
        """
        Verifica la connessione e aggiorna lo stato dell'impianto.
        
        Returns:
            bool: True se l'aggiornamento ha avuto successo, False altrimenti
        """
        if not self.available:
            return self.update_status(0.0, 0.0, False, "Libreria FusionSolar non disponibile")
        
        try:
            # Ottieni un client valido dal client manager
            client = self.client_manager.get_client()
            if not client:
                return self.update_status(0.0, 0.0, False, "Client non disponibile")
            
            # Ottieni lo stato di potenza
            power_status = client.get_power_status()
            
            if power_status:
                try:
                    current_power = power_status.current_power_kw
                    
                    # Ottieni l'energia giornaliera - nota che il nome dell'attributo potrebbe variare
                    # a seconda della versione della libreria
                    energy_today = getattr(power_status, 'energy_today_kwh', 0.0)
                    if energy_today is None or energy_today == 0.0:
                        # Prova attributi alternativi per l'energia giornaliera
                        energy_today = getattr(power_status, 'total_power_today_kwh', 0.0)
                    
                    # Aggiorna lo stato dell'impianto
                    return self.update_status(current_power, energy_today, True)
                except AttributeError as e:
                    logger.error(f"Errore nell'accesso agli attributi dell'oggetto PowerStatus: {str(e)}")
                    return self.update_status(0.0, 0.0, False, f"Errore attributi PowerStatus: {str(e)}")
            else:
                logger.warning(f"Dati non disponibili per {self.name}")
                return self.update_status(0.0, 0.0, False, "Dati non disponibili")
                
        except Exception as e:
            logger.error(f"Errore durante l'aggiornamento di {self.name}: {str(e)}")
            # Invalida il client per forzare un nuovo login
            self.client_manager.invalidate_client()
            return self.update_status(0.0, 0.0, False, f"Errore: {str(e)}")
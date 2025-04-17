"""
Modello base per gli impianti fotovoltaici.
Definisce l'interfaccia comune a tutti i tipi di impianti.
"""
from datetime import datetime

class Plant:
    """Classe base per rappresentare un impianto fotovoltaico."""
    
    def __init__(self, name, plant_id, plant_type):
        self.name = name
        self.id = plant_id
        self.type = plant_type
        self.power = 0.0
        self.energy_today = 0.0  # Manteniamo il campo ma non lo mostriamo nell'UI
        self.status = "Non inizializzato"
        self.last_update = None
        self.is_online = False
        self.error_message = None
        self.connection_retry_count = 0
        self.max_retries = 3
        self.consecutive_failures = 0
        self.last_successful_check = None
    
    def update_status(self, power, energy_today, is_online, error_message=None):
        """
        Aggiorna lo stato dell'impianto.
        
        Args:
            power (float): Potenza attuale in kW
            energy_today (float): Energia prodotta oggi in kWh (non mostrata nell'UI)
            is_online (bool): Se l'impianto è online
            error_message (str, optional): Messaggio di errore. Default None.
        
        Returns:
            bool: True se l'impianto è online, False altrimenti
        """
        self.power = power
        self.energy_today = energy_today
        self.last_update = datetime.now()
        self.is_online = is_online
        self.error_message = error_message
        
        if is_online:
            self.status = "Online" if power > 0 else "Inattivo"
            self.consecutive_failures = 0
            self.last_successful_check = self.last_update
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_retries:
                self.status = "OFFLINE"
            else:
                self.status = "Errore"
        
        return is_online
    
    def to_dict(self):
        """
        Converte l'impianto in un dizionario.
        
        Returns:
            dict: Rappresentazione dell'impianto come dizionario
        """
        return {
            "name": self.name,
            "id": self.id,
            "type": self.type,
            "power": round(self.power, 2),
            "energy_today": round(self.energy_today, 2),  # Manteniamo il campo per i calcoli backend
            "status": self.status,
            "is_online": self.is_online,
            "last_update": self.last_update.strftime("%Y-%m-%d %H:%M:%S") if self.last_update else "Mai",
            "error_message": self.error_message,
            "consecutive_failures": self.consecutive_failures
        }
    
    def check_connection(self):
        """
        Verifica la connessione all'impianto e aggiorna i dati.
        Deve essere implementato dalle sottoclassi.
        
        Returns:
            bool: True se l'aggiornamento ha avuto successo, False altrimenti
        """
        raise NotImplementedError("Le sottoclassi devono implementare check_connection()")
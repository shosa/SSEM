"""
Servizio di gestione centralizzata degli impianti fotovoltaici.
"""
import logging
import threading
import time
import configparser
import os
from datetime import datetime

# Utilizziamo import assoluti invece di relativi
from services.session_managers import AuroraSessionManager, FusionSolarClientManager
from models.aurora_plant import AuroraVisionPlant
from models.fusion_plant import FusionSolarPlant, FUSION_SOLAR_AVAILABLE

logger = logging.getLogger(__name__)

class PlantManager:
    """
    Gestore centralizzato degli impianti fotovoltaici.
    Monitora tutti gli impianti e mantiene lo stato aggiornato.
    """
    
    def __init__(self, config_dir="config"):
        """
        Inizializza il gestore impianti.
        
        Args:
            config_dir (str): Directory contenente i file di configurazione
        """
        self.config_dir = config_dir
        self.plants = {}
        self.aurora_session_manager = None
        self.fusion_client_manager = None
        self.monitoring_active = False
        self.monitoring_thread = None
        self.update_interval = 300  # 5 minuti di default
        self.aurora_config = None
        self.fusion_config = None
    
    def load_aurora_config(self, config_file):
        """
        Carica la configurazione AuroraVision da file.
        
        Args:
            config_file (str): Nome del file di configurazione
        
        Returns:
            bool: True se il caricamento è riuscito, False altrimenti
        """
        config = configparser.ConfigParser()
        config_path = os.path.join(self.config_dir, config_file)
        
        if not os.path.exists(config_path):
            logger.error(f"File di configurazione AuroraVision non trovato: {config_path}")
            return False
        
        try:
            config.read(config_path)
            
            self.aurora_config = {
                "username": config.get("CREDENTIALS", "username"),
                "password": config.get("CREDENTIALS", "password"),
                "entity_ids": config.get("CREDENTIALS", "entity_ids").split(","),
                "entity_aliases": config.get("CREDENTIALS", "entity_aliases", fallback="").split(","),
                "time_interval": config.getint("SETTINGS", "time_interval", fallback=300)
            }
            
            # Imposta l'intervallo di aggiornamento
            self.update_interval = min(self.update_interval, self.aurora_config["time_interval"])
            
            # Crea il gestore di sessione
            self.aurora_session_manager = AuroraSessionManager(
                {
                    "username": self.aurora_config["username"],
                    "password": self.aurora_config["password"]
                }
            )
            
            # Registra gli impianti
            for i, entity_id in enumerate(self.aurora_config["entity_ids"]):
                name = (self.aurora_config["entity_aliases"][i] 
                        if i < len(self.aurora_config["entity_aliases"]) 
                        else f"AuroraVision-{entity_id}")
                plant = AuroraVisionPlant(name, entity_id, self.aurora_session_manager)
                self.plants[f"aurora_{entity_id}"] = plant
                logger.info(f"Registrato impianto AuroraVision: {name} (ID: {entity_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore durante il caricamento della configurazione AuroraVision: {e}")
            return False
    
    def load_fusion_config(self, config_file):
        """
        Carica la configurazione FusionSolar da file.
        
        Args:
            config_file (str): Nome del file di configurazione
        
        Returns:
            bool: True se il caricamento è riuscito, False altrimenti
        """
        if not FUSION_SOLAR_AVAILABLE:
            logger.warning("Libreria FusionSolar non disponibile, configurazione ignorata")
            return False
            
        config = configparser.ConfigParser()
        config_path = os.path.join(self.config_dir, config_file)
        
        if not os.path.exists(config_path):
            logger.error(f"File di configurazione FusionSolar non trovato: {config_path}")
            return False
        
        try:
            config.read(config_path)
            
            self.fusion_config = {
                "username": config.get("CREDENTIALS", "username"),
                "password": config.get("CREDENTIALS", "password"),
                "subdomain": config.get("CREDENTIALS", "subdomain", fallback=""),
                "captcha_model_path": config.get("CREDENTIALS", "captcha_model_path", fallback=""),
                "plant_name": config.get("CREDENTIALS", "plant_name", fallback="FusionSolar"),  # Aggiungi questa riga
                "time_interval": config.getint("SETTINGS", "time_interval", fallback=300)
            }
            
            # Imposta l'intervallo di aggiornamento
            self.update_interval = min(self.update_interval, self.fusion_config["time_interval"])
            
            # Crea il gestore di client
            self.fusion_client_manager = FusionSolarClientManager(
                {
                    "username": self.fusion_config["username"],
                    "password": self.fusion_config["password"],
                    "subdomain": self.fusion_config["subdomain"],
                    "captcha_model_path": self.fusion_config["captcha_model_path"]
                }
            )
            
            # Registra impianto FusionSolar
            plant = FusionSolarPlant(self.fusion_config["plant_name"], "main", self.fusion_client_manager)
            self.plants["fusion_main"] = plant
            logger.info("Registrato impianto FusionSolar principale")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore durante il caricamento della configurazione FusionSolar: {e}")
            return False
    
    def update_all_plants(self):
        """
        Aggiorna lo stato di tutti gli impianti.
        
        Returns:
            dict: Dizionario con i risultati degli aggiornamenti
        """
        results = {}
        
        for plant_id, plant in self.plants.items():
            try:
                # Aggiorna lo stato dell'impianto
                success = plant.check_connection()
                results[plant_id] = success
                
                if success:
                    logger.info(f"Aggiornato impianto {plant.name}: {plant.power} kW")
                else:
                    logger.warning(f"Aggiornamento fallito per l'impianto {plant.name}: {plant.error_message}")
                    
            except Exception as e:
                logger.error(f"Errore durante l'aggiornamento dell'impianto {plant_id}: {e}")
                results[plant_id] = False
        
        return results
    
    def monitoring_loop(self):
        """Loop di monitoraggio che aggiorna periodicamente tutti gli impianti."""
        logger.info(f"Avvio loop di monitoraggio (intervallo: {self.update_interval} secondi)")
        
        while self.monitoring_active:
            try:
                self.update_all_plants()
            except Exception as e:
                logger.error(f"Errore nel loop di monitoraggio: {e}")
                
            # Attendi il prossimo aggiornamento
            for i in range(self.update_interval):
                if not self.monitoring_active:
                    break
                time.sleep(1)
    
    def start_monitoring(self):
        """
        Avvia il monitoraggio in background.
        
        Returns:
            bool: True se l'avvio è riuscito, False altrimenti
        """
        if self.monitoring_active:
            return False
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("Monitoraggio avviato")
        return True
    
    def stop_monitoring(self):
        """
        Ferma il monitoraggio in background.
        
        Returns:
            bool: True se l'arresto è riuscito, False altrimenti
        """
        if not self.monitoring_active:
            return False
            
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
            self.monitoring_thread = None
        logger.info("Monitoraggio fermato")
        return True
    
    def get_all_plants(self):
        """
        Restituisce informazioni su tutti gli impianti.
        
        Returns:
            dict: Dizionario con le informazioni degli impianti
        """
        return {plant_id: plant.to_dict() for plant_id, plant in self.plants.items()}
    
    def get_plant(self, plant_id):
        """
        Restituisce informazioni su un impianto specifico.
        
        Args:
            plant_id (str): ID dell'impianto
            
        Returns:
            dict: Informazioni sull'impianto o None se non trovato
        """
        plant = self.plants.get(plant_id)
        return plant.to_dict() if plant else None
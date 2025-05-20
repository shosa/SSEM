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

# Importa il supporto per la nuova API Northbound
try:
    from models.fusion_pyhfs_plant import PyHFSManager, FusionSolarNorthboundPlant, PYHFS_AVAILABLE
except ImportError:
    PYHFS_AVAILABLE = False
    logging.warning("Libreria pyhfs non disponibile. Il supporto per FusionSolar Northbound API è disabilitato.")

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
        self.fusion_northbound_manager = None
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
        config = configparser.ConfigParser()
        config_path = os.path.join(self.config_dir, config_file)
        
        if not os.path.exists(config_path):
            logger.error(f"File di configurazione FusionSolar non trovato: {config_path}")
            return False
        
        try:
            config.read(config_path)
            
            # Leggi la configurazione dalla sezione standard
            username = config.get("CREDENTIALS", "username")
            password = config.get("CREDENTIALS", "password")
            subdomain = config.get("CREDENTIALS", "subdomain", fallback="")
            captcha_model_path = config.get("CREDENTIALS", "captcha_model_path", fallback="")
            plant_name = config.get("CREDENTIALS", "plant_name", fallback="FusionSolar")
            time_interval = config.getint("SETTINGS", "time_interval", fallback=300)
            
            # Verifica se la sezione NORTHBOUND esiste e se è abilitata
            northbound_enabled = False
            northbound_username = username
            northbound_password = password
            northbound_plant_id = "main"
            
            if config.has_section("NORTHBOUND"):
                # Leggi il flag enabled
                northbound_enabled = config.getboolean("NORTHBOUND", "enabled", fallback=False)
                
                if northbound_enabled:
                    northbound_username = config.get("NORTHBOUND", "username", fallback=username)
                    northbound_password = config.get("NORTHBOUND", "password", fallback=password)
                    northbound_plant_id = config.get("NORTHBOUND", "plant_id", fallback="main")
            
            # Determina quale API usare (Northbound o Standard)
            if northbound_enabled and PYHFS_AVAILABLE:
                api_type = "Northbound"
                logger.info("API Northbound abilitata e disponibile per FusionSolar")
            elif FUSION_SOLAR_AVAILABLE:
                api_type = "Standard"
                logger.info("API Standard disponibile per FusionSolar")
            else:
                logger.warning("Nessuna libreria FusionSolar disponibile, configurazione ignorata")
                return False
            
            self.fusion_config = {
                "username": username,
                "password": password,
                "subdomain": subdomain,
                "captcha_model_path": captcha_model_path,
                "plant_name": plant_name,
                "time_interval": time_interval,
                "api_type": api_type,
                "northbound_enabled": northbound_enabled,
                "northbound_username": northbound_username,
                "northbound_password": northbound_password,
                "northbound_plant_id": northbound_plant_id
            }
            
            # Imposta l'intervallo di aggiornamento
            self.update_interval = min(self.update_interval, time_interval)
            
            # Inizializza il gestore appropriato in base al tipo di API
            if api_type == "Northbound":
                logger.info("Utilizzo dell'API Northbound per FusionSolar")
                # Crea il gestore Northbound API
                self.fusion_northbound_manager = PyHFSManager(
                    {
                        "username": northbound_username,
                        "password": northbound_password
                    }
                )
                
                # Registra impianto FusionSolar con API Northbound
                plant = FusionSolarNorthboundPlant(plant_name, northbound_plant_id, self.fusion_northbound_manager)
                self.plants["fusion_main"] = plant
                logger.info(f"Registrato impianto FusionSolar principale (API Northbound): {plant_name}")
            else:
                logger.info("Utilizzo dell'API Standard per FusionSolar")
                # Verifica percorso del modello CAPTCHA
                if captcha_model_path and not os.path.isabs(captcha_model_path):
                    # Costruisci un percorso assoluto rispetto alla directory di configurazione
                    abs_captcha_path = os.path.abspath(os.path.join(self.config_dir, captcha_model_path))
                    if os.path.exists(abs_captcha_path):
                        captcha_model_path = abs_captcha_path
                        logger.info(f"Aggiornato percorso del modello CAPTCHA a: {abs_captcha_path}")
                    else:
                        logger.warning(f"File del modello CAPTCHA non trovato nel percorso: {abs_captcha_path}")
                
                # Crea il gestore di client
                self.fusion_client_manager = FusionSolarClientManager(
                    {
                        "username": username,
                        "password": password,
                        "subdomain": subdomain,
                        "captcha_model_path": captcha_model_path
                    }
                )
                
                # Registra impianto FusionSolar con API Standard
                plant = FusionSolarPlant(plant_name, "main", self.fusion_client_manager)
                self.plants["fusion_main"] = plant
                logger.info(f"Registrato impianto FusionSolar principale (API Standard): {plant_name}")
            
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
        
        # Contatori per il keep-alive
        keep_alive_counter = 0
        keep_alive_interval = 30  # Secondi (come suggerito dalla documentazione)
        is_session_active_interval = 10  # Secondi (come suggerito dalla documentazione)
        is_session_active_counter = 0
        
        while self.monitoring_active:
            try:
                # Per l'API Standard: gestione della sessione FusionSolar
                if self.fusion_client_manager:
                    # Verifica se la sessione è attiva (circa ogni 10 secondi)
                    if is_session_active_counter >= is_session_active_interval:
                        try:
                            if self.fusion_client_manager.client and hasattr(self.fusion_client_manager.client, 'is_session_active'):
                                self.fusion_client_manager.client.is_session_active()
                            is_session_active_counter = 0
                        except Exception as e:
                            logger.debug(f"Errore nella verifica della sessione: {e}")
                    
                    # Mantieni attiva la sessione FusionSolar (circa ogni 30 secondi)
                    if keep_alive_counter >= keep_alive_interval:
                        self.fusion_client_manager.keep_session_alive()
                        keep_alive_counter = 0
                
                # Aggiorna tutti gli impianti
                self.update_all_plants()
            except Exception as e:
                logger.error(f"Errore nel loop di monitoraggio: {e}")
                
            # Attendi il prossimo aggiornamento
            for i in range(self.update_interval):
                if not self.monitoring_active:
                    break
                time.sleep(1)
                keep_alive_counter += 1
                is_session_active_counter += 1
    
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
        
        # Chiudi le sessioni
        if self.fusion_northbound_manager:
            self.fusion_northbound_manager.invalidate_session()
            
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
"""
Gestori di sessione per le varie API di impianti fotovoltaici.
"""
import logging
import requests
import time
from datetime import datetime, timedelta
import threading

# Verifica se la libreria FusionSolar è disponibile
try:
    from fusion_solar_py.client import FusionSolarClient
    FUSION_SOLAR_AVAILABLE = True
except ImportError:
    FUSION_SOLAR_AVAILABLE = False
    logging.warning("Libreria fusion_solar_py non disponibile. Il supporto per FusionSolar è disabilitato.")

logger = logging.getLogger(__name__)

class AuroraSessionManager:
    """
    Gestore della sessione per l'API AuroraVision.
    Mantiene una sessione condivisa per tutti gli impianti AuroraVision.
    """
    
    def __init__(self, credentials):
        """
        Inizializza il gestore di sessione AuroraVision.
        
        Args:
            credentials (dict): Credenziali per l'API AuroraVision
        """
        self.credentials = credentials
        self.session = None
        self.last_login_time = None
        self.login_valid_duration = 3600  # 1 ora in secondi
        self.lock = threading.RLock()
        self.login_url = "https://www.auroravision.net/ums/v1/login?setCookie=true"
        self.request_timeout = 30  # Timeout in secondi
    
    def login(self):
        """
        Effettua il login all'API AuroraVision.
        
        Returns:
            bool: True se il login ha avuto successo, False altrimenti
        """
        with self.lock:
            logger.info("Tentativo login AuroraVision...")
            try:
                username = self.credentials.get("username", "")
                password = self.credentials.get("password", "")
                
                # Controlla le credenziali
                if not username or not password:
                    logger.error("Credenziali AuroraVision mancanti")
                    return False
                
                # Crea una nuova sessione
                session = requests.Session()
                
                # Headers per sembrare un browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*',
                }
                session.headers.update(headers)
                
                # Effettua il login
                response = session.get(
                    self.login_url,
                    auth=requests.auth.HTTPBasicAuth(username, password),
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    self.session = session
                    self.last_login_time = datetime.now()
                    logger.info("Login AuroraVision riuscito")
                    return True
                else:
                    logger.error(f"Login AuroraVision fallito: {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.error(f"Errore durante il login AuroraVision: {e}")
                return False
    
    def get_session(self):
        """
        Ottiene una sessione valida, effettuando il login se necessario.
        
        Returns:
            requests.Session: Sessione valida o None se il login fallisce
        """
        with self.lock:
            # Se la sessione è valida, restituiscila
            if (self.session and self.last_login_time and 
                    (datetime.now() - self.last_login_time).total_seconds() < self.login_valid_duration):
                return self.session
            
            # Altrimenti, effettua un nuovo login
            if self.login():
                return self.session
            else:
                return None
    
    def invalidate_session(self):
        """Invalida la sessione corrente."""
        with self.lock:
            self.last_login_time = None


class FusionSolarClientManager:
    """
    Gestore del client FusionSolar.
    Mantiene un client condiviso per tutti gli impianti FusionSolar.
    """
    
    def __init__(self, credentials):
        """
        Inizializza il gestore del client FusionSolar.
        
        Args:
            credentials (dict): Credenziali per l'API FusionSolar
        """
        self.credentials = credentials
        self.client = None
        self.last_login_time = None
        self.login_valid_duration = 3600  # 1 ora in secondi
        self.lock = threading.RLock()
        self.available = FUSION_SOLAR_AVAILABLE
    
    def initialize_client(self):
        """
        Inizializza il client FusionSolar.
        
        Returns:
            bool: True se l'inizializzazione ha avuto successo, False altrimenti
        """
        if not self.available:
            logger.error("Libreria FusionSolar non disponibile")
            return False
            
        with self.lock:
            logger.info("Inizializzazione client FusionSolar...")
            try:
                username = self.credentials.get("username", "")
                password = self.credentials.get("password", "")
                subdomain = self.credentials.get("subdomain", "")
                captcha_model_path = self.credentials.get("captcha_model_path", "")
                
                # Controlla le credenziali
                if not username or not password:
                    logger.error("Credenziali FusionSolar mancanti")
                    return False
                
                # Crea un nuovo client
                client = FusionSolarClient(
                    username, 
                    password,
                    captcha_model_path=captcha_model_path,
                    huawei_subdomain=subdomain
                )
                
                # Testa il client
                power_status = client.get_power_status()
                if power_status:
                    self.client = client
                    self.last_login_time = datetime.now()
                    logger.info("Inizializzazione client FusionSolar riuscita")
                    return True
                else:
                    logger.error("Inizializzazione client FusionSolar fallita")
                    return False
                    
            except Exception as e:
                logger.error(f"Errore durante l'inizializzazione del client FusionSolar: {e}")
                return False
    
    def get_client(self):
        """
        Ottiene un client valido, inizializzandolo se necessario.
        
        Returns:
            FusionSolarClient: Client valido o None se l'inizializzazione fallisce
        """
        if not self.available:
            return None
            
        with self.lock:
            # Se il client è valido, restituiscilo
            if (self.client and self.last_login_time and 
                    (datetime.now() - self.last_login_time).total_seconds() < self.login_valid_duration):
                return self.client
            
            # Altrimenti, inizializza un nuovo client
            if self.initialize_client():
                return self.client
            else:
                return None
    
    def invalidate_client(self):
        """Invalida il client corrente."""
        with self.lock:
            self.last_login_time = None
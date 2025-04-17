"""
SolarMonitor - Applicazione per il monitoraggio di impianti fotovoltaici
FusionSolar e AuroraVision

Entry point dell'applicazione Flask.
"""
import os
import logging
from flask import Flask

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("solar_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SolarMonitor")

def create_app(config_dir="config"):
    """
    Crea e configura l'applicazione Flask.
    
    Args:
        config_dir (str): Directory contenente i file di configurazione
    
    Returns:
        Flask: Applicazione Flask configurata
    """
    # Crea l'applicazione Flask
    app = Flask(__name__)
    
    # Assicurati che le directory esistano
    os.makedirs(config_dir, exist_ok=True)
    
    # Crea i file di configurazione se non esistono
    setup_config_files(config_dir)
    
    # Importa i servizi qui per evitare import circolari
    from services.plant_manager import PlantManager
    
    # Crea e configura il gestore impianti
    plant_manager = PlantManager(config_dir=config_dir)
    
    # Carica le configurazioni
    plant_manager.load_aurora_config("aurora_config.ini")
    plant_manager.load_fusion_config("fusion_config.ini")
    
    # Avvia il monitoraggio
    plant_manager.start_monitoring()
    
    # Registra il gestore impianti nell'applicazione
    app.config['PLANT_MANAGER'] = plant_manager
    
    # Importa i blueprint qui per evitare import circolari
    from solar_routes import blueprints
    
    # Registra i blueprint
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    logger.info("Applicazione SolarMonitor inizializzata")
    
    return app

def setup_config_files(config_dir):
    """
    Crea i file di configurazione se non esistono.
    
    Args:
        config_dir (str): Directory contenente i file di configurazione
    """
    # Copia aurora_config.ini se non esiste
    target_aurora = os.path.join(config_dir, "aurora_config.ini")
    if not os.path.exists(target_aurora):
        with open(target_aurora, "w") as f:
            f.write("""[CREDENTIALS]
username = tomacarburanti
password = Riccardo@01
entity_ids = 14354021,14349631
entity_aliases = Pizzuti,Vasca

[SETTINGS]
time_interval = 300
alarm_enabled = True
data_retention_days = 30
""")
        logger.info(f"Creato file di configurazione: {target_aurora}")
    
    # Copia fusion_config.ini se non esiste
    target_fusion = os.path.join(config_dir, "fusion_config.ini")
    if not os.path.exists(target_fusion):
        with open(target_fusion, "w") as f:
            f.write("""[CREDENTIALS]
username = tomarocco@libero.it
password = logistica2024
subdomain = uni005eu5
captcha_model_path = captcha_huawei.onnx

[SETTINGS]
time_interval = 300
alarm_enabled = True
data_retention_days = 30
""")
        logger.info(f"Creato file di configurazione: {target_fusion}")

if __name__ == "__main__":
    # Crea l'applicazione
    app = create_app()
    
    # Avvia il server
    app.run(host='0.0.0.0', port=5000, debug=True)
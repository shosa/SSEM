"""
SSEM - Sistema di Sorveglianza Energetica Monitorata
Applicazione per il monitoraggio di impianti fotovoltaici FusionSolar e AuroraVision

Entry point dell'applicazione Flask con pannello di controllo.
"""
import os
import sys
import logging
import threading
import webbrowser
import time
import configparser
from flask import Flask

# Verifica se PyQt5 è disponibile, altrimenti usa Tkinter come fallback
try:
    from PyQt5 import QtWidgets, QtGui, QtCore
    USE_QT = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    USE_QT = False

# Ottieni la cartella AppData dell'utente corrente
app_data_dir = os.path.join(os.environ['APPDATA'], 'SSEM')
os.makedirs(app_data_dir, exist_ok=True)  # Crea la directory se non esiste

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(app_data_dir, "ssem.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SSEM")

# Variabili globali
flask_app = None
flask_thread = None
server_running = False
plant_manager = None

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
    global plant_manager
    plant_manager = PlantManager(config_dir=config_dir)
    
    # Carica le configurazioni
    plant_manager.load_aurora_config("aurora_config.ini")
    plant_manager.load_fusion_config("fusion_config.ini")
    
    # Registra il gestore impianti nell'applicazione
    app.config['PLANT_MANAGER'] = plant_manager
    
    # Importa i blueprint qui per evitare import circolari
    from solar_routes import blueprints
    
    # Registra i blueprint
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    logger.info("Applicazione SSEM inizializzata")
    
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
                        plant_name = Giumentare

                        [SETTINGS]
                        time_interval = 300
                        alarm_enabled = True
                        data_retention_days = 30
                        """)
        logger.info(f"Creato file di configurazione: {target_fusion}")

def run_flask_server():
    """Avvia il server Flask in un thread separato"""
    global flask_app, server_running
    
    # Crea l'applicazione se non esiste
    if flask_app is None:
        flask_app = create_app()
    
    # Avvia il monitoraggio
    plant_manager.start_monitoring()
    
    server_running = True
    # Avvia il server Flask (non in modalità debug per consentire l'esecuzione in thread)
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def start_server():
    """Avvia il server in un thread separato"""
    global flask_thread, server_running
    
    if not server_running:
        flask_thread = threading.Thread(target=run_flask_server)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("Server SSEM avviato")

def stop_server():
    """Ferma il server"""
    global server_running, plant_manager
    
    if server_running and plant_manager:
        # Prima fermiamo il monitoraggio
        plant_manager.stop_monitoring()
        server_running = False
        logger.info("Server SSEM fermato")

def open_browser():
    """Apre il browser sulla pagina dell'applicazione"""
    webbrowser.open('http://localhost:5000')
    logger.info("Browser aperto sulla pagina SSEM")

def open_config_folder():
    """Apre la cartella di configurazione"""
    os.startfile(os.path.abspath("config"))
    logger.info("Cartella di configurazione aperta")

def open_logs():
    """Apre il file di log"""
    os.startfile(os.path.join(app_data_dir, "ssem.log"))
    logger.info("File di log aperto")

# Funzione per la modifica delle configurazioni
def save_config_file(config_path, config_data):
    """
    Salva i dati di configurazione in un file.
    
    Args:
        config_path (str): Percorso completo del file di configurazione
        config_data (configparser.ConfigParser): Dati di configurazione
    """
    with open(config_path, 'w') as f:
        config_data.write(f)
    logger.info(f"Configurazione salvata: {config_path}")

# Implementazione per PyQt5
if USE_QT:
    class ConfigEditorDialog(QtWidgets.QDialog):
        def __init__(self, parent=None, config_dir="config"):
            super().__init__(parent)
            self.config_dir = config_dir
            self.aurora_config = configparser.ConfigParser()
            self.fusion_config = configparser.ConfigParser()
            
            # Carica le configurazioni
            self.aurora_config.read(os.path.join(config_dir, "aurora_config.ini"))
            self.fusion_config.read(os.path.join(config_dir, "fusion_config.ini"))
            
            self.setup_ui()
            
        def setup_ui(self):
            self.setWindowTitle("Editor Configurazioni")
            self.setMinimumSize(600, 500)
            
            # Layout principale
            main_layout = QtWidgets.QVBoxLayout(self)
            main_layout.setContentsMargins(20, 20, 20, 20)
            main_layout.setSpacing(15)
            
            # Tab widget per le diverse configurazioni
            self.tab_widget = QtWidgets.QTabWidget()
            main_layout.addWidget(self.tab_widget)
            
            # Tab per AuroraVision
            aurora_tab = QtWidgets.QWidget()
            self.tab_widget.addTab(aurora_tab, "AuroraVision")
            
            # Tab per FusionSolar
            fusion_tab = QtWidgets.QWidget()
            self.tab_widget.addTab(fusion_tab, "FusionSolar")
            
            # Configura il tab AuroraVision
            self.setup_aurora_tab(aurora_tab)
            
            # Configura il tab FusionSolar
            self.setup_fusion_tab(fusion_tab)
            
            # Pulsanti di azione
            button_layout = QtWidgets.QHBoxLayout()
            button_layout.addStretch()
            
            self.save_btn = QtWidgets.QPushButton("Salva")
            self.save_btn.clicked.connect(self.save_configurations)
            button_layout.addWidget(self.save_btn)
            
            self.cancel_btn = QtWidgets.QPushButton("Annulla")
            self.cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(self.cancel_btn)
            
            main_layout.addLayout(button_layout)
        
        def setup_aurora_tab(self, tab):
            layout = QtWidgets.QVBoxLayout(tab)
            
            # Gruppo Credenziali
            cred_group = QtWidgets.QGroupBox("Credenziali")
            cred_layout = QtWidgets.QFormLayout(cred_group)
            
            # Username
            self.aurora_username = QtWidgets.QLineEdit()
            self.aurora_username.setText(self.aurora_config.get('CREDENTIALS', 'username', fallback=''))
            cred_layout.addRow("Username:", self.aurora_username)
            
            # Password
            self.aurora_password = QtWidgets.QLineEdit()
            self.aurora_password.setEchoMode(QtWidgets.QLineEdit.Password)
            self.aurora_password.setText(self.aurora_config.get('CREDENTIALS', 'password', fallback=''))
            cred_layout.addRow("Password:", self.aurora_password)
            
            # Entity IDs
            self.aurora_entity_ids = QtWidgets.QLineEdit()
            self.aurora_entity_ids.setText(self.aurora_config.get('CREDENTIALS', 'entity_ids', fallback=''))
            cred_layout.addRow("ID Entità (separati da virgola):", self.aurora_entity_ids)
            
            # Entity Aliases
            self.aurora_entity_aliases = QtWidgets.QLineEdit()
            self.aurora_entity_aliases.setText(self.aurora_config.get('CREDENTIALS', 'entity_aliases', fallback=''))
            cred_layout.addRow("Alias Entità (separati da virgola):", self.aurora_entity_aliases)
            
            layout.addWidget(cred_group)
            
            # Gruppo Impostazioni
            settings_group = QtWidgets.QGroupBox("Impostazioni")
            settings_layout = QtWidgets.QFormLayout(settings_group)
            
            # Time Interval
            self.aurora_time_interval = QtWidgets.QSpinBox()
            self.aurora_time_interval.setMinimum(60)
            self.aurora_time_interval.setMaximum(3600)
            self.aurora_time_interval.setSingleStep(60)
            self.aurora_time_interval.setValue(int(self.aurora_config.get('SETTINGS', 'time_interval', fallback='300')))
            settings_layout.addRow("Intervallo di aggiornamento (secondi):", self.aurora_time_interval)
            
            # Alarm Enabled
            self.aurora_alarm_enabled = QtWidgets.QCheckBox()
            self.aurora_alarm_enabled.setChecked(self.aurora_config.getboolean('SETTINGS', 'alarm_enabled', fallback=True))
            settings_layout.addRow("Abilitare allarmi:", self.aurora_alarm_enabled)
            
            # Data Retention
            self.aurora_data_retention = QtWidgets.QSpinBox()
            self.aurora_data_retention.setMinimum(1)
            self.aurora_data_retention.setMaximum(365)
            self.aurora_data_retention.setValue(int(self.aurora_config.get('SETTINGS', 'data_retention_days', fallback='30')))
            settings_layout.addRow("Conservazione dati (giorni):", self.aurora_data_retention)
            
            layout.addWidget(settings_group)
            layout.addStretch()
        
        def setup_fusion_tab(self, tab):
            layout = QtWidgets.QVBoxLayout(tab)
            
            # Gruppo Credenziali
            cred_group = QtWidgets.QGroupBox("Credenziali")
            cred_layout = QtWidgets.QFormLayout(cred_group)
            
            # Username
            self.fusion_username = QtWidgets.QLineEdit()
            self.fusion_username.setText(self.fusion_config.get('CREDENTIALS', 'username', fallback=''))
            cred_layout.addRow("Username:", self.fusion_username)
            
            # Password
            self.fusion_password = QtWidgets.QLineEdit()
            self.fusion_password.setEchoMode(QtWidgets.QLineEdit.Password)
            self.fusion_password.setText(self.fusion_config.get('CREDENTIALS', 'password', fallback=''))
            cred_layout.addRow("Password:", self.fusion_password)
            
            # Subdomain
            self.fusion_subdomain = QtWidgets.QLineEdit()
            self.fusion_subdomain.setText(self.fusion_config.get('CREDENTIALS', 'subdomain', fallback=''))
            cred_layout.addRow("Sottodominio:", self.fusion_subdomain)
            
            # Captcha Model Path
            self.fusion_captcha_model = QtWidgets.QLineEdit()
            self.fusion_captcha_model.setText(self.fusion_config.get('CREDENTIALS', 'captcha_model_path', fallback=''))
            cred_layout.addRow("Percorso modello captcha:", self.fusion_captcha_model)
            
            # Plant Name
            self.fusion_plant_name = QtWidgets.QLineEdit()
            self.fusion_plant_name.setText(self.fusion_config.get('CREDENTIALS', 'plant_name', fallback=''))
            cred_layout.addRow("Nome impianto:", self.fusion_plant_name)
            
            layout.addWidget(cred_group)
            
            # Gruppo Northbound (se esiste nella configurazione)
            if self.fusion_config.has_section('NORTHBOUND'):
                northbound_group = QtWidgets.QGroupBox("Northbound")
                northbound_layout = QtWidgets.QFormLayout(northbound_group)
                
                # Enabled
                self.fusion_northbound_enabled = QtWidgets.QCheckBox()
                self.fusion_northbound_enabled.setChecked(self.fusion_config.getboolean('NORTHBOUND', 'enabled', fallback=False))
                northbound_layout.addRow("Abilitato:", self.fusion_northbound_enabled)
                
                # Username
                self.fusion_northbound_username = QtWidgets.QLineEdit()
                self.fusion_northbound_username.setText(self.fusion_config.get('NORTHBOUND', 'username', fallback=''))
                northbound_layout.addRow("Username:", self.fusion_northbound_username)
                
                # Password
                self.fusion_northbound_password = QtWidgets.QLineEdit()
                self.fusion_northbound_password.setEchoMode(QtWidgets.QLineEdit.Password)
                self.fusion_northbound_password.setText(self.fusion_config.get('NORTHBOUND', 'password', fallback=''))
                northbound_layout.addRow("Password:", self.fusion_northbound_password)
                
                # Plant ID
                self.fusion_northbound_plant_id = QtWidgets.QLineEdit()
                self.fusion_northbound_plant_id.setText(self.fusion_config.get('NORTHBOUND', 'plant_id', fallback=''))
                northbound_layout.addRow("ID Impianto:", self.fusion_northbound_plant_id)
                
                layout.addWidget(northbound_group)
            
            # Gruppo Impostazioni
            settings_group = QtWidgets.QGroupBox("Impostazioni")
            settings_layout = QtWidgets.QFormLayout(settings_group)
            
            # Time Interval
            self.fusion_time_interval = QtWidgets.QSpinBox()
            self.fusion_time_interval.setMinimum(60)
            self.fusion_time_interval.setMaximum(3600)
            self.fusion_time_interval.setSingleStep(60)
            self.fusion_time_interval.setValue(int(self.fusion_config.get('SETTINGS', 'time_interval', fallback='300')))
            settings_layout.addRow("Intervallo di aggiornamento (secondi):", self.fusion_time_interval)
            
            # Alarm Enabled
            self.fusion_alarm_enabled = QtWidgets.QCheckBox()
            self.fusion_alarm_enabled.setChecked(self.fusion_config.getboolean('SETTINGS', 'alarm_enabled', fallback=True))
            settings_layout.addRow("Abilitare allarmi:", self.fusion_alarm_enabled)
            
            # Data Retention
            self.fusion_data_retention = QtWidgets.QSpinBox()
            self.fusion_data_retention.setMinimum(1)
            self.fusion_data_retention.setMaximum(365)
            self.fusion_data_retention.setValue(int(self.fusion_config.get('SETTINGS', 'data_retention_days', fallback='30')))
            settings_layout.addRow("Conservazione dati (giorni):", self.fusion_data_retention)
            
            layout.addWidget(settings_group)
            layout.addStretch()
        
        def save_configurations(self):
            # Salva configurazione AuroraVision
            self.aurora_config['CREDENTIALS']['username'] = self.aurora_username.text()
            self.aurora_config['CREDENTIALS']['password'] = self.aurora_password.text()
            self.aurora_config['CREDENTIALS']['entity_ids'] = self.aurora_entity_ids.text()
            self.aurora_config['CREDENTIALS']['entity_aliases'] = self.aurora_entity_aliases.text()
            
            self.aurora_config['SETTINGS']['time_interval'] = str(self.aurora_time_interval.value())
            self.aurora_config['SETTINGS']['alarm_enabled'] = str(self.aurora_alarm_enabled.isChecked())
            self.aurora_config['SETTINGS']['data_retention_days'] = str(self.aurora_data_retention.value())
            
            # Salva configurazione FusionSolar
            self.fusion_config['CREDENTIALS']['username'] = self.fusion_username.text()
            self.fusion_config['CREDENTIALS']['password'] = self.fusion_password.text()
            self.fusion_config['CREDENTIALS']['subdomain'] = self.fusion_subdomain.text()
            self.fusion_config['CREDENTIALS']['captcha_model_path'] = self.fusion_captcha_model.text()
            self.fusion_config['CREDENTIALS']['plant_name'] = self.fusion_plant_name.text()
            
            if self.fusion_config.has_section('NORTHBOUND'):
                self.fusion_config['NORTHBOUND']['enabled'] = str(self.fusion_northbound_enabled.isChecked())
                self.fusion_config['NORTHBOUND']['username'] = self.fusion_northbound_username.text()
                self.fusion_config['NORTHBOUND']['password'] = self.fusion_northbound_password.text()
                self.fusion_config['NORTHBOUND']['plant_id'] = self.fusion_northbound_plant_id.text()
            
            self.fusion_config['SETTINGS']['time_interval'] = str(self.fusion_time_interval.value())
            self.fusion_config['SETTINGS']['alarm_enabled'] = str(self.fusion_alarm_enabled.isChecked())
            self.fusion_config['SETTINGS']['data_retention_days'] = str(self.fusion_data_retention.value())
            
            # Salva i file
            save_config_file(os.path.join(self.config_dir, "aurora_config.ini"), self.aurora_config)
            save_config_file(os.path.join(self.config_dir, "fusion_config.ini"), self.fusion_config)
            
            # Mostra messaggio di conferma
            QtWidgets.QMessageBox.information(
                self,
                "Configurazione salvata",
                "Le configurazioni sono state salvate con successo.\n"
                "Riavviare il server per applicare le modifiche."
            )
            
            # Chiudi il dialog
            self.accept()
    
    class ControlPanel(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("SSEM - Pannello di Controllo")
            self.setWindowIcon(QtGui.QIcon("static/favicon.ico"))
            self.setGeometry(100, 100, 500, 400)
            self.setMinimumSize(500, 500)
            
            # Widget centrale
            central_widget = QtWidgets.QWidget()
            self.setCentralWidget(central_widget)
            
            # Layout principale
            main_layout = QtWidgets.QVBoxLayout(central_widget)
            main_layout.setContentsMargins(20, 20, 20, 20)
            main_layout.setSpacing(15)
            
            # Header
            header_layout = QtWidgets.QHBoxLayout()
            
            # Logo/Icon
            logo_label = QtWidgets.QLabel()
            logo_pixmap = QtGui.QPixmap("static/favicon.ico")
            if not logo_pixmap.isNull():
                logo_label.setPixmap(logo_pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio))
            header_layout.addWidget(logo_label)
            
            # Titolo
            title_layout = QtWidgets.QVBoxLayout()
            title_label = QtWidgets.QLabel("SSEM")
            title_font = QtGui.QFont()
            title_font.setBold(True)
            title_font.setPointSize(18)
            title_label.setFont(title_font)
            
            subtitle_label = QtWidgets.QLabel("AuroraVisione e FusionSolar")
            subtitle_font = QtGui.QFont()
            subtitle_font.setPointSize(10)
            subtitle_label.setFont(subtitle_font)
            
            title_layout.addWidget(title_label)
            title_layout.addWidget(subtitle_label)
            header_layout.addLayout(title_layout)
            header_layout.addStretch()
            
            main_layout.addLayout(header_layout)
            
            # Separatore
            separator = QtWidgets.QFrame()
            separator.setFrameShape(QtWidgets.QFrame.HLine)
            separator.setFrameShadow(QtWidgets.QFrame.Sunken)
            main_layout.addWidget(separator)
            
            # Stato del server
            status_layout = QtWidgets.QHBoxLayout()
            status_label_text = QtWidgets.QLabel("Stato:")
            status_label_text.setFixedWidth(60)
            status_layout.addWidget(status_label_text)
            
            self.status_label = QtWidgets.QLabel("Fermo")
            status_font = QtGui.QFont()
            status_font.setBold(True)
            self.status_label.setFont(status_font)
            status_layout.addWidget(self.status_label)
            
            self.status_indicator = QtWidgets.QLabel()
            self.status_indicator.setFixedSize(15, 15)
            self.update_status_indicator(False)
            status_layout.addWidget(self.status_indicator)
            
            status_layout.addStretch()
            main_layout.addLayout(status_layout)
            
            # Controlli server
            controls_layout = QtWidgets.QHBoxLayout()
            
            self.start_btn = QtWidgets.QPushButton("Avvia server")
            self.start_btn.setFixedHeight(40)
            self.start_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            self.start_btn.clicked.connect(self.start_server_action)
            controls_layout.addWidget(self.start_btn)
            
            self.stop_btn = QtWidgets.QPushButton("Ferma server")
            self.stop_btn.setFixedHeight(40)
            self.stop_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
            self.stop_btn.clicked.connect(self.stop_server_action)
            controls_layout.addWidget(self.stop_btn)
            
            main_layout.addLayout(controls_layout)
            
            # Separatore
            separator2 = QtWidgets.QFrame()
            separator2.setFrameShape(QtWidgets.QFrame.HLine)
            separator2.setFrameShadow(QtWidgets.QFrame.Sunken)
            main_layout.addWidget(separator2)
            
            # Azioni rapide
            actions_label = QtWidgets.QLabel("Azioni rapide")
            actions_font = QtGui.QFont()
            actions_font.setBold(True)
            actions_font.setPointSize(12)
            actions_label.setFont(actions_font)
            main_layout.addWidget(actions_label)
            
            # Griglia di azioni
            actions_grid = QtWidgets.QGridLayout()
            actions_grid.setSpacing(10)
            
            # Pulsante Apri Browser
            browser_btn = QtWidgets.QPushButton("Apri nel browser")
            browser_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
            browser_btn.clicked.connect(open_browser)
            browser_btn.setFixedHeight(50)
            actions_grid.addWidget(browser_btn, 0, 0)
            
            # Pulsante Configurazione
            config_btn = QtWidgets.QPushButton("Configurazione")
            config_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
            config_btn.clicked.connect(open_config_folder)
            config_btn.setFixedHeight(50)
            actions_grid.addWidget(config_btn, 0, 1)
            
            # Pulsante Log
            logs_btn = QtWidgets.QPushButton("Visualizza log")
            logs_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView))
            logs_btn.clicked.connect(open_logs)
            logs_btn.setFixedHeight(50)
            actions_grid.addWidget(logs_btn, 1, 0)
            
            # Pulsante Info
            info_btn = QtWidgets.QPushButton("Informazioni")
            info_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation))
            info_btn.clicked.connect(self.show_info)
            info_btn.setFixedHeight(50)
            actions_grid.addWidget(info_btn, 1, 1)
            
            # NUOVO PULSANTE: Editor Configurazioni
            config_editor_btn = QtWidgets.QPushButton("Editor Configurazioni")
            config_editor_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogListView))
            config_editor_btn.clicked.connect(self.open_config_editor)
            config_editor_btn.setFixedHeight(50)
            actions_grid.addWidget(config_editor_btn, 2, 0, 1, 2)  # Span 2 colonne
            
            main_layout.addLayout(actions_grid)
            
            # Spazio di espansione
            main_layout.addStretch()
            
            # Footer
            footer_layout = QtWidgets.QHBoxLayout()
            footer_layout.addStretch()
            
            version_label = QtWidgets.QLabel("Versione 2.4.0")
            version_font = QtGui.QFont()
            version_font.setItalic(True)
            version_label.setFont(version_font)
            footer_layout.addWidget(version_label)
            
            main_layout.addLayout(footer_layout)
            
            # Aggiorna lo stato iniziale dell'UI
            self.update_ui()
            
            # Timer per aggiornare l'interfaccia
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.update_ui)
            self.timer.start(1000)  # Aggiorna ogni secondo
        
        # NUOVA FUNZIONE: Apri editor configurazioni
        def open_config_editor(self):
            config_editor = ConfigEditorDialog(self, config_dir="config")
            config_editor.exec_()
            
        def start_server_action(self):
            start_server()
            self.update_ui()
        
        def stop_server_action(self):
            stop_server()
            self.update_ui()
        
        def update_status_indicator(self, running):
            if running:
                self.status_indicator.setStyleSheet("background-color: #4CAF50; border-radius: 7px;")
            else:
                self.status_indicator.setStyleSheet("background-color: #F44336; border-radius: 7px;")
        
        def update_ui(self):
            if server_running:
                self.status_label.setText("In esecuzione")
                self.status_label.setStyleSheet("color: #4CAF50;")
            else:
                self.status_label.setText("Fermo")
                self.status_label.setStyleSheet("color: #F44336;")
            
            self.update_status_indicator(server_running)
            self.start_btn.setEnabled(not server_running)
            self.stop_btn.setEnabled(server_running)
        
        def show_info(self):
            QtWidgets.QMessageBox.information(
                self,
                "Informazioni su SSEM",
                "Stefano Solidoro\n\n"
                "Versione 2.4.0\n\n"
                "Applicazione per il monitoraggio di impianti fotovoltaici\n"
                "FusionSolar e AuroraVision"
            )
            
        def closeEvent(self, event):
            # Chiudere veramente l'app e fermare il server
            if server_running:
                reply = QtWidgets.QMessageBox.question(
                    self, 
                    'Chiusura applicazione',
                    'Il server è in esecuzione. Vuoi fermarlo e chiudere l\'applicazione?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    stop_server()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()

# Implementazione per Tkinter
else:
    class TkConfigEditor:
        def __init__(self, parent, config_dir="config"):
            self.parent = parent
            self.config_dir = config_dir
            self.dialog = tk.Toplevel(parent)
            self.dialog.title("Editor Configurazioni")
            self.dialog.geometry("600x500")
            self.dialog.minsize(600, 500)
            
            self.aurora_config = configparser.ConfigParser()
            self.fusion_config = configparser.ConfigParser()
            
            # Carica le configurazioni
            self.aurora_config.read(os.path.join(config_dir, "aurora_config.ini"))
            self.fusion_config.read(os.path.join(config_dir, "fusion_config.ini"))
            
            self.setup_ui()
            
        def setup_ui(self):
            # Notebook (Tab widget)
            self.notebook = ttk.Notebook(self.dialog)
            self.notebook.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Tab per AuroraVision
            aurora_tab = ttk.Frame(self.notebook)
            self.notebook.add(aurora_tab, text="AuroraVision")
            
            # Tab per FusionSolar
            fusion_tab = ttk.Frame(self.notebook)
            self.notebook.add(fusion_tab, text="FusionSolar")
            
            # Configura il tab AuroraVision
            self.setup_aurora_tab(aurora_tab)
            
            # Configura il tab FusionSolar
            self.setup_fusion_tab(fusion_tab)
            
            # Pulsanti di azione
            button_frame = ttk.Frame(self.dialog)
            button_frame.pack(fill="x", padx=20, pady=10)
            
            ttk.Button(button_frame, text="Annulla", command=self.dialog.destroy).pack(side="right", padx=5)
            ttk.Button(button_frame, text="Salva", command=self.save_configurations).pack(side="right", padx=5)
        
        def setup_aurora_tab(self, tab):
            # Frame con scrollbar per il contenuto
            canvas = tk.Canvas(tab)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Frame contenitore
            content_frame = ttk.Frame(scrollable_frame)
            content_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Gruppo Credenziali
            cred_frame = ttk.LabelFrame(content_frame, text="Credenziali")
            cred_frame.pack(fill="x", padx=5, pady=5)
            
            # Username
            ttk.Label(cred_frame, text="Username:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.aurora_username = ttk.Entry(cred_frame)
            self.aurora_username.insert(0, self.aurora_config.get('CREDENTIALS', 'username', fallback=''))
            self.aurora_username.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            # Password
            ttk.Label(cred_frame, text="Password:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.aurora_password = ttk.Entry(cred_frame, show="*")
            self.aurora_password.insert(0, self.aurora_config.get('CREDENTIALS', 'password', fallback=''))
            self.aurora_password.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
            
            # Entity IDs
            ttk.Label(cred_frame, text="ID Entità (separati da virgola):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            self.aurora_entity_ids = ttk.Entry(cred_frame)
            self.aurora_entity_ids.insert(0, self.aurora_config.get('CREDENTIALS', 'entity_ids', fallback=''))
            self.aurora_entity_ids.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            
            # Entity Aliases
            ttk.Label(cred_frame, text="Alias Entità (separati da virgola):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
            self.aurora_entity_aliases = ttk.Entry(cred_frame)
            self.aurora_entity_aliases.insert(0, self.aurora_config.get('CREDENTIALS', 'entity_aliases', fallback=''))
            self.aurora_entity_aliases.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
            
            # Configurare le colonne per adattarsi
            cred_frame.columnconfigure(1, weight=1)
            
            # Gruppo Impostazioni
            settings_frame = ttk.LabelFrame(content_frame, text="Impostazioni")
            settings_frame.pack(fill="x", padx=5, pady=5)
            
            # Time Interval
            ttk.Label(settings_frame, text="Intervallo di aggiornamento (secondi):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.aurora_time_interval = ttk.Spinbox(settings_frame, from_=60, to=3600, increment=60)
            self.aurora_time_interval.insert(0, self.aurora_config.get('SETTINGS', 'time_interval', fallback='300'))
            self.aurora_time_interval.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            # Alarm Enabled
            ttk.Label(settings_frame, text="Abilitare allarmi:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.aurora_alarm_enabled = tk.BooleanVar()
            self.aurora_alarm_enabled.set(self.aurora_config.getboolean('SETTINGS', 'alarm_enabled', fallback=True))
            ttk.Checkbutton(settings_frame, variable=self.aurora_alarm_enabled).grid(row=1, column=1, sticky="w", padx=5, pady=5)
            
            # Data Retention
            ttk.Label(settings_frame, text="Conservazione dati (giorni):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            self.aurora_data_retention = ttk.Spinbox(settings_frame, from_=1, to=365, increment=1)
            self.aurora_data_retention.insert(0, self.aurora_config.get('SETTINGS', 'data_retention_days', fallback='30'))
            self.aurora_data_retention.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            
            # Configurare le colonne per adattarsi
            settings_frame.columnconfigure(1, weight=1)
        
        def setup_fusion_tab(self, tab):
            # Frame con scrollbar per il contenuto
            canvas = tk.Canvas(tab)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Frame contenitore
            content_frame = ttk.Frame(scrollable_frame)
            content_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Gruppo Credenziali
            cred_frame = ttk.LabelFrame(content_frame, text="Credenziali")
            cred_frame.pack(fill="x", padx=5, pady=5)
            
            # Username
            ttk.Label(cred_frame, text="Username:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.fusion_username = ttk.Entry(cred_frame)
            self.fusion_username.insert(0, self.fusion_config.get('CREDENTIALS', 'username', fallback=''))
            self.fusion_username.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            # Password
            ttk.Label(cred_frame, text="Password:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.fusion_password = ttk.Entry(cred_frame, show="*")
            self.fusion_password.insert(0, self.fusion_config.get('CREDENTIALS', 'password', fallback=''))
            self.fusion_password.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
            
            # Subdomain
            ttk.Label(cred_frame, text="Sottodominio:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            self.fusion_subdomain = ttk.Entry(cred_frame)
            self.fusion_subdomain.insert(0, self.fusion_config.get('CREDENTIALS', 'subdomain', fallback=''))
            self.fusion_subdomain.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            
            # Captcha Model Path
            ttk.Label(cred_frame, text="Percorso modello captcha:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
            self.fusion_captcha_model = ttk.Entry(cred_frame)
            self.fusion_captcha_model.insert(0, self.fusion_config.get('CREDENTIALS', 'captcha_model_path', fallback=''))
            self.fusion_captcha_model.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
            
            # Plant Name
            ttk.Label(cred_frame, text="Nome impianto:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
            self.fusion_plant_name = ttk.Entry(cred_frame)
            self.fusion_plant_name.insert(0, self.fusion_config.get('CREDENTIALS', 'plant_name', fallback=''))
            self.fusion_plant_name.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
            
            # Configurare le colonne per adattarsi
            cred_frame.columnconfigure(1, weight=1)
            
            # Gruppo Northbound (se esiste nella configurazione)
            if self.fusion_config.has_section('NORTHBOUND'):
                northbound_frame = ttk.LabelFrame(content_frame, text="Northbound")
                northbound_frame.pack(fill="x", padx=5, pady=5)
                
                # Enabled
                ttk.Label(northbound_frame, text="Abilitato:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
                self.fusion_northbound_enabled = tk.BooleanVar()
                self.fusion_northbound_enabled.set(self.fusion_config.getboolean('NORTHBOUND', 'enabled', fallback=False))
                ttk.Checkbutton(northbound_frame, variable=self.fusion_northbound_enabled).grid(row=0, column=1, sticky="w", padx=5, pady=5)
                
                # Username
                ttk.Label(northbound_frame, text="Username:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
                self.fusion_northbound_username = ttk.Entry(northbound_frame)
                self.fusion_northbound_username.insert(0, self.fusion_config.get('NORTHBOUND', 'username', fallback=''))
                self.fusion_northbound_username.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
                
                # Password
                ttk.Label(northbound_frame, text="Password:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
                self.fusion_northbound_password = ttk.Entry(northbound_frame, show="*")
                self.fusion_northbound_password.insert(0, self.fusion_config.get('NORTHBOUND', 'password', fallback=''))
                self.fusion_northbound_password.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
                
                # Plant ID
                ttk.Label(northbound_frame, text="ID Impianto:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
                self.fusion_northbound_plant_id = ttk.Entry(northbound_frame)
                self.fusion_northbound_plant_id.insert(0, self.fusion_config.get('NORTHBOUND', 'plant_id', fallback=''))
                self.fusion_northbound_plant_id.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
                
                # Configurare le colonne per adattarsi
                northbound_frame.columnconfigure(1, weight=1)
            
            # Gruppo Impostazioni
            settings_frame = ttk.LabelFrame(content_frame, text="Impostazioni")
            settings_frame.pack(fill="x", padx=5, pady=5)
            
            # Time Interval
            ttk.Label(settings_frame, text="Intervallo di aggiornamento (secondi):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.fusion_time_interval = ttk.Spinbox(settings_frame, from_=60, to=3600, increment=60)
            self.fusion_time_interval.insert(0, self.fusion_config.get('SETTINGS', 'time_interval', fallback='300'))
            self.fusion_time_interval.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            # Alarm Enabled
            ttk.Label(settings_frame, text="Abilitare allarmi:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.fusion_alarm_enabled = tk.BooleanVar()
            self.fusion_alarm_enabled.set(self.fusion_config.getboolean('SETTINGS', 'alarm_enabled', fallback=True))
            ttk.Checkbutton(settings_frame, variable=self.fusion_alarm_enabled).grid(row=1, column=1, sticky="w", padx=5, pady=5)
            
            # Data Retention
            ttk.Label(settings_frame, text="Conservazione dati (giorni):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            self.fusion_data_retention = ttk.Spinbox(settings_frame, from_=1, to=365, increment=1)
            self.fusion_data_retention.insert(0, self.fusion_config.get('SETTINGS', 'data_retention_days', fallback='30'))
            self.fusion_data_retention.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            
            # Configurare le colonne per adattarsi
            settings_frame.columnconfigure(1, weight=1)
        
        def save_configurations(self):
            # Salva configurazione AuroraVision
            self.aurora_config['CREDENTIALS']['username'] = self.aurora_username.get()
            self.aurora_config['CREDENTIALS']['password'] = self.aurora_password.get()
            self.aurora_config['CREDENTIALS']['entity_ids'] = self.aurora_entity_ids.get()
            self.aurora_config['CREDENTIALS']['entity_aliases'] = self.aurora_entity_aliases.get()
            
            self.aurora_config['SETTINGS']['time_interval'] = self.aurora_time_interval.get()
            self.aurora_config['SETTINGS']['alarm_enabled'] = str(self.aurora_alarm_enabled.get())
            self.aurora_config['SETTINGS']['data_retention_days'] = self.aurora_data_retention.get()
            
            # Salva configurazione FusionSolar
            self.fusion_config['CREDENTIALS']['username'] = self.fusion_username.get()
            self.fusion_config['CREDENTIALS']['password'] = self.fusion_password.get()
            self.fusion_config['CREDENTIALS']['subdomain'] = self.fusion_subdomain.get()
            self.fusion_config['CREDENTIALS']['captcha_model_path'] = self.fusion_captcha_model.get()
            self.fusion_config['CREDENTIALS']['plant_name'] = self.fusion_plant_name.get()
            
            if self.fusion_config.has_section('NORTHBOUND'):
                self.fusion_config['NORTHBOUND']['enabled'] = str(self.fusion_northbound_enabled.get())
                self.fusion_config['NORTHBOUND']['username'] = self.fusion_northbound_username.get()
                self.fusion_config['NORTHBOUND']['password'] = self.fusion_northbound_password.get()
                self.fusion_config['NORTHBOUND']['plant_id'] = self.fusion_northbound_plant_id.get()
            
            self.fusion_config['SETTINGS']['time_interval'] = self.fusion_time_interval.get()
            self.fusion_config['SETTINGS']['alarm_enabled'] = str(self.fusion_alarm_enabled.get())
            self.fusion_config['SETTINGS']['data_retention_days'] = self.fusion_data_retention.get()
            
            # Salva i file
            save_config_file(os.path.join(self.config_dir, "aurora_config.ini"), self.aurora_config)
            save_config_file(os.path.join(self.config_dir, "fusion_config.ini"), self.fusion_config)
            
            # Mostra messaggio di conferma
            import tkinter.messagebox as messagebox
            messagebox.showinfo(
                "Configurazione salvata",
                "Le configurazioni sono state salvate con successo.\n"
                "Riavviare il server per applicare le modifiche."
            )
            
            # Chiudi il dialog
            self.dialog.destroy()
    
    class TkApp:
        def __init__(self, root):
            self.root = root
            root.title("SSEM - Pannello di Controllo")
            root.geometry("500x400")
            root.minsize(500, 400)
            
            # Stile
            style = ttk.Style()
            style.configure("TButton", padding=6, relief="flat", font=('Helvetica', 10))
            style.configure("TLabel", font=('Helvetica', 10))
            style.configure("Header.TLabel", font=('Helvetica', 14, 'bold'))
            style.configure("Subheader.TLabel", font=('Helvetica', 12))
            style.configure("Title.TLabel", font=('Helvetica', 18, 'bold'))
            style.configure("Footer.TLabel", font=('Helvetica', 9, 'italic'))
            
            # Frame principale
            main_frame = ttk.Frame(root, padding="20 20 20 20")
            main_frame.pack(fill="both", expand=True)
            
            # Header
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill="x", pady=(0, 15))
            
            title_label = ttk.Label(header_frame, text="SSEM", style="Title.TLabel")
            title_label.pack(anchor="w")
            
            subtitle_label = ttk.Label(header_frame, text="Sistema di Sorveglianza Energetica Monitorata")
            subtitle_label.pack(anchor="w")
            
            # Separator
            separator1 = ttk.Separator(main_frame, orient="horizontal")
            separator1.pack(fill="x", pady=(0, 15))
            
            # Stato del server
            status_frame = ttk.Frame(main_frame)
            status_frame.pack(fill="x", pady=(0, 10))
            
            status_text = ttk.Label(status_frame, text="Stato:")
            status_text.pack(side="left")
            
            self.status_label = ttk.Label(status_frame, text="Fermo", foreground="red", font=('Helvetica', 10, 'bold'))
            self.status_label.pack(side="left", padx=(5, 0))
            
            # Controlli server
            controls_frame = ttk.Frame(main_frame)
            controls_frame.pack(fill="x", pady=(0, 15))
            
            self.start_btn = ttk.Button(controls_frame, text="Avvia server", command=self.start_server_action)
            self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            self.stop_btn = ttk.Button(controls_frame, text="Ferma server", command=self.stop_server_action)
            self.stop_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
            
            # Separator
            separator2 = ttk.Separator(main_frame, orient="horizontal")
            separator2.pack(fill="x", pady=(0, 15))
            
            # Azioni rapide
            actions_label = ttk.Label(main_frame, text="Azioni rapide", style="Subheader.TLabel")
            actions_label.pack(anchor="w", pady=(0, 10))
            
            # Frame per le azioni
            actions_frame = ttk.Frame(main_frame)
            actions_frame.pack(fill="both", expand=True)
            
            # Configura le colonne e righe per essere responsive
            actions_frame.columnconfigure(0, weight=1)
            actions_frame.columnconfigure(1, weight=1)
            actions_frame.rowconfigure(0, weight=1)
            actions_frame.rowconfigure(1, weight=1)
            actions_frame.rowconfigure(2, weight=1)  # Aggiunta una riga per il nuovo pulsante
            
            # Pulsante Apri Browser
            browser_btn = ttk.Button(actions_frame, text="Apri nel browser", command=open_browser)
            browser_btn.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            
            # Pulsante Configurazione
            config_btn = ttk.Button(actions_frame, text="Configurazione", command=open_config_folder)
            config_btn.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
            
            # Pulsante Log
            logs_btn = ttk.Button(actions_frame, text="Visualizza log", command=open_logs)
            logs_btn.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            
            # Pulsante Info
            info_btn = ttk.Button(actions_frame, text="Informazioni", command=self.show_info)
            info_btn.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
            
            # NUOVO PULSANTE: Editor Configurazioni
            config_editor_btn = ttk.Button(actions_frame, text="Editor Configurazioni", command=self.open_config_editor)
            config_editor_btn.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
            
            # Footer
            footer_frame = ttk.Frame(main_frame)
            footer_frame.pack(fill="x", pady=(15, 0))
            
            version_label = ttk.Label(footer_frame, text="Versione 2.4.0", style="Footer.TLabel")
            version_label.pack(side="right")
            
            # Aggiorna lo stato iniziale dell'UI
            self.update_ui()
            
            # Aggiorna l'UI periodicamente
            self.update_timer()
            
            # Gestione della chiusura
            root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # NUOVA FUNZIONE: Apri editor configurazioni
        def open_config_editor(self):
            config_editor = TkConfigEditor(self.root, config_dir="config")
        
        def start_server_action(self):
            start_server()
            self.update_ui()
        
        def stop_server_action(self):
            stop_server()
            self.update_ui()
        
        def update_ui(self):
            if server_running:
                self.status_label.config(text="In esecuzione", foreground="green")
                self.start_btn.config(state="disabled")
                self.stop_btn.config(state="normal")
            else:
                self.status_label.config(text="Fermo", foreground="red")
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
        
        def update_timer(self):
            self.update_ui()
            self.root.after(1000, self.update_timer)  # Aggiorna ogni secondo
        
        def show_info(self):
            import tkinter.messagebox as messagebox
            messagebox.showinfo(
                "Informazioni su SSEM",
                "SSEM \n\n"
                "Versione 2.4.0\n\n"
                "Applicazione per il monitoraggio di impianti fotovoltaici\n"
                "FusionSolar e AuroraVision"
            )
        
        def on_closing(self):
            import tkinter.messagebox as messagebox
            
            if server_running:
                result = messagebox.askyesno(
                    "Chiusura applicazione",
                    "Il server è in esecuzione. Vuoi fermarlo e chiudere l'applicazione?"
                )
                
                if result:
                    stop_server()
                    self.root.destroy()
            else:
                self.root.destroy()

if __name__ == "__main__":
    # Non avviare il server automaticamente
    
    if USE_QT:
        # Create PyQt application
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle("Fusion")  # Use Fusion style for a modern look
        
        # Create and show the control panel
        control_panel = ControlPanel()
        control_panel.show()
        
        sys.exit(app.exec_())
    else:
        # Create Tkinter application
        root = tk.Tk()
        app = TkApp(root)
        root.mainloop()
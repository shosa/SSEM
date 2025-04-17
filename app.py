"""
SSEM - Sistema di Sorveglianza Energetica Monitorata
Applicazione per il monitoraggio di impianti fotovoltaici FusionSolar e AuroraVision

Entry point dell'applicazione Flask con pannello di controllo e integrazione systray.
"""
import os
import sys
import logging
import threading
import webbrowser
import time
from flask import Flask

# Verifica se PyQt5 è disponibile, altrimenti usa Tkinter come fallback
try:
    from PyQt5 import QtWidgets, QtGui, QtCore
    USE_QT = True
except ImportError:
    import tkinter as tk
    import tkinter.messagebox as messagebox
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
    
    # Avvia il monitoraggio
    plant_manager.start_monitoring()
    
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
        
        # Apri il browser dopo un breve ritardo
        threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()

def stop_server():
    """Ferma il server"""
    global server_running, plant_manager
    
    if server_running and plant_manager:
        # Prima fermiamo il monitoraggio
        plant_manager.stop_monitoring()
        server_running = False
        logger.info("Server SSEM fermato")
        
        # In una vera implementazione, avresti bisogno di un modo più robusto per
        # fermare un server Flask in esecuzione. Questo dipende dal web server WSGI.
        # Per semplicità qui stiamo solo aggiornando il flag.

def restart_server():
    """Riavvia il server"""
    stop_server()
    time.sleep(1)  # Attendi che il server si fermi
    start_server()
    logger.info("Server SSEM riavviato")

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

# Implementazione GUI con PyQt5
if USE_QT:
    class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
        def __init__(self, icon, parent=None):
            QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
            self.setToolTip('SSEM')
            
            menu = QtWidgets.QMenu(parent)
            
            # Azioni del menu
            open_action = menu.addAction("Apri SSEM")
            open_action.triggered.connect(open_browser)
            
            menu.addSeparator()
            
            restart_action = menu.addAction("Riavvia Server")
            restart_action.triggered.connect(restart_server)
            
            open_config_action = menu.addAction("Configurazione")
            open_config_action.triggered.connect(open_config_folder)
            
            open_logs_action = menu.addAction("Visualizza Log")
            open_logs_action.triggered.connect(open_logs)
            
            menu.addSeparator()
            
            exit_action = menu.addAction("Esci")
            exit_action.triggered.connect(self.exit_app)
            
            self.setContextMenu(menu)
            self.activated.connect(self.on_tray_icon_activated)
            
            # Creiamo anche una finestra di controllo
            self.control_panel = ControlPanel()
        
        def on_tray_icon_activated(self, reason):
            if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
                self.control_panel.show()
        
        def exit_app(self):
            stop_server()
            QtWidgets.QApplication.quit()
    
    class ControlPanel(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("SSEM - Pannello di Controllo")
            self.setWindowIcon(QtGui.QIcon("static/favicon.ico"))
            self.setGeometry(100, 100, 400, 300)
            
            # Widget centrale
            central_widget = QtWidgets.QWidget()
            self.setCentralWidget(central_widget)
            
            # Layout principale
            layout = QtWidgets.QVBoxLayout(central_widget)
            
            # Titolo
            title_label = QtWidgets.QLabel("SSEM - Sistema di Sorveglianza Energetica Monitorata")
            title_label.setAlignment(QtCore.Qt.AlignCenter)
            font = QtGui.QFont()
            font.setBold(True)
            font.setPointSize(14)
            title_label.setFont(font)
            layout.addWidget(title_label)
            
            # Stato del server
            status_group = QtWidgets.QGroupBox("Stato Server")
            status_layout = QtWidgets.QVBoxLayout(status_group)
            
            self.status_label = QtWidgets.QLabel("Server: In esecuzione" if server_running else "Server: Fermo")
            status_layout.addWidget(self.status_label)
            
            # Pulsanti di controllo server
            btn_layout = QtWidgets.QHBoxLayout()
            
            self.start_btn = QtWidgets.QPushButton("Avvia")
            self.start_btn.clicked.connect(self.start_server_action)
            btn_layout.addWidget(self.start_btn)
            
            self.stop_btn = QtWidgets.QPushButton("Ferma")
            self.stop_btn.clicked.connect(self.stop_server_action)
            btn_layout.addWidget(self.stop_btn)
            
            self.restart_btn = QtWidgets.QPushButton("Riavvia")
            self.restart_btn.clicked.connect(restart_server)
            btn_layout.addWidget(self.restart_btn)
            
            status_layout.addLayout(btn_layout)
            layout.addWidget(status_group)
            
            # Pulsanti di azione
            action_group = QtWidgets.QGroupBox("Azioni")
            action_layout = QtWidgets.QVBoxLayout(action_group)
            
            open_browser_btn = QtWidgets.QPushButton("Apri nel Browser")
            open_browser_btn.clicked.connect(open_browser)
            action_layout.addWidget(open_browser_btn)
            
            open_config_btn = QtWidgets.QPushButton("Apri Configurazione")
            open_config_btn.clicked.connect(open_config_folder)
            action_layout.addWidget(open_config_btn)
            
            open_logs_btn = QtWidgets.QPushButton("Visualizza Log")
            open_logs_btn.clicked.connect(open_logs)
            action_layout.addWidget(open_logs_btn)
            
            layout.addWidget(action_group)
            
            # Pulsante di uscita
            exit_btn = QtWidgets.QPushButton("Esci")
            exit_btn.clicked.connect(QtWidgets.QApplication.quit)
            layout.addWidget(exit_btn)
            
            # Timer per aggiornare l'interfaccia
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.update_ui)
            self.timer.start(1000)  # Aggiorna ogni secondo
            
            # Aggiorna lo stato iniziale dell'UI
            self.update_ui()
        
        def start_server_action(self):
            start_server()
            self.update_ui()
        
        def stop_server_action(self):
            stop_server()
            self.update_ui()
        
        def update_ui(self):
            self.status_label.setText("Server: In esecuzione" if server_running else "Server: Fermo")
            self.start_btn.setEnabled(not server_running)
            self.stop_btn.setEnabled(server_running)
        
        def closeEvent(self, event):
            # Non chiudere veramente l'app, solo nascondila
            event.ignore()
            self.hide()

# Implementazione GUI con Tkinter (fallback)
else:
    class TkApp:
        def __init__(self, root):
            self.root = root
            root.title("SSEM - Pannello di Controllo")
            root.geometry("400x300")
            root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Titolo
            title_label = ttk.Label(root, text="SSEM - Sistema di Sorveglianza Energetica Monitorata", font=("TkDefaultFont", 12, "bold"))
            title_label.pack(pady=10)
            
            # Frame per lo stato del server
            status_frame = ttk.LabelFrame(root, text="Stato Server")
            status_frame.pack(fill="x", padx=10, pady=5)
            
            self.status_label = ttk.Label(status_frame, text="Server: In esecuzione" if server_running else "Server: Fermo")
            self.status_label.pack(pady=5)
            
            # Frame per i pulsanti di controllo
            btn_frame = ttk.Frame(status_frame)
            btn_frame.pack(fill="x", pady=5)
            
            self.start_btn = ttk.Button(btn_frame, text="Avvia", command=self.start_server_action)
            self.start_btn.pack(side="left", padx=5, expand=True, fill="x")
            
            self.stop_btn = ttk.Button(btn_frame, text="Ferma", command=self.stop_server_action)
            self.stop_btn.pack(side="left", padx=5, expand=True, fill="x")
            
            self.restart_btn = ttk.Button(btn_frame, text="Riavvia", command=restart_server)
            self.restart_btn.pack(side="left", padx=5, expand=True, fill="x")
            
            # Frame per le azioni
            action_frame = ttk.LabelFrame(root, text="Azioni")
            action_frame.pack(fill="x", padx=10, pady=5)
            
            open_browser_btn = ttk.Button(action_frame, text="Apri nel Browser", command=open_browser)
            open_browser_btn.pack(fill="x", pady=2)
            
            open_config_btn = ttk.Button(action_frame, text="Apri Configurazione", command=open_config_folder)
            open_config_btn.pack(fill="x", pady=2)
            
            open_logs_btn = ttk.Button(action_frame, text="Visualizza Log", command=open_logs)
            open_logs_btn.pack(fill="x", pady=2)
            
            # Pulsante di uscita
            exit_btn = ttk.Button(root, text="Esci", command=self.exit_app)
            exit_btn.pack(pady=10)
            
            # Aggiorna lo stato iniziale dell'UI
            self.update_ui()
            
            # Aggiorna l'UI periodicamente
            self.update_timer()
        
        def start_server_action(self):
            start_server()
            self.update_ui()
        
        def stop_server_action(self):
            stop_server()
            self.update_ui()
        
        def update_ui(self):
            self.status_label.config(text="Server: In esecuzione" if server_running else "Server: Fermo")
            self.start_btn.config(state="disabled" if server_running else "normal")
            self.stop_btn.config(state="normal" if server_running else "disabled")
        
        def update_timer(self):
            self.update_ui()
            self.root.after(1000, self.update_timer)  # Aggiorna ogni secondo
        
        def on_closing(self):
            # Minimizza invece di chiudere
            self.root.withdraw()
        
        def exit_app(self):
            stop_server()
            self.root.destroy()
            sys.exit(0)

    def create_tray_icon():
        """Crea un'icona nella systray con Tkinter"""
        # Questa è una versione molto semplificata, in quanto Tkinter non ha un supporto
        # nativo per le icone nella systray come PyQt5
        root = tk.Tk()
        root.withdraw()  # Nascondi la finestra principale
        
        app = TkApp(tk.Toplevel(root))
        
        try:
            import pystray
            from PIL import Image
            
            # Usa pystray se disponibile
            # Crea un'icona per la systray
            icon = pystray.Icon("ssem")
            icon.title = "SSEM"
            
            # Menu della systray
            icon.menu = pystray.Menu(
                pystray.MenuItem("Apri SSEM", lambda: open_browser()),
                pystray.MenuItem("Pannello di controllo", lambda: root.deiconify()),
                pystray.MenuItem("Esci", lambda: app.exit_app())
            )
            
            # Avvia l'icona nella systray
            icon.run()
        except ImportError:
            # Se pystray non è disponibile, usa solo la finestra
            pass
        
        root.mainloop()

if __name__ == "__main__":
    # Avvia il server immediatamente
    start_server()
    
    if USE_QT:
        # Crea l'applicazione PyQt
        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)  # Permette l'esecuzione in background
        
        # Crea l'icona per la systray
        icon = QtGui.QIcon("static/favicon.ico")
        if not icon.isNull():
            tray_icon = SystemTrayIcon(icon)
        else:
            # Usa un'icona di fallback da Qt
            tray_icon = SystemTrayIcon(app.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
        
        tray_icon.show()
        tray_icon.control_panel.show()  # Mostra il pannello di controllo all'avvio
        
        sys.exit(app.exec_())
    else:
        # Crea l'applicazione Tkinter
        create_tray_icon()
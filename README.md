# SSEM

Sistema di monitoraggio in tempo reale per impianti fotovoltaici AuroraVision e FusionSolar.

## Caratteristiche

- **Monitoraggio in tempo reale** degli impianti fotovoltaici
- **Rilevamento di impianti offline** con segnalazione visuale
- **Dashboard informativa** con potenza totale e stato degli impianti
- **Supporto per più impianti** AuroraVision sotto un'unica autenticazione
- **Architettura modulare** facilmente estendibile

## Struttura del progetto

```
solar_monitor/
├── app.py                    # Entry point dell'applicazione
├── config/                   # Directory per file di configurazione
│   ├── aurora_config.ini     # Configurazione AuroraVision
│   └── fusion_config.ini     # Configurazione FusionSolar
├── models/                   # Directory per modelli di dati
│   ├── __init__.py
│   ├── plant.py              # Classe base Plant
│   ├── aurora_plant.py       # Implementazione AuroraVision
│   └── fusion_plant.py       # Implementazione FusionSolar
├── services/                 # Directory per servizi
│   ├── __init__.py
│   ├── plant_manager.py      # Servizio centralizzato di gestione impianti
│   └── session_managers.py   # Gestori di sessione per le API
├── routes/                   # Directory per route Flask
│   ├── __init__.py
│   └── api.py                # Definizione delle route API
├── static/                   # Directory per file statici
│   └── js/
│       └── monitor.js        # JavaScript per l'interfaccia utente
└── templates/                # Directory per i template HTML
    └── index.html            # Template principale
```

## Requisiti

- Python 3.7+
- Flask
- Requests

Opzionale (per supporto FusionSolar):
- fusion_solar_py

## Installazione

1. Clona il repository o scarica i file in una directory
2. Crea un ambiente virtuale e attivalo:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Installa le dipendenze:
   ```
   pip install flask requests
   ```
4. Opzionale: Installa il supporto per FusionSolar:
   ```
   pip install fusion-solar-py
   ```
5. Copia il file del modello CAPTCHA nella directory principale (necessario solo per FusionSolar)

## Configurazione

I file di configurazione vengono creati automaticamente alla prima esecuzione nella directory `config/`. Modifica i file in base alle tue esigenze:

### aurora_config.ini

```ini
[CREDENTIALS]
username = username_auroravision
password = password_auroravision
entity_ids = 12345,67890
entity_aliases = Impianto1,Impianto2

[SETTINGS]
time_interval = 300
```

### fusion_config.ini

```ini
[CREDENTIALS]
username = username_fusionsolar
password = password_fusionsolar
subdomain = subdomain_fusionsolar
captcha_model_path = percorso/al/modello/captcha.onnx

[SETTINGS]
time_interval = 300
```

## Avvio

Per avviare l'applicazione:

```
python app.py
```

L'applicazione sarà disponibile all'indirizzo `http://localhost:5000`.

## Utilizzo

- La dashboard mostra lo stato di tutti gli impianti monitorati
- Il pulsante "Aggiorna" forza un aggiornamento immediato dei dati
- Il pulsante "Monitoraggio attivo/fermo" permette di attivare/disattivare il monitoraggio automatico
- Gli impianti sono visualizzati con codici colore:
  - **Verde**: Impianto attivo e in produzione
  - **Giallo**: Impianto connesso ma non in produzione
  - **Rosso**: Impianto offline o non raggiungibile

## API

L'applicazione espone le seguenti API REST:

- `GET /api/plants`: Restituisce lo stato di tutti gli impianti
- `GET /api/plants/<plant_id>`: Restituisce lo stato di un impianto specifico
- `GET /api/update`: Forza l'aggiornamento di tutti gli impianti
- `GET /api/monitoring/start`: Avvia il monitoraggio in background
- `GET /api/monitoring/stop`: Ferma il monitoraggio in background
- `GET /api/status`: Restituisce lo stato del sistema di monitoraggio

## Estensione

Per aggiungere supporto a nuovi tipi di impianti:

1. Crea una nuova classe nel modulo `models/` che estende la classe `Plant`
2. Implementa il metodo `check_connection()` per il nuovo tipo di impianto
3. Crea il gestore di sessione appropriato in `services/session_managers.py`
4. Aggiorna il `PlantManager` per supportare il nuovo tipo di impianto

## Licenza

Questo progetto è rilasciato sotto licenza MIT.
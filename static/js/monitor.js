/**
 * SolarMonitor - Script per l'interfaccia di monitoraggio impianti fotovoltaici
 */

// Stato del monitoraggio
let monitoringActive = true;

// Configurazione del sistema (valori predefiniti)
let config = {
    updateInterval: 30000,     // Intervallo di aggiornamento in ms (30 sec default)
    alarmOnZeroPower: true,    // Allarme quando potenza = 0
    beepFrequency: 800,        // Frequenza del beep in Hz
    beepDuration: 200,         // Durata del beep in ms
    beepInterval: 3000         // Intervallo tra i beep in ms
};

// Carica la configurazione dal localStorage se disponibile
function loadConfig() {
    const savedConfig = localStorage.getItem('solarMonitorConfig');
    if (savedConfig) {
        try {
            const parsedConfig = JSON.parse(savedConfig);
            config = { ...config, ...parsedConfig };
        } catch (e) {
            console.error("Errore nel caricamento della configurazione:", e);
        }
    }
}

// Salva la configurazione nel localStorage
function saveConfig() {
    try {
        localStorage.setItem('solarMonitorConfig', JSON.stringify(config));
    } catch (e) {
        console.error("Errore nel salvataggio della configurazione:", e);
    }
}

// Intervallo di aggiornamento
let autoRefreshInterval = null;

// Variabili per il beep
let audioContext = null;
let beepInterval = null;
let hasOfflineImpianti = false;
let hasZeroPowerImpianti = false;

/**
 * Inizializza l'AudioContext per il beep
 */
function initAudio() {
    try {
        // Crea l'AudioContext (funziona in tutti i browser moderni)
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        audioContext = new AudioContext();
    } catch (e) {
        console.error("Il browser non supporta Web Audio API");
    }
}

/**
 * Genera un semplice beep
 * @param {boolean} isZeroPower - se true, usa un tono diverso per l'allarme potenza zero
 */
function beep(isZeroPower = false) {
    if (!audioContext) return;
    
    try {
        // Crea un oscillatore (generatore di segnale)
        const oscillator = audioContext.createOscillator();
        // Crea un nodo per controllare il volume
        const gainNode = audioContext.createGain();
        
        // Configura l'oscillatore - frequenza diversa per tipo di allarme
        oscillator.type = "sine"; // Onda sinusoidale per un beep pulito
        oscillator.frequency.value = isZeroPower ? config.beepFrequency * 1.5 : config.beepFrequency; // Frequenza più alta per potenza zero
        
        // Configura il volume
        gainNode.gain.value = 0.3; // Volume basso (0-1)
        
        // Collega oscillatore -> volume -> output
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Avvia e ferma il beep
        oscillator.start();
        setTimeout(() => {
            oscillator.stop();
        }, config.beepDuration);
    } catch (e) {
        console.error("Errore nella generazione del beep:", e);
    }
}

/**
 * Gestisce l'allarme sonoro (beep)
 * @param {boolean} active - true per attivare l'allarme, false per disattivarlo
 * @param {boolean} isZeroPower - se true, usa un tono diverso per l'allarme potenza zero
 */
function toggleAlarm(active, isZeroPower = false) {
    // Disattiva l'allarme esistente se presente
    if (beepInterval) {
        clearInterval(beepInterval);
        beepInterval = null;
    }
    
    // Se richiesto attivo, avvia l'allarme
    if (active) {
        beep(isZeroPower); // Beep immediato
        beepInterval = setInterval(() => beep(isZeroPower), config.beepInterval); // Beep periodico
    }
}

/**
 * Semplifica il messaggio di errore per renderlo più leggibile
 * @param {string} errorMessage - Messaggio di errore originale
 * @returns {string} - Messaggio semplificato
 */
function simplifyErrorMessage(errorMessage) {
    if (!errorMessage) return "";
    
    // Se contiene errore di connessione
    if (errorMessage.includes("HTTPSConnectionPool") || 
        errorMessage.includes("NameResolutionError") || 
        errorMessage.includes("getaddrinfo failed")) {
        return "Errore di connessione: server non raggiungibile";
    }
    
    // Se contiene errore di autenticazione
    if (errorMessage.includes("401") || errorMessage.includes("403") || 
        errorMessage.includes("Authentication failed")) {
        return "Errore di autenticazione: credenziali non valide";
    }
    
    // Se contiene errore di client o sessione
    if (errorMessage.includes("Client non disponibile") || 
        errorMessage.includes("Sessione non disponibile")) {
        return "Impossibile stabilire connessione";
    }
    
    // Ritorna un messaggio semplificato generico
    return "Errore di comunicazione";
}

/**
 * Crea una card per un impianto usando il template
 * @param {Object} plant - Dati dell'impianto
 * @returns {HTMLElement} - Elemento DOM della card
 */
function createPlantCard(plant) {
    const template = document.getElementById('plantCardTemplate');
    const clone = document.importNode(template.content, true);
    
    const card = clone.querySelector('.plant-card');
    const nameEl = clone.querySelector('.plant-name');
    const statusEl = clone.querySelector('.plant-status');
    const statusIndicator = clone.querySelector('.status-indicator');
    const powerEl = clone.querySelector('.power-value');
    const updateTimeEl = clone.querySelector('.update-time');
    
    // Aggiungi message-container se non esiste nel template
    let messageContainer = clone.querySelector('.message-container');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.className = 'message-container mt-3';
        const cardBody = clone.querySelector('.card-body');
        if (cardBody) {
            cardBody.appendChild(messageContainer);
        }
    }
    
    nameEl.textContent = plant.name;
    powerEl.textContent = plant.power + ' kW';
    updateTimeEl.textContent = 'Aggiornato: ' + plant.last_update;
    
    // Determina se l'impianto ha potenza zero mentre è online
    const isZeroPower = plant.is_online && plant.power <= 0;
    
    // Imposta lo stato e il semaforo in base allo stato dell'impianto
    if (plant.is_online) {
        if (plant.power > 0) {
            statusEl.textContent = 'ONLINE';
            statusEl.classList.add('text-success');
            statusIndicator.classList.add('status-online');
            card.classList.add('plant-online');
        } else {
            statusEl.textContent = 'ATTENZIONE';
            statusEl.classList.add('text-warning');
            statusIndicator.classList.add('status-warning');
            card.classList.add('plant-warning', 'blinking-card');
            
            // Aggiunge messaggio warning per potenza zero
            const warningMsg = document.createElement('div');
            warningMsg.className = 'warning-message';
            warningMsg.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Impianto attivo ma produzione a zero';
            messageContainer.appendChild(warningMsg);
        }
    } else {
        statusEl.textContent = 'OFFLINE';
        statusEl.classList.add('text-danger');
        statusIndicator.classList.add('status-offline');
        card.classList.add('plant-offline', 'blinking-card');
        
        // Aggiunge messaggio di errore se presente
        if (plant.error_message) {
            const errorMsg = document.createElement('div');
            errorMsg.className = 'error-message';
            errorMsg.innerHTML = `<i class="bi bi-exclamation-circle"></i> ${simplifyErrorMessage(plant.error_message)}`;
            messageContainer.appendChild(errorMsg);
        }
    }
    
    return clone;
}

/**
 * Aggiorna le informazioni degli impianti
 */
function updatePlants() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Aggiornamento...';
    
    fetch('/api/plants')
        .then(response => response.json())
        .then(plants => {
            const plantsContainer = document.getElementById('plantsContainer');
            plantsContainer.innerHTML = '';
            
            let onlineCount = 0;
            let warningCount = 0;
            let offlineCount = 0;
            let newHasOfflineImpianti = false; // Resetta lo stato offline
            let newHasZeroPowerImpianti = false; // Resetta lo stato potenza zero
            
            // Mostra tutti gli impianti
            Object.entries(plants).forEach(([plantId, plant]) => {
                // Determina lo stato dell'impianto
                if (plant.is_online) {
                    if (plant.power > 0) {
                        onlineCount++;
                    } else {
                        warningCount++;
                        if (config.alarmOnZeroPower) {
                            newHasZeroPowerImpianti = true;
                        }
                    }
                } else {
                    offlineCount++;
                    newHasOfflineImpianti = true;
                }
                
                // Crea e aggiungi la card usando il template
                try {
                    const plantCard = createPlantCard(plant);
                    plantsContainer.appendChild(plantCard);
                } catch (error) {
                    console.error('Errore nella creazione della card per l\'impianto:', plant.name, error);
                }
            });
            
            // Aggiorna i contatori
            document.getElementById('onlineCount').textContent = onlineCount;
            document.getElementById('warningCount').textContent = warningCount;
            document.getElementById('offlineCount').textContent = offlineCount;
            
            // Controlla se lo stato degli allarmi è cambiato
            const alarmsChanged = (newHasOfflineImpianti !== hasOfflineImpianti || 
                                  newHasZeroPowerImpianti !== hasZeroPowerImpianti);
            
            hasOfflineImpianti = newHasOfflineImpianti;
            hasZeroPowerImpianti = newHasZeroPowerImpianti;
            
            if (alarmsChanged) {
                // Priorità all'allarme offline rispetto a potenza zero
                if (hasOfflineImpianti) {
                    toggleAlarm(true, false);
                } else if (hasZeroPowerImpianti) {
                    toggleAlarm(true, true);
                } else {
                    toggleAlarm(false);
                }
            }
            
            // Riabilita il pulsante
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Aggiorna';
        })
        .catch(error => {
            console.error('Errore durante il recupero dei dati:', error);
            
            // Riabilita il pulsante
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Aggiorna';
            
            // Mostra un messaggio di errore
            const plantsContainer = document.getElementById('plantsContainer');
            plantsContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Errore durante il recupero dei dati. Riprova più tardi.
                    </div>
                </div>
            `;
        });
}

/**
 * Forza l'aggiornamento di tutti gli impianti
 */
function forceUpdate() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Aggiornamento forzato...';
    
    fetch('/api/update')
        .then(response => response.json())
        .then(data => {
            // Aggiorna l'interfaccia con i nuovi dati
            updatePlants();
        })
        .catch(error => {
            console.error('Errore durante l\'aggiornamento forzato:', error);
            
            // Riabilita il pulsante
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Aggiorna';
            
            // Mostra un messaggio di errore
            const plantsContainer = document.getElementById('plantsContainer');
            plantsContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Errore durante l'aggiornamento forzato. Riprova più tardi.
                    </div>
                </div>
            `;
        });
}

/**
 * Gestisce lo stato del monitoraggio
 */
function toggleMonitoring() {
    const monitoringBtn = document.getElementById('monitoringBtn');
    monitoringBtn.disabled = true;
    
    const endpoint = monitoringActive ? '/api/monitoring/stop' : '/api/monitoring/start';
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            monitoringActive = !monitoringActive;
            monitoringBtn.disabled = false;
            
            if (monitoringActive) {
                monitoringBtn.className = 'btn btn-success';
                monitoringBtn.innerHTML = '<i class="bi bi-play-circle"></i> Monitoraggio attivo';
                
                // Riavvia l'intervallo di aggiornamento
                if (autoRefreshInterval) clearInterval(autoRefreshInterval);
                autoRefreshInterval = setInterval(updatePlants, config.updateInterval);
            } else {
                monitoringBtn.className = 'btn btn-danger';
                monitoringBtn.innerHTML = '<i class="bi bi-stop-circle"></i> Monitoraggio fermo';
                
                // Ferma l'intervallo di aggiornamento
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
                
                // Ferma l'allarme
                toggleAlarm(false);
            }
        })
        .catch(error => {
            console.error('Errore durante la modifica dello stato del monitoraggio:', error);
            monitoringBtn.disabled = false;
        });
}

/**
 * Silenzia l'allarme sonoro
 */
function silenceAlarm() {
    toggleAlarm(false);
    
    // Disattiva il pulsante di silenziamento
    const silenceBtn = document.getElementById('silenceBtn');
    if (silenceBtn) {
        silenceBtn.disabled = true;
        setTimeout(() => {
            silenceBtn.disabled = false;
        }, 30000); // Riabilita dopo 30 secondi
    }
}

/**
 * Mostra il modale delle impostazioni
 */
function showSettingsModal() {
    // Aggiorna i valori del form con la configurazione attuale
    document.getElementById('updateInterval').value = config.updateInterval / 1000; // Da ms a secondi
    document.getElementById('alarmOnZeroPower').checked = config.alarmOnZeroPower;
    document.getElementById('beepFrequency').value = config.beepFrequency;
    document.getElementById('beepInterval').value = config.beepInterval / 1000; // Da ms a secondi
    
    // Mostra il modale
    const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
    modal.show();
}

/**
 * Salva le impostazioni dal modale
 */
function saveSettings() {
    // Recupera i valori dal form
    config.updateInterval = parseInt(document.getElementById('updateInterval').value) * 1000; // Da secondi a ms
    config.alarmOnZeroPower = document.getElementById('alarmOnZeroPower').checked;
    config.beepFrequency = parseInt(document.getElementById('beepFrequency').value);
    config.beepInterval = parseInt(document.getElementById('beepInterval').value) * 1000; // Da secondi a ms
    
    // Salva la configurazione
    saveConfig();
    
    // Aggiorna l'intervallo di aggiornamento
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        if (monitoringActive) {
            autoRefreshInterval = setInterval(updatePlants, config.updateInterval);
        }
    }
    
    // Chiudi il modale
    const modalElement = document.getElementById('settingsModal');
    const modal = bootstrap.Modal.getInstance(modalElement);
    modal.hide();
    
    // Notifica l'utente
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        Impostazioni salvate con successo.
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container').prepend(alertDiv);
    
    // Rimuovi l'alert dopo 3 secondi
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

/**
 * Inizializza la pagina
 */
document.addEventListener('DOMContentLoaded', function() {
    // Carica la configurazione salvata
    loadConfig();
    
    // Inizializza l'audio
    initAudio();
    
    // Carica i dati iniziali
    updatePlants();
    
    // Aggiungi event listener per il pulsante di aggiornamento
    document.getElementById('refreshBtn').addEventListener('click', forceUpdate);
    
    // Aggiungi event listener per il pulsante di monitoraggio
    document.getElementById('monitoringBtn').addEventListener('click', toggleMonitoring);
    
    // Crea e aggiungi i pulsanti per silenziare l'allarme e le impostazioni
    const btnGroup = document.querySelector('.btn-group');
    
    // Pulsante silenzia allarme
    const silenceBtn = document.createElement('button');
    silenceBtn.id = 'silenceBtn';
    silenceBtn.className = 'btn btn-warning ms-2';
    silenceBtn.innerHTML = '<i class="bi bi-volume-mute"></i> Silenzia allarme';
    silenceBtn.addEventListener('click', silenceAlarm);
    btnGroup.appendChild(silenceBtn);
    
    // Pulsante impostazioni
    const settingsBtn = document.createElement('button');
    settingsBtn.id = 'settingsBtn';
    settingsBtn.className = 'btn btn-secondary ms-2';
    settingsBtn.innerHTML = '<i class="bi bi-gear"></i> Impostazioni';
    settingsBtn.addEventListener('click', showSettingsModal);
    btnGroup.appendChild(settingsBtn);
    
    // Crea il modale delle impostazioni
    const modalHtml = `
        <div class="modal fade" id="settingsModal" tabindex="-1" aria-labelledby="settingsModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="settingsModalLabel">Impostazioni</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="settingsForm">
                            <div class="mb-3">
                                <label for="updateInterval" class="form-label">Intervallo di aggiornamento DASHBOARD (no valori impianti) (in secondi)</label>
                                <input type="number" class="form-control" id="updateInterval" min="5" max="300" value="30">
                            </div>
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" id="alarmOnZeroPower">
                                <label class="form-check-label" for="alarmOnZeroPower">Allarme quando potenza = 0</label>
                            </div>
                            <div class="mb-3">
                                <label for="beepFrequency" class="form-label">Frequenza beep (Hz)</label>
                                <input type="number" class="form-control" id="beepFrequency" min="200" max="2000" value="800">
                                <div class="form-text">Valori più alti generano toni più acuti</div>
                            </div>
                            <div class="mb-3">
                                <label for="beepInterval" class="form-label">Intervallo tra i beep (secondi)</label>
                                <input type="number" class="form-control" id="beepInterval" min="1" max="10" value="3">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annulla</button>
                        <button type="button" class="btn btn-primary" onclick="saveSettings()">Salva</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Aggiungi il modale al DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Prima attivazione dell'audio richiede interazione utente
    document.body.addEventListener('click', function() {
        if (audioContext && audioContext.state === 'suspended') {
            audioContext.resume();
        }
    }, { once: true });
    
    // Imposta l'aggiornamento automatico
    if (monitoringActive) {
        autoRefreshInterval = setInterval(updatePlants, config.updateInterval);
    }
});
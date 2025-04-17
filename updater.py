import os
import requests
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

UPDATE_URL = "https://example.com/solarmonitor/latest.json"  # Sostituisci con il tuo URL di aggiornamento

def get_current_version():
    """Legge la versione corrente dal file version.txt"""
    version_file = Path("version.txt")
    if not version_file.exists():
        version_file = Path(os.path.dirname(sys.executable)) / "version.txt"
    
    if version_file.exists():
        with open(version_file, "r") as f:
            return f.read().strip()
    return "0.0.0"  # Versione predefinita

def check_for_updates():
    """Controlla se sono disponibili aggiornamenti"""
    current_version = get_current_version()
    
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code == 200:
            update_info = response.json()
            latest_version = update_info.get("version")
            
            if latest_version and latest_version > current_version:
                return {
                    "available": True,
                    "version": latest_version,
                    "download_url": update_info.get("download_url"),
                    "release_notes": update_info.get("release_notes", "")
                }
    except Exception as e:
        print(f"Errore durante il controllo degli aggiornamenti: {e}")
    
    return {"available": False}

def download_update(download_url):
    """Scarica l'aggiornamento"""
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "update.zip")
        
        response = requests.get(download_url, stream=True, timeout=30)
        with open(temp_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return temp_file
    except Exception as e:
        print(f"Errore durante il download dell'aggiornamento: {e}")
        return None

def install_update(update_file):
    """Installa l'aggiornamento"""
    try:
        temp_dir = tempfile.mkdtemp()
        
        # Estrai l'aggiornamento
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Esegui l'installer se presente
        installer_path = os.path.join(temp_dir, "setup.exe")
        if os.path.exists(installer_path):
            subprocess.Popen([installer_path])
            return True
        
        # Altrimenti, aggiorna i file manualmente
        app_dir = os.path.dirname(sys.executable)
        # ... codice per aggiornare i file manualmente ...
        
        return True
    except Exception as e:
        print(f"Errore durante l'installazione dell'aggiornamento: {e}")
        return False

def update_app():
    """Processo completo di aggiornamento"""
    update_info = check_for_updates()
    
    if update_info["available"]:
        print(f"È disponibile l'aggiornamento alla versione {update_info['version']}")
        
        # Scarica l'aggiornamento
        update_file = download_update(update_info["download_url"])
        if update_file:
            # Installa l'aggiornamento
            success = install_update(update_file)
            if success:
                print("Aggiornamento installato con successo. L'applicazione verrà riavviata.")
                return True
    
    return False
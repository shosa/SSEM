import os
import subprocess
import sys
import time
from datetime import datetime

def increment_version(version_str):
    """Incrementa la versione (semver)"""
    major, minor, patch = map(int, version_str.split('.'))
    patch += 1
    return f"{major}.{minor}.{patch}"

def update_version():
    """Incrementa e aggiorna il numero di versione"""
    with open('version.txt', 'r') as f:
        current_version = f.read().strip()
    
    new_version = increment_version(current_version)
    
    with open('version.txt', 'w') as f:
        f.write(new_version)
    
    print(f"Versione aggiornata: {current_version} -> {new_version}")
    return new_version

def build_executable():
    """Esegue il build dell'eseguibile"""
    subprocess.check_call([sys.executable, 'build.py'])

def create_installer():
    """Crea l'installer con Inno Setup"""
    print("Creazione dell'installer...")
    subprocess.check_call(['iscc', 'installer.iss'])
    print("Installer creato con successo")

def create_update_package(version):
    """Crea il pacchetto di aggiornamento e il file JSON delle info"""
    # Crea zip di aggiornamento
    update_zip = f'output/SSEM-Update-{version}.zip'
    subprocess.check_call(['7z', 'a', update_zip, './dist/SSEM/*'])
    
    # Crea file JSON con le info di aggiornamento
    update_json = f'output/latest.json'
    with open(update_json, 'w') as f:
        f.write(f"""{{
    "version": "{version}",
    "download_url": "https://example.com/SSEM/SSEM-Update-{version}.zip",
    "release_notes": "Aggiornamento automatico alla versione {version}\\nData: {datetime.now().strftime('%d/%m/%Y')}",
    "release_date": "{datetime.now().strftime('%Y-%m-%d')}"
}}""")
    
    print(f"Pacchetto di aggiornamento creato: {update_zip}")
    print(f"File info aggiornamento creato: {update_json}")

def main():
    """Esegue l'intero processo di rilascio"""
    # Aggiorna la versione
    version = update_version()
    
    # Build dell'eseguibile
    build_executable()
    
    # Crea l'installer
    create_installer()
    
    # Crea il pacchetto di aggiornamento
    create_update_package(version)
    
    print("\nRilascio completato con successo!")
    print(f"Versione: {version}")
    print("File creati:")
    print(f" - output/SSEM-{version}.zip (Archivio dell'applicazione)")
    print(f" - output/SSEM-Setup-{version}.exe (Installer)")
    print(f" - output/SSEM-Update-{version}.zip (Pacchetto di aggiornamento)")
    print(f" - output/latest.json (Informazioni per l'aggiornamento automatico)")

if __name__ == '__main__':
    main()
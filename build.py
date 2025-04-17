import os
import shutil
import subprocess
import sys

def get_version():
    with open('version.txt', 'r') as f:
        return f.read().strip()

def build_executable():
    print("Compilando il programma con PyInstaller...")
    subprocess.check_call(['pyinstaller', 'ssem.spec'])
    
    # Copia i file aggiuntivi richiesti nella dist
    version = get_version()
    print(f"Build completata per la versione {version}")
    
    # Crea la cartella di output se non esiste
    os.makedirs('output', exist_ok=True)
    
    # Archivia la build
    output_file = f'output/SSEM-{version}.zip'
    shutil.make_archive(
        f'output/SSEM-{version}', 
        'zip', 
        'dist/SSEM'
    )
    
    print(f"Build archiviata in {output_file}")
    return output_file

if __name__ == '__main__':
    build_executable()
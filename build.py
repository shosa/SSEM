import os
import shutil
import subprocess
import sys

def build_executable():
    print("Compilando SSEM con PyInstaller...")
    subprocess.check_call(['pyinstaller', 'ssem.spec'])
    
    print("Build completata!")
    
    # Crea la cartella di output se non esiste
    os.makedirs('output', exist_ok=True)
    
    # Archivia la build
    output_file = 'output/SSEM.zip'
    shutil.make_archive('output/SSEM', 'zip', 'dist/SSEM')
    
    print(f"Build archiviata in {output_file}")
    return output_file

if __name__ == '__main__':
    build_executable()
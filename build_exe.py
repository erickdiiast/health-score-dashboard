"""
Script de build para gerar executável do Health Score Dashboard
Versão 2.8.0 - Com aba Jornada do Jogador
"""

import PyInstaller.__main__
import os
import sys
import shutil

# Configurações
APP_NAME = "HealthScoreDashboard"
APP_VERSION = "2.8.0"
MAIN_SCRIPT = "app.py"
ICON_PATH = None  # Adicione um ícone .ico se desejar

def clean_build():
    """Limpa diretórios de build anteriores"""
    dirs_to_remove = ['build', 'dist', f'{APP_NAME}.spec']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removendo {dir_name}...")
            if os.path.isdir(dir_name):
                shutil.rmtree(dir_name)
            else:
                os.remove(dir_name)
    print("Limpeza concluída!")

def build_exe():
    """Gera o executável com PyInstaller"""
    print(f"=" * 60)
    print(f"  BUILD - Health Score Dashboard v{APP_VERSION}")
    print(f"=" * 60)
    print()
    
    # Argumentos do PyInstaller
    args = [
        MAIN_SCRIPT,
        '--name', APP_NAME,
        '--onefile',
        '--windowed',
        '--add-data', 'templates;templates',
        '--add-data', 'static;static',
        '--hidden-import', 'uvicorn',
        '--hidden-import', 'uvicorn.logging',
        '--hidden-import', 'uvicorn.loops',
        '--hidden-import', 'uvicorn.loops.auto',
        '--hidden-import', 'uvicorn.protocols',
        '--hidden-import', 'uvicorn.protocols.http',
        '--hidden-import', 'uvicorn.protocols.http.auto',
        '--hidden-import', 'uvicorn.protocols.websockets',
        '--hidden-import', 'uvicorn.protocols.websockets.auto',
        '--hidden-import', 'uvicorn.lifespan',
        '--hidden-import', 'uvicorn.lifespan.on',
        '--hidden-import', 'pandas',
        '--hidden-import', 'numpy',
        '--hidden-import', 'openpyxl',
        '--hidden-import', 'sqlite3',
    ]
    
    if ICON_PATH and os.path.exists(ICON_PATH):
        args.extend(['--icon', ICON_PATH])
    
    print("Iniciando build...")
    print(f"Comando: pyinstaller {' '.join(args)}")
    print()
    
    PyInstaller.__main__.run(args)
    
    print()
    print(f"=" * 60)
    print(f"  BUILD CONCLUÍDO!")
    print(f"=" * 60)
    print()
    print(f"Executável gerado em: dist/{APP_NAME}.exe")
    print()
    print(f"Para testar:")
    print(f"  .\\dist\\{APP_NAME}.exe")
    print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Build Health Score Dashboard')
    parser.add_argument('--clean', action='store_true', help='Limpa build anterior')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    else:
        # Verifica se pyinstaller está instalado
        try:
            import PyInstaller
        except ImportError:
            print("PyInstaller não encontrado. Instalando...")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
            print("PyInstaller instalado!")
        
        build_exe()
